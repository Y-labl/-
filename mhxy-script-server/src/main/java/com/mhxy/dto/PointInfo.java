package com.mhxy.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 图片匹配坐标信息
 */
@Data
@AllArgsConstructor
public class PointInfo {
    private double x;
    private double y;
    private double similarity;
}
