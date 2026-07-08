package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 屏幕截图工具类
 */
@Slf4j
@Component
public class ScreenCaptureUtil {

    private final Robot robot;

    public ScreenCaptureUtil() {
        try {
            this.robot = new Robot();
            // 设置截图延迟
            this.robot.setAutoDelay(50);
        } catch (AWTException e) {
            throw new RuntimeException("初始化Robot失败: " + e.getMessage(), e);
        }
    }

    /**
     * 全屏截图
     */
    public BufferedImage captureFullScreen() {
        Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
        Rectangle screenRect = new Rectangle(screenSize);
        return robot.createScreenCapture(screenRect);
    }

    /**
     * 指定区域截图
     */
    public BufferedImage captureRegion(int x, int y, int width, int height) {
        Rectangle region = new Rectangle(x, y, width, height);
        return robot.createScreenCapture(region);
    }

    /**
     * 保存截图到文件
     */
    public String saveScreenshot(BufferedImage image, String filename) {
        try {
            Path screenshotPath = Paths.get("screenshots");
            if (!Files.exists(screenshotPath)) {
                Files.createDirectories(screenshotPath);
            }
            
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
            String fullFilename = filename + "_" + timestamp + ".png";
            File output = new File(screenshotPath.toFile(), fullFilename);
            
            ImageIO.write(image, "png", output);
            log.info("截图已保存: {}", output.getAbsolutePath());
            return output.getAbsolutePath();
        } catch (IOException e) {
            log.error("保存截图失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 截图并返回Base64编码
     */
    public String captureToBase64() {
        BufferedImage image = captureFullScreen();
        try {
            java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
            ImageIO.write(image, "png", baos);
            return java.util.Base64.getEncoder().encodeToString(baos.toByteArray());
        } catch (IOException e) {
            log.error("截图转Base64失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 获取屏幕尺寸
     */
    public Dimension getScreenSize() {
        return Toolkit.getDefaultToolkit().getScreenSize();
    }
}
