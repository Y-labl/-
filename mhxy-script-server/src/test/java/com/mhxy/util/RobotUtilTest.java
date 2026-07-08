package com.mhxy.util;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.awt.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 工具类测试
 */
@SpringBootTest
class RobotUtilTest {

    @Autowired
    private ScreenCaptureUtil screenCapture;

    @Autowired
    private RobotUtil robotUtil;

    @Test
    void testScreenCapture() {
        BufferedImage image = screenCapture.captureFullScreen();
        assertNotNull(image);
        assertTrue(image.getWidth() > 0);
        assertTrue(image.getHeight() > 0);
        System.out.println("屏幕尺寸: " + image.getWidth() + "x" + image.getHeight());
    }

    @Test
    void testRegionCapture() {
        BufferedImage image = screenCapture.captureRegion(0, 0, 100, 100);
        assertNotNull(image);
        assertEquals(100, image.getWidth());
        assertEquals(100, image.getHeight());
    }

    @Test
    void testScreenSize() {
        Dimension size = screenCapture.getScreenSize();
        assertTrue(size.width > 0);
        assertTrue(size.height > 0);
        System.out.println("屏幕尺寸: " + size.width + "x" + size.height);
    }

    @Test
    void testMouseMove() {
        // 移动鼠标到屏幕中心
        Dimension size = screenCapture.getScreenSize();
        robotUtil.moveTo(size.width / 2, size.height / 2);
        System.out.println("鼠标移动测试完成");
    }
}
