package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import org.opencv.core.*;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
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

    @Value("${script.match-threshold:0.75}")
    private double matchThreshold = 0.75;

    /**
     * 在屏幕截图中查找模板图片的位置
     * @param screenImage 屏幕截图
     * @param templatePath 模板图片路径
     * @return 匹配到的中心点坐标，如果没有找到返回Optional.empty()
     */
    public Optional<Point> findTemplate(BufferedImage screenImage, String templatePath) {
        return findTemplate(screenImage, templatePath, matchThreshold);
    }

    public Optional<Point> findTemplate(BufferedImage screenImage, String templatePath, double threshold) {
        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = readImageMat(templatePath);
        Optional<Point> result = findTemplate(screenMat, templateMat, threshold);
        screenMat.release();
        templateMat.release();
        return result;
    }

    public Optional<Point> findTemplate(Mat screenMat, Mat templateMat, double threshold) {
        if (screenMat.empty() || templateMat.empty()) {
            return Optional.empty();
        }
        if (screenMat.cols() < templateMat.cols() || screenMat.rows() < templateMat.rows()) {
            log.warn("模板尺寸({}x{})大于目标图({}x{})，无法进行模板匹配",
                    templateMat.cols(), templateMat.rows(), screenMat.cols(), screenMat.rows());
            return Optional.empty();
        }

        // 执行模板匹配
        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);

        Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(result);
        double maxVal = minMaxResult.maxVal;
        Point maxLoc = minMaxResult.maxLoc;
        result.release();

        log.debug("模板匹配结果: 相似度={}, 阈值={}", String.format("%.4f", maxVal), threshold);

        if (maxVal >= threshold) {
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
    public List<Point> findAllTemplates(BufferedImage screenImage, String templatePath) {
        return findAllTemplates(screenImage, templatePath, matchThreshold);
    }

    public List<Point> findAllTemplates(BufferedImage screenImage, String templatePath, double threshold) {
        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = readImageMat(templatePath);
        List<Point> matches = findAllTemplates(screenMat, templateMat, threshold);
        screenMat.release();
        templateMat.release();
        return matches;
    }

    public List<Point> findAllTemplates(Mat screenMat, Mat templateMat, double threshold) {
        List<Point> matches = new ArrayList<>();
        if (screenMat.empty() || templateMat.empty()) {
            return matches;
        }
        if (screenMat.cols() < templateMat.cols() || screenMat.rows() < templateMat.rows()) {
            log.warn("模板尺寸({}x{})大于目标图({}x{})，无法进行模板匹配",
                    templateMat.cols(), templateMat.rows(), screenMat.cols(), screenMat.rows());
            return matches;
        }

        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);

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

        result.release();
        return matches;
    }

    /**
     * 获取匹配的相似度
     */
    public double getMatchSimilarity(BufferedImage screenImage, String templatePath) {
        Mat screenMat = bufferedImageToMat(screenImage);
        Mat templateMat = readImageMat(templatePath);
        double similarity = getMatchSimilarity(screenMat, templateMat);
        screenMat.release();
        templateMat.release();
        return similarity;
    }

    public double getMatchSimilarity(Mat screenMat, Mat templateMat) {
        if (screenMat.empty() || templateMat.empty()) {
            return 0;
        }
        if (screenMat.cols() < templateMat.cols() || screenMat.rows() < templateMat.rows()) {
            log.warn("模板尺寸({}x{})大于目标图({}x{})，无法进行模板匹配",
                    templateMat.cols(), templateMat.rows(), screenMat.cols(), screenMat.rows());
            return 0;
        }

        Mat result = new Mat();
        Imgproc.matchTemplate(screenMat, templateMat, result, Imgproc.TM_CCOEFF_NORMED);
        Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(result);
        double maxVal = minMaxResult.maxVal;
        result.release();
        return maxVal;
    }

    /**
     * 使用OpenCV读取图片文件为Mat
     */
    public Mat readImageMat(String filePath) {
        File file = new File(filePath);
        if (!file.exists()) {
            log.warn("图片文件不存在: {}", filePath);
            return new Mat();
        }
        try {
            byte[] bytes = java.nio.file.Files.readAllBytes(file.toPath());
            Mat mat = Imgcodecs.imdecode(new MatOfByte(bytes), Imgcodecs.IMREAD_GRAYSCALE);
            if (mat.empty()) {
                log.warn("OpenCV无法解码图片: {}", filePath);
            }
            return mat;
        } catch (java.io.IOException e) {
            log.warn("读取图片文件失败: {}, 原因: {}", filePath, e.getMessage());
            return new Mat();
        }
    }

    /**
     * 使用OpenCV解码字节数组为Mat
     */
    public Mat decodeImageMat(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            return new Mat();
        }
        Mat mat = Imgcodecs.imdecode(new MatOfByte(imageBytes), Imgcodecs.IMREAD_GRAYSCALE);
        if (mat.empty()) {
            log.warn("OpenCV无法解码图片字节流");
        }
        return mat;
    }

    /**
     * BufferedImage 转换为 OpenCV Mat
     */
    public Mat bufferedImageToMat(BufferedImage image) {
        if (image == null) {
            return new Mat();
        }
        try (java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream()) {
            javax.imageio.ImageIO.write(image, "png", baos);
            byte[] bytes = baos.toByteArray();
            return decodeImageMat(bytes);
        } catch (Exception e) {
            throw new RuntimeException("图片转换失败: " + e.getMessage(), e);
        }
    }
}

