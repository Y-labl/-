package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import org.opencv.core.*;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Optional;

/**
 * 图像匹配工具类 - 使用OpenCV进行模板匹配
 */
@Slf4j
@Component
public class ImageMatchUtil {

    static {
        // 加载OpenCV原生库
        nu.pattern.OpenCV.loadShared();
    }

    /** 单次 findAllTemplates 最多返回的匹配数，防止极端情况下死循环 */
    private static final int MAX_MATCHES = 50;

    @Value("${script.match-threshold:0.85}")
    private double matchThreshold;

    /**
     * 在屏幕截图中查找模板图片的位置
     * @param screenImage 屏幕截图
     * @param templatePath 模板图片路径
     * @return 匹配到的中心点坐标，如果没有找到返回Optional.empty()
     */
    public Optional<Point> findTemplate(BufferedImage screenImage, String templatePath) {
        File templateFile = new File(templatePath);
        if (!templateFile.exists()) {
            log.warn("模板文件不存在: {}", templatePath);
            return Optional.empty();
        }

        // 将BufferedImage转换为Mat
        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = Imgcodecs.imread(templatePath);

        if (templateMat.empty()) {
            log.warn("无法读取模板图片: {}", templatePath);
            return Optional.empty();
        }

        // 执行模板匹配
        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);

        // 找到最佳匹配位置
        double minVal = 0, maxVal = 0;
        Point maxLoc = new Point();
        Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(result);
        
        // 对于TM_CCOEFF_NORMED，最大值位置是最佳匹配
        maxVal = minMaxResult.maxVal;
        maxLoc = minMaxResult.maxLoc;

        log.debug("模板匹配结果: 相似度={}, 阈值={}", String.format("%.2f", maxVal), matchThreshold);

        // 释放内存
        screenMat.release();
        templateMat.release();
        result.release();

        // 判断是否达到阈值
        if (maxVal >= matchThreshold) {
            // 计算中心点
            Point center = new Point(
                maxLoc.x + templateMat.cols() / 2.0,
                maxLoc.y + templateMat.rows() / 2.0
            );
            return Optional.of(center);
        }

        return Optional.empty();
    }

    /**
     * 在截图中查找所有匹配位置
     */
    public java.util.List<Point> findAllTemplates(BufferedImage screenImage, String templatePath) {
        java.util.List<Point> matches = new java.util.ArrayList<>();
        
        File templateFile = new File(templatePath);
        if (!templateFile.exists()) {
            log.warn("模板文件不存在: {}", templatePath);
            return matches;
        }

        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = Imgcodecs.imread(templatePath);

        if (templateMat.empty()) {
            return matches;
        }

        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);

        // 查找所有超过阈值的匹配
        double threshold = matchThreshold;
        int matchCount = 0;
        while (matchCount < MAX_MATCHES) {
            Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(result);
            if (minMaxResult.maxVal >= threshold) {
                matches.add(new Point(
                    minMaxResult.maxLoc.x + templateMat.cols() / 2.0,
                    minMaxResult.maxLoc.y + templateMat.rows() / 2.0
                ));

                // 将已匹配区域置零，避免重复匹配
                Imgproc.rectangle(result,
                    minMaxResult.maxLoc,
                    new Point(minMaxResult.maxLoc.x + templateMat.cols(),
                              minMaxResult.maxLoc.y + templateMat.rows()),
                    new Scalar(0), -1);
                matchCount++;
            } else {
                break;
            }
        }
        if (matchCount >= MAX_MATCHES) {
            log.warn("findAllTemplates 达到最大匹配数限制({})，可能遗漏部分匹配", MAX_MATCHES);
        }

        screenMat.release();
        templateMat.release();
        result.release();

        return matches;
    }

    /**
     * 获取匹配的相似度
     */
    public double getMatchSimilarity(BufferedImage screenImage, String templatePath) {
        File templateFile = new File(templatePath);
        if (!templateFile.exists()) {
            return 0;
        }

        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = Imgcodecs.imread(templatePath);

        if (templateMat.empty()) {
            return 0;
        }

        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);
        
        Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(result);
        double maxVal = minMaxResult.maxVal;

        screenMat.release();
        templateMat.release();
        result.release();

        return maxVal;
    }

    /**
     * BufferedImage 转换为 OpenCV Mat
     */
    private Mat bufferedImageToMat(BufferedImage image) {
        try (java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream()) {
            javax.imageio.ImageIO.write(image, "png", baos);
            byte[] bytes = baos.toByteArray();
            return Imgcodecs.imdecode(new Mat(1, bytes.length, CvType.CV_8UC1),
                Imgcodecs.IMREAD_COLOR);
        } catch (Exception e) {
            throw new RuntimeException("图片转换失败: " + e.getMessage(), e);
        }
    }
}
