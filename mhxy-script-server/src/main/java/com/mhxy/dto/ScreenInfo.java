package com.mhxy.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 屏幕信息
 */
@Data
@AllArgsConstructor
public class ScreenInfo {
    private int width;
    private int height;
    private String screenshotPath;
}
