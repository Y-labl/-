package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.TemplateImage;
import com.mhxy.mapper.TemplateImageMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.mhxy.entity.Device;
import com.mhxy.service.DeviceScannerService;
import com.mhxy.service.DeviceService;
import com.mhxy.util.ImageMatchUtil;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/template")
public class TemplateController {

    @Autowired
    private TemplateImageMapper templateImageMapper;

    @Autowired
    private ImageMatchUtil imageMatchUtil;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private DeviceScannerService scannerService;

    @Value("${script.template-path:${user.dir}/templates}")
    private String templatePath;

    @GetMapping("/list")
    public ApiResponse<List<Map<String, Object>>> list(
            @RequestParam(required = false) String category) {
        List<TemplateImage> list;
        if (category != null && !category.isEmpty()) {
            list = templateImageMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TemplateImage>()
                    .eq(TemplateImage::getCategory, category));
        } else {
            list = templateImageMapper.selectList(null);
        }
        List<Map<String, Object>> result = new ArrayList<>();
        for (TemplateImage t : list) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", t.getId());
            m.put("templateName", t.getTemplateName());
            m.put("category", t.getCategory());
            m.put("matchThreshold", t.getMatchThreshold());
            m.put("description", t.getDescription());
            m.put("usageCount", t.getUsageCount());
            m.put("thumbnail", "/api/template/image/" + t.getId());
            m.put("width", t.getWidth());
            m.put("height", t.getHeight());
            m.put("fileSize", t.getFileSize());
            result.add(m);
        }
        return ApiResponse.success(result);
    }

    @GetMapping("/image/{id}")
    public byte[] getImage(@PathVariable Long id) {
        TemplateImage t = templateImageMapper.selectById(id);
        if (t == null || t.getTemplatePath() == null) return new byte[0];
        try {
            return Files.readAllBytes(Paths.get(t.getTemplatePath()));
        } catch (IOException e) {
            return new byte[0];
        }
    }

    @PostMapping("/upload")
    public ApiResponse<Map<String, Object>> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam("templateName") String templateName,
            @RequestParam(value = "category", defaultValue = "monster") String category,
            @RequestParam(value = "matchThreshold", defaultValue = "0.85") Double threshold,
            @RequestParam(value = "description", required = false) String description) {
        try {
            Path dir = Paths.get(templatePath);
            if (!Files.exists(dir)) Files.createDirectories(dir);

            String fileName = System.currentTimeMillis() + "_" + file.getOriginalFilename();
            Path dest = dir.resolve(fileName);
            file.transferTo(dest.toFile());

            BufferedImage img = ImageIO.read(dest.toFile());

            TemplateImage template = new TemplateImage();
            template.setTemplateName(templateName);
            template.setCategory(category);
            template.setTemplatePath(dest.toString());
            template.setFileSize((int) file.getSize());
            template.setWidth(img != null ? img.getWidth() : 0);
            template.setHeight(img != null ? img.getHeight() : 0);
            template.setMatchThreshold(threshold);
            template.setDescription(description);
            template.setUsageCount(0);
            template.setSuccessCount(0);
            template.setStatus(1);

            templateImageMapper.insert(template);
            log.info("Template uploaded: {} ({})", templateName, fileName);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", template.getId());
            result.put("templateName", templateName);
            return ApiResponse.success("Uploaded", result);
        } catch (Exception e) {
            log.error("Upload failed: {}", e.getMessage());
            return ApiResponse.fail(e.getMessage());
        }
    }


    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        TemplateImage t = templateImageMapper.selectById(id);
        if (t == null) return ApiResponse.fail("Template not found");
        if (body.containsKey("templateName")) t.setTemplateName((String) body.get("templateName"));
        if (body.containsKey("category")) t.setCategory((String) body.get("category"));
        if (body.containsKey("description")) t.setDescription((String) body.get("description"));
        if (body.containsKey("matchThreshold")) t.setMatchThreshold(((Number) body.get("matchThreshold")).doubleValue());
        templateImageMapper.updateById(t);
        return ApiResponse.success("Updated", null);
    }

    /** 测试：用上传的图片进行模板匹配 */
    @PostMapping("/{id}/match")
    public ApiResponse<Map<String, Object>> matchTemplate(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile file) {
        TemplateImage template = templateImageMapper.selectById(id);
        if (template == null || template.getTemplatePath() == null) {
            return ApiResponse.fail("模板不存在");
        }
        try {
            BufferedImage targetImage = ImageIO.read(new ByteArrayInputStream(file.getBytes()));
            if (targetImage == null) return ApiResponse.fail("无法读取目标图片");

            double similarity = imageMatchUtil.getMatchSimilarity(targetImage, template.getTemplatePath());
            java.util.List<org.opencv.core.Point> matches = imageMatchUtil.findAllTemplates(targetImage, template.getTemplatePath());

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("templateId", id);
            result.put("templateName", template.getTemplateName());
            result.put("templateWidth", template.getWidth());
            result.put("templateHeight", template.getHeight());
            result.put("imageWidth", targetImage.getWidth());
            result.put("imageHeight", targetImage.getHeight());
            result.put("similarity", Math.round(similarity * 10000) / 10000.0);
            result.put("matched", !matches.isEmpty());
            if (!matches.isEmpty()) {
                List<Map<String, Object>> points = new ArrayList<>();
                for (org.opencv.core.Point p : matches) {
                    Map<String, Object> pt = new LinkedHashMap<>();
                    pt.put("x", (int) p.x);
                    pt.put("y", (int) p.y);
                    points.add(pt);
                }
                result.put("matchPoints", points);
            }
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("Match failed: {}", e.getMessage());
            return ApiResponse.fail(e.getMessage());
        }
    }

    /** 测试：通过设备截图进行模板匹配 */
    @PostMapping("/{id}/match-device")
    public ApiResponse<Map<String, Object>> matchDevice(
            @PathVariable Long id,
            @RequestParam("deviceId") Long deviceId) {
        TemplateImage template = templateImageMapper.selectById(id);
        if (template == null || template.getTemplatePath() == null) {
            return ApiResponse.fail("模板不存在");
        }
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) {
            return ApiResponse.fail("设备不存在或未绑定");
        }
        try {
            byte[] pngBytes = scannerService.captureAdbScreenshot(device.getDeviceId());
            if (pngBytes == null || pngBytes.length == 0) {
                return ApiResponse.fail("设备截图失败");
            }
            BufferedImage screenImage = ImageIO.read(new ByteArrayInputStream(pngBytes));
            if (screenImage == null) return ApiResponse.fail("无法读取设备截图");

            double similarity = imageMatchUtil.getMatchSimilarity(screenImage, template.getTemplatePath());
            java.util.List<org.opencv.core.Point> matches = imageMatchUtil.findAllTemplates(screenImage, template.getTemplatePath());

            String base64 = Base64.getEncoder().encodeToString(pngBytes);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("templateId", id);
            result.put("templateName", template.getTemplateName());
            result.put("templateWidth", template.getWidth());
            result.put("templateHeight", template.getHeight());
            result.put("imageWidth", screenImage.getWidth());
            result.put("imageHeight", screenImage.getHeight());
            result.put("similarity", Math.round(similarity * 10000) / 10000.0);
            result.put("matched", !matches.isEmpty());
            result.put("deviceName", device.getDeviceName());
            result.put("screenshotBase64", "data:image/png;base64," + base64);
            if (!matches.isEmpty()) {
                List<Map<String, Object>> points = new ArrayList<>();
                for (org.opencv.core.Point p : matches) {
                    Map<String, Object> pt = new LinkedHashMap<>();
                    pt.put("x", (int) p.x);
                    pt.put("y", (int) p.y);
                    points.add(pt);
                }
                result.put("matchPoints", points);
            }
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("Device match failed: {}", e.getMessage());
            return ApiResponse.fail(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        TemplateImage t = templateImageMapper.selectById(id);
        if (t != null && t.getTemplatePath() != null) {
            try { Files.deleteIfExists(Paths.get(t.getTemplatePath())); } catch (Exception ignored) {}
        }
        templateImageMapper.deleteById(id);
        return ApiResponse.success("Deleted", null);
    }
}