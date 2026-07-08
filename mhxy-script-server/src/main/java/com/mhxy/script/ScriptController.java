package com.mhxy.script;

import com.mhxy.dto.ApiResponse;
import com.mhxy.dto.PointInfo;
import com.mhxy.dto.ScreenInfo;
import com.mhxy.service.ConcurrentOcrService;
import com.mhxy.util.ImageMatchUtil;
import com.mhxy.util.RobotUtil;
import com.mhxy.util.ScreenCaptureUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import org.opencv.core.Point;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 图色脚本控制器 - 提供 RESTful API
 */
@Slf4j
@RestController
@RequestMapping("/api/script")
@RequiredArgsConstructor
public class ScriptController {

    private final ScreenCaptureUtil screenCapture;
    private final ImageMatchUtil imageMatch;
    private final RobotUtil robot;
    private final ConcurrentOcrService ocrService;

    // ==================== 截图相关 ====================

    /**
     * 全屏截图
     */
    @GetMapping("/screenshot/full")
    public ApiResponse<ScreenInfo> captureFullScreen() {
        BufferedImage image = screenCapture.captureFullScreen();
        String path = screenCapture.saveScreenshot(image, "full_screen");
        return ApiResponse.success(new ScreenInfo(
                screenCapture.getScreenSize().width,
                screenCapture.getScreenSize().height,
                path
        ));
    }

    /**
     * 区域截图
     */
    @GetMapping("/screenshot/region")
    public ApiResponse<String> captureRegion(
            @RequestParam int x,
            @RequestParam int y,
            @RequestParam int width,
            @RequestParam int height,
            @RequestParam(required = false) String filename) {
        BufferedImage image = screenCapture.captureRegion(x, y, width, height);
        String name = filename != null ? filename : "region";
        String path = screenCapture.saveScreenshot(image, name);
        return ApiResponse.success(path);
    }

    /**
     * 获取屏幕尺寸
     */
    @GetMapping("/screen/size")
    public ApiResponse<ScreenInfo> getScreenSize() {
        Dimension size = screenCapture.getScreenSize();
        return ApiResponse.success(new ScreenInfo(size.width, size.height, null));
    }

    // ==================== 图色匹配相关 ====================

    /**
     * 查找模板图片（全屏）
     */
    @GetMapping("/match/find")
    public ApiResponse<?> findTemplate(
            @RequestParam String templatePath,
            @RequestParam(required = false) Boolean findAll) {
        BufferedImage screen = screenCapture.captureFullScreen();

        if (Boolean.TRUE.equals(findAll)) {
            List<Point> points = imageMatch.findAllTemplates(screen, templatePath);
            List<PointInfo> infos = points.stream()
                    .map(p -> new PointInfo(p.x, p.y, 1.0))
                    .toList();
            return ApiResponse.success(infos);
        } else {
            Optional<Point> point = imageMatch.findTemplate(screen, templatePath);
            if (point.isPresent()) {
                return ApiResponse.success(new PointInfo(point.get().x, point.get().y, 1.0));
            }
            return ApiResponse.fail("未找到匹配图片");
        }
    }

    /**
     * 获取匹配相似度
     */
    @GetMapping("/match/similarity")
    public ApiResponse<Double> getSimilarity(@RequestParam String templatePath) {
        BufferedImage screen = screenCapture.captureFullScreen();
        double similarity = imageMatch.getMatchSimilarity(screen, templatePath);
        return ApiResponse.success(similarity);
    }

    /**
     * 区域模板匹配
     */
    @GetMapping("/match/findInRegion")
    public ApiResponse<PointInfo> findInRegion(
            @RequestParam String templatePath,
            @RequestParam int x,
            @RequestParam int y,
            @RequestParam int width,
            @RequestParam int height) {
        BufferedImage regionImage = screenCapture.captureRegion(x, y, width, height);
        Optional<Point> point = imageMatch.findTemplate(regionImage, templatePath);

        if (point.isPresent()) {
            // 转换为全屏坐标
            return ApiResponse.success(new PointInfo(
                    point.get().x + x,
                    point.get().y + y,
                    1.0
            ));
        }
        return ApiResponse.fail("未找到匹配图片");
    }

    // ==================== 鼠标操作相关 ====================

    /**
     * 移动鼠标
     */
    @PostMapping("/mouse/move")
    public ApiResponse<Void> moveMouse(@RequestParam int x, @RequestParam int y) {
        robot.moveTo(x, y);
        return ApiResponse.success(null);
    }

    /**
     * 点击鼠标（支持左键/右键）
     */
    @PostMapping("/mouse/click")
    public ApiResponse<Void> click(
            @RequestParam int x,
            @RequestParam int y,
            @RequestParam(defaultValue = "left") String button) {
        robot.moveTo(x, y);
        if ("right".equalsIgnoreCase(button)) {
            robot.rightClick();
        } else {
            robot.leftClick();
        }
        return ApiResponse.success(null);
    }

    /**
     * 双击
     */
    @PostMapping("/mouse/doubleClick")
    public ApiResponse<Void> doubleClick(@RequestParam int x, @RequestParam int y) {
        robot.moveTo(x, y);
        robot.doubleClick();
        return ApiResponse.success(null);
    }

    /**
     * 拖拽
     */
    @PostMapping("/mouse/drag")
    public ApiResponse<Void> drag(
            @RequestParam int startX,
            @RequestParam int startY,
            @RequestParam int endX,
            @RequestParam int endY) {
        robot.drag(startX, startY, endX, endY);
        return ApiResponse.success(null);
    }

    /**
     * 滚轮滚动
     */
    @PostMapping("/mouse/scroll")
    public ApiResponse<Void> scroll(@RequestParam int units) {
        robot.scroll(units);
        return ApiResponse.success(null);
    }

    // ==================== 键盘操作相关 ====================

    /**
     * 按键
     */
    @PostMapping("/keyboard/key")
    public ApiResponse<Void> pressKey(@RequestParam int keyCode) {
        robot.typeKey(keyCode);
        return ApiResponse.success(null);
    }

    /**
     * 输入文本
     */
    @PostMapping("/keyboard/type")
    public ApiResponse<Void> typeString(@RequestParam String text) {
        robot.typeString(text);
        return ApiResponse.success(null);
    }

    // ==================== 组合操作 ====================

    /**
     * 查找图片并点击
     */
    @GetMapping("/action/findAndClick")
    public ApiResponse<Void> findAndClick(@RequestParam String templatePath) {
        BufferedImage screen = screenCapture.captureFullScreen();
        Optional<Point> point = imageMatch.findTemplate(screen, templatePath);

        if (point.isPresent()) {
            robot.click((int) point.get().x, (int) point.get().y);
            return ApiResponse.success(null);
        }
        return ApiResponse.fail("未找到图片");
    }

    /**
     * 等待图片出现（最长等待 timeout 毫秒）
     * <p>注意：这是一个同步阻塞接口，会占用 Tomcat 线程，生产环境建议改为异步。</p>
     */
    @GetMapping("/action/waitFor")
    public ApiResponse<PointInfo> waitFor(
            @RequestParam String templatePath,
            @RequestParam(defaultValue = "30000") long timeout) {
        long startTime = System.currentTimeMillis();
        while (System.currentTimeMillis() - startTime < timeout) {
            try {
                BufferedImage screen = screenCapture.captureFullScreen();
                Optional<Point> point = imageMatch.findTemplate(screen, templatePath);
                if (point.isPresent()) {
                    return ApiResponse.success(new PointInfo(point.get().x, point.get().y, 1.0));
                }
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                log.warn("等待图片异常: {}", e.getMessage());
            }
        }
        return ApiResponse.fail("等待超时，图片未出现");
    }

    // ==================== OCR 数字/文字识别 ====================

    /**
     * 单区域数字识别（ROI截图 + 预处理 + OCR）
     */
    @GetMapping("/ocr/digits")
    public ApiResponse<String> ocrDigits(
            @RequestParam int x,
            @RequestParam int y,
            @RequestParam int width,
            @RequestParam int height) {
        String result = ocrService.recognizeSingleRegion(x, y, width, height);
        return ApiResponse.success(result);
    }

    /**
     * 多区域并发数字识别（使用预设区域）
     */
    @GetMapping("/ocr/defaults")
    public ApiResponse<Map<String, String>> ocrDefaultRegions() {
        Map<String, String> results = ocrService.recognizeDefaultRegions();
        return ApiResponse.success(results);
    }

    /**
     * 自定义多区域并发数字识别
     * <p>请求体格式：</p>
     * <pre>
     * [
     *   {"name": "血量", "x": 100, "y": 50, "width": 60, "height": 20},
     *   {"name": "蓝量", "x": 100, "y": 75, "width": 60, "height": 20}
     * ]
     * </pre>
     */
    @PostMapping("/ocr/multi")
    public ApiResponse<Map<String, String>> ocrMultiRegions(
            @RequestBody List<ConcurrentOcrService.GameRegion> regions) {
        Map<String, String> results = ocrService.recognizeMultipleRegions(regions);
        return ApiResponse.success(results);
    }
}
