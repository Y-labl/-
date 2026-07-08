package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.awt.*;
import java.awt.event.InputEvent;
import java.awt.event.KeyEvent;

/**
 * 鼠标键盘操作工具类
 */
@Slf4j
@Component
public class RobotUtil {

    private final Robot robot;
    
    @Value("${script.click-interval:300}")
    private long clickInterval;

    public RobotUtil() {
        try {
            this.robot = new Robot();
            this.robot.setAutoDelay(50);
        } catch (AWTException e) {
            throw new RuntimeException("初始化Robot失败: " + e.getMessage(), e);
        }
    }

    /**
     * 鼠标移动到指定位置
     */
    public void moveTo(int x, int y) {
        robot.mouseMove(x, y);
        log.debug("鼠标移动到: ({}, {})", x, y);
    }

    /**
     * 左键点击
     */
    public void leftClick() {
        robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
        robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
        sleep(clickInterval);
        log.debug("左键点击");
    }

    /**
     * 右键点击
     */
    public void rightClick() {
        robot.mousePress(InputEvent.BUTTON3_DOWN_MASK);
        robot.mouseRelease(InputEvent.BUTTON3_DOWN_MASK);
        sleep(clickInterval);
        log.debug("右键点击");
    }

    /**
     * 在指定位置左键点击
     */
    public void click(int x, int y) {
        moveTo(x, y);
        leftClick();
    }

    /**
     * 双击
     */
    public void doubleClick() {
        robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
        robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
        robot.delay(50);
        robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
        robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
        sleep(clickInterval);
        log.debug("双击");
    }

    /**
     * 拖拽
     */
    public void drag(int startX, int startY, int endX, int endY) {
        moveTo(startX, startY);
        robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
        sleep(100);
        // 分段移动，使拖拽更平滑
        int steps = 10;
        for (int i = 1; i <= steps; i++) {
            int currentX = startX + (endX - startX) * i / steps;
            int currentY = startY + (endY - startY) * i / steps;
            robot.mouseMove(currentX, currentY);
            sleep(20);
        }
        robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
        sleep(clickInterval);
        log.debug("拖拽: ({}, {}) -> ({}, {})", startX, startY, endX, endY);
    }

    /**
     * 按下指定键
     */
    public void keyPress(int keyCode) {
        robot.keyPress(keyCode);
        log.debug("按键: {}", KeyEvent.getKeyText(keyCode));
    }

    /**
     * 释放指定键
     */
    public void keyRelease(int keyCode) {
        robot.keyRelease(keyCode);
    }

    /**
     * 按下并释放指定键
     */
    public void typeKey(int keyCode) {
        robot.keyPress(keyCode);
        robot.keyRelease(keyCode);
        sleep(clickInterval);
    }

    /**
     * 输入字符串
     */
    public void typeString(String text) {
        for (char c : text.toCharArray()) {
            typeChar(c);
        }
        log.debug("输入文本: {}", text);
    }

    /**
     * 输入单个字符
     */
    private void typeChar(char c) {
        int keyCode = KeyEvent.getExtendedKeyCodeForChar(c);
        if (keyCode != KeyEvent.VK_UNDEFINED) {
            robot.keyPress(keyCode);
            robot.keyRelease(keyCode);
        }
        sleep(50);
    }

    /**
     * 滚轮滚动
     */
    public void scroll(int units) {
        robot.mouseWheel(units);
        log.debug("滚轮滚动: {} 单位", units);
    }

    /**
     * 组合键按下
     */
    public void comboKeyPress(int... keyCodes) {
        for (int keyCode : keyCodes) {
            robot.keyPress(keyCode);
        }
    }

    /**
     * 组合键释放
     */
    public void comboKeyRelease(int... keyCodes) {
        for (int keyCode : keyCodes) {
            robot.keyRelease(keyCode);
        }
    }

    /**
     * 常用组合键 - Ctrl+C
     */
    public void copy() {
        comboKeyPress(KeyEvent.VK_CONTROL, KeyEvent.VK_C);
        comboKeyRelease(KeyEvent.VK_CONTROL, KeyEvent.VK_C);
        sleep(clickInterval);
    }

    /**
     * 常用组合键 - Ctrl+V
     */
    public void paste() {
        comboKeyPress(KeyEvent.VK_CONTROL, KeyEvent.VK_V);
        comboKeyRelease(KeyEvent.VK_CONTROL, KeyEvent.VK_V);
        sleep(clickInterval);
    }

    /**
     * 常用组合键 - Ctrl+A
     */
    public void selectAll() {
        comboKeyPress(KeyEvent.VK_CONTROL, KeyEvent.VK_A);
        comboKeyRelease(KeyEvent.VK_CONTROL, KeyEvent.VK_A);
        sleep(clickInterval);
    }

    /**
     * 休眠
     */
    private void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
