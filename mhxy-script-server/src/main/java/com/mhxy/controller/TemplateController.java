package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.TemplateImage;
import com.mhxy.mapper.TemplateImageMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.opencv.core.Mat;
import org.opencv.imgcodecs.Imgcodecs;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.mhxy.entity.Device;
import com.mhxy.service.DeviceScannerService;
import com.mhxy.service.DeviceService;
import com.mhxy.util.ImageMatchUtil;
import com.mhxy.util.OcrUtil;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
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

    @Autowired
    private OcrUtil ocrUtil;

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
            @RequestParam(value = "matchThreshold", defaultValue = "0.75") Double threshold,
            @RequestParam(value = "description", required = false) String description) {
        try {
            Path dir = Paths.get(templatePath);
            if (!Files.exists(dir)) Files.createDirectories(dir);

            String fileName = System.currentTimeMillis() + "_" + file.getOriginalFilename();
            Path dest = dir.resolve(fileName);
            file.transferTo(dest.toFile());

            // 优先用ImageIO读尺寸，失败则使用OpenCV兜底
            int width = 0, height = 0;
            BufferedImage img = ImageIO.read(dest.toFile());
            if (img != null) {
                width = img.getWidth();
                height = img.getHeight();
            } else {
                Mat mat = Imgcodecs.imread(dest.toString(), Imgcodecs.IMREAD_COLOR);
                if (!mat.empty()) {
                    width = mat.cols();
                    height = mat.rows();
                    mat.release();
                }
            }

            TemplateImage template = new TemplateImage();
            template.setTemplateName(templateName);
            template.setCategory(category);
            template.setTemplatePath(dest.toString());
            template.setFileSize((int) file.getSize());
            template.setWidth(width);
            template.setHeight(height);
            template.setMatchThreshold(threshold);
            template.setDescription(description);
            template.setUsageCount(0);
            template.setSuccessCount(0);
            template.setStatus(1);

            templateImageMapper.insert(template);
            log.info("Template uploaded: {} ({}), size={}x{}", templateName, fileName, width, height);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", template.getId());
            result.put("templateName", templateName);
            result.put("width", width);
            result.put("height", height);
            return ApiResponse.success("Uploaded", result);
        } catch (Exception e) {
            log.error("Upload failed: {}", e.getMessage(), e);
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



    /** 文字识别：对设备截图进行OCR（可选模板裁剪区域识别） */
    @PostMapping("/ocr-device")
    public ApiResponse<Map<String, Object>> ocrDevice(
            @RequestParam("deviceId") Long deviceId,
            @RequestParam(value = "templateId", required = false) Long templateId) {
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) {
            return ApiResponse.fail("设备不存在或未绑定");
        }
        try {
            byte[] pngBytes = scannerService.captureAdbScreenshot(device.getDeviceId());
            if (pngBytes == null || pngBytes.length == 0) return ApiResponse.fail("设备截图失败");

            BufferedImage image = ImageIO.read(new ByteArrayInputStream(pngBytes));
            if (image == null) return ApiResponse.fail("无法读取设备截图");

            String base64 = Base64.getEncoder().encodeToString(pngBytes);
            BufferedImage targetRegion = image;
            Map<String, Object> matchInfo = null;

            if (templateId != null) {
                TemplateImage template = templateImageMapper.selectById(templateId);
                if (template != null && template.getTemplatePath() != null) {
                    Mat screenMat = imageMatchUtil.decodeImageMat(pngBytes);
                    Mat templateMat = imageMatchUtil.readImageMat(template.getTemplatePath());
                    if (!screenMat.empty() && !templateMat.empty()) {
                        double threshold = template.getMatchThreshold() != null ? template.getMatchThreshold() : 0.75;
                        java.util.Optional<org.opencv.core.Point> match = imageMatchUtil.findTemplate(screenMat, templateMat, threshold);
                        if (match.isPresent()) {
                            org.opencv.core.Point p = match.get();
                            int tx = templateMat.cols();
                            int ty = templateMat.rows();
                            int cx = Math.max(0, (int)(p.x - tx / 2.0));
                            int cy = Math.max(0, (int)(p.y - ty / 2.0));
                            int cw = Math.min(tx, image.getWidth() - cx);
                            int ch = Math.min(ty, image.getHeight() - cy);
                            if (cw > 0 && ch > 0) {
                                targetRegion = image.getSubimage(cx, cy, cw, ch);
                                matchInfo = new LinkedHashMap<>();
                                matchInfo.put("x", cx);
                                matchInfo.put("y", cy);
                                matchInfo.put("width", cw);
                                matchInfo.put("height", ch);
                            }
                        }
                        screenMat.release();
                        templateMat.release();
                    }
                }
            }

            long t0 = System.currentTimeMillis();
            String text = ocrUtil.recognize(targetRegion);
            long elapsed = System.currentTimeMillis() - t0;

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("text", text);
            result.put("elapsedMs", elapsed);
            result.put("deviceName", device.getDeviceName());
            result.put("imageWidth", image.getWidth());
            result.put("imageHeight", image.getHeight());
            result.put("screenshotBase64", "data:image/png;base64," + base64);
            if (matchInfo != null) {
                result.put("cropRegion", matchInfo);
            }
            if (templateId != null && matchInfo == null) {
                result.put("matchFailed", true);
            }
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("Device OCR failed: {}", e.getMessage(), e);
            return ApiResponse.fail(e.getMessage());
        }
    }

        /** 文字识别：对上传图片进行OCR（可选模板裁剪区域识别） */
    @PostMapping("/ocr")
    public ApiResponse<Map<String, Object>> ocrImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "templateId", required = false) Long templateId) {
        try {
            BufferedImage image = ImageIO.read(new ByteArrayInputStream(file.getBytes()));
            if (image == null) return ApiResponse.fail("无法读取图片");

            BufferedImage targetRegion = image;
            Map<String, Object> matchInfo = null;

            if (templateId != null) {
                TemplateImage template = templateImageMapper.selectById(templateId);
                if (template != null && template.getTemplatePath() != null) {
                    Mat targetMat = imageMatchUtil.decodeImageMat(file.getBytes());
                    Mat templateMat = imageMatchUtil.readImageMat(template.getTemplatePath());
                    if (!targetMat.empty() && !templateMat.empty()) {
                        double threshold = template.getMatchThreshold() != null ? template.getMatchThreshold() : 0.75;
                        java.util.Optional<org.opencv.core.Point> match = imageMatchUtil.findTemplate(targetMat, templateMat, threshold);
                        if (match.isPresent()) {
                            org.opencv.core.Point p = match.get();
                            int tx = templateMat.cols();
                            int ty = templateMat.rows();
                            int cx = Math.max(0, (int)(p.x - tx / 2.0));
                            int cy = Math.max(0, (int)(p.y - ty / 2.0));
                            int cw = Math.min(tx, image.getWidth() - cx);
                            int ch = Math.min(ty, image.getHeight() - cy);
                            if (cw > 0 && ch > 0) {
                                targetRegion = image.getSubimage(cx, cy, cw, ch);
                                matchInfo = new LinkedHashMap<>();
                                matchInfo.put("x", cx);
                                matchInfo.put("y", cy);
                                matchInfo.put("width", cw);
                                matchInfo.put("height", ch);
                            }
                        }
                        targetMat.release();
                        templateMat.release();
                    }
                }
            }

            long t0 = System.currentTimeMillis();
            String text = ocrUtil.recognize(targetRegion);
            long elapsed = System.currentTimeMillis() - t0;

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("text", text);
            result.put("elapsedMs", elapsed);
            result.put("imageWidth", image.getWidth());
            result.put("imageHeight", image.getHeight());
            if (matchInfo != null) {
                result.put("cropRegion", matchInfo);
            }
            if (templateId != null && matchInfo == null) {
                result.put("matchFailed", true);
            }
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("OCR failed: {}", e.getMessage(), e);
            return ApiResponse.fail(e.getMessage());
        }
    }

        /** 测试：用上传的图片进行模板匹配 */
    @PostMapping("/{id}/match")
    public ApiResponse<Map<String, Object>> matchTemplate(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "threshold", required = false) Double overrideThreshold) {
        TemplateImage template = templateImageMapper.selectById(id);
        if (template == null || template.getTemplatePath() == null) {
            return ApiResponse.fail("模板不存在");
        }
        try {
            // 统一使用OpenCV读取，避免ImageIO与OpenCV通道不一致
            Mat targetMat = imageMatchUtil.decodeImageMat(file.getBytes());
            Mat templateMat = imageMatchUtil.readImageMat(template.getTemplatePath());

            if (targetMat.empty()) return ApiResponse.fail("无法读取目标图片");
            if (templateMat.empty()) return ApiResponse.fail("无法读取模板图片");

            double threshold = overrideThreshold != null ? overrideThreshold
                : (template.getMatchThreshold() != null ? template.getMatchThreshold() : 0.75);
            double similarity = imageMatchUtil.getMatchSimilarity(targetMat, templateMat);
            java.util.List<org.opencv.core.Point> matches = imageMatchUtil.findAllTemplates(targetMat, templateMat, threshold);

            log.info("模板匹配测试 id={}: target={}x{}, template={}x{}, similarity={}, matched={}, threshold={}",
                    id, targetMat.cols(), targetMat.rows(), templateMat.cols(), templateMat.rows(),
                    String.format("%.4f", similarity), !matches.isEmpty(), threshold);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("templateId", id);
            result.put("templateName", template.getTemplateName());
            result.put("templateWidth", template.getWidth() != null && template.getWidth() > 0 ? template.getWidth() : templateMat.cols());
            result.put("templateHeight", template.getHeight() != null && template.getHeight() > 0 ? template.getHeight() : templateMat.rows());
            result.put("imageWidth", targetMat.cols());
            result.put("imageHeight", targetMat.rows());
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

            targetMat.release();
            templateMat.release();
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("Match failed: {}", e.getMessage(), e);
            return ApiResponse.fail(e.getMessage());
        }
    }

    /** 测试：通过设备截图进行模板匹配 */
    @PostMapping("/{id}/match-device")
    public ApiResponse<Map<String, Object>> matchDevice(
            @PathVariable Long id,
            @RequestParam("deviceId") Long deviceId,
            @RequestParam(value = "threshold", required = false) Double overrideThreshold) {
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
            Mat screenMat = imageMatchUtil.decodeImageMat(pngBytes);
            Mat templateMat = imageMatchUtil.readImageMat(template.getTemplatePath());
            if (screenMat.empty()) return ApiResponse.fail("无法读取设备截图");
            if (templateMat.empty()) return ApiResponse.fail("无法读取模板图片");

            double threshold = overrideThreshold != null ? overrideThreshold
                : (template.getMatchThreshold() != null ? template.getMatchThreshold() : 0.75);
            double similarity = imageMatchUtil.getMatchSimilarity(screenMat, templateMat);
            java.util.List<org.opencv.core.Point> matches = imageMatchUtil.findAllTemplates(screenMat, templateMat, threshold);

            String base64 = Base64.getEncoder().encodeToString(pngBytes);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("templateId", id);
            result.put("templateName", template.getTemplateName());
            result.put("templateWidth", template.getWidth() != null && template.getWidth() > 0 ? template.getWidth() : templateMat.cols());
            result.put("templateHeight", template.getHeight() != null && template.getHeight() > 0 ? template.getHeight() : templateMat.rows());
            result.put("imageWidth", screenMat.cols());
            result.put("imageHeight", screenMat.rows());
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

            screenMat.release();
            templateMat.release();
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("Device match failed: {}", e.getMessage(), e);
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