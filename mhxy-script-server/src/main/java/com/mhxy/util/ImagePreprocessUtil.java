package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import org.opencv.core.*;
import org.opencv.imgproc.Imgproc;
import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;

/**
 * 图像预处理工具类 —— 为 OCR 和模板匹配提供预处理能力
 * <p>
 * 核心优化：
 * <ul>
 *   <li>灰度化：移除颜色通道，减少计算量</li>
 *   <li>缩放：缩小图像以加速 OCR（游戏数字特征保留）</li>
 *   <li>自适应阈值二值化：消除光照/背景噪声</li>
 *   <li>形态学操作：去噪、增强字符轮廓</li>
 * </ul>
 */
@Slf4j
@Component
public class ImagePreprocessUtil {

    static {
        nu.pattern.OpenCV.loadShared();
    }

    /**
     * BufferedImage → Mat (BGR)
     */
    public Mat bufferedImageToMat(BufferedImage image) {
        if (image.getType() == BufferedImage.TYPE_3BYTE_BGR) {
            // 直接零拷贝转换（性能最优）
            byte[] data = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
            Mat mat = new Mat(image.getHeight(), image.getWidth(), CvType.CV_8UC3);
            mat.put(0, 0, data);
            return mat;
        }
        // 兜底：通过 byte[] 中转
        try (java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream()) {
            javax.imageio.ImageIO.write(image, "png", baos);
            byte[] bytes = baos.toByteArray();
            return org.opencv.imgcodecs.Imgcodecs.imdecode(
                    new Mat(1, bytes.length, CvType.CV_8UC1),
                    org.opencv.imgcodecs.Imgcodecs.IMREAD_COLOR);
        } catch (Exception e) {
            throw new RuntimeException("BufferedImage→Mat 转换失败: " + e.getMessage(), e);
        }
    }

    /**
     * Mat → BufferedImage (BGR)
     */
    public BufferedImage matToBufferedImage(Mat mat) {
        int type = mat.channels() > 1
                ? BufferedImage.TYPE_3BYTE_BGR
                : BufferedImage.TYPE_BYTE_GRAY;
        BufferedImage image = new BufferedImage(mat.cols(), mat.rows(), type);
        byte[] data = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
        mat.get(0, 0, data);
        return image;
    }

    /**
     * 标准 OCR 预处理流水线（灰度化 → 缩放 → 自适应阈值 → 形态学去噪）
     * <p>适用于游戏内数字/文字识别，一次调用完成所有预处理</p>
     *
     * @param image  原始截图（通常是 ROI 区域）
     * @param scale  缩放比例，如 0.5 表示缩小到 50%
     * @return 预处理后的二值化图像
     */
    public Mat preprocessForOCR(BufferedImage image, double scale) {
        Mat src = bufferedImageToMat(image);

        // 1. 灰度化（3通道 → 1通道，数据量降为1/3）
        Mat gray = new Mat();
        Imgproc.cvtColor(src, gray, Imgproc.COLOR_BGR2GRAY);
        src.release();

        // 2. 缩放（降低分辨率加速 OCR）
        Mat scaled = new Mat();
        if (scale > 0 && scale < 1.0) {
            Imgproc.resize(gray, scaled, new Size(), scale, scale, Imgproc.INTER_LINEAR);
            gray.release();
        } else {
            scaled = gray;
        }

        // 3. 自适应阈值二值化（对抗不均匀光照）
        Mat binary = new Mat();
        Imgproc.adaptiveThreshold(scaled, binary, 255,
                Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C,
                Imgproc.THRESH_BINARY,
                11,  // 邻域大小（奇数）
                2);  // 常数偏移
        scaled.release();

        // 4. 形态学去噪（开运算：先腐蚀再膨胀，去除小噪点）
        Mat denoised = new Mat();
        Mat kernel = Imgproc.getStructuringElement(Imgproc.MORPH_RECT, new Size(2, 2));
        Imgproc.morphologyEx(binary, denoised, Imgproc.MORPH_OPEN, kernel);
        binary.release();
        kernel.release();

        return denoised;
    }

    /**
     * 简化版预处理（灰度化 + 缩放），适用于匹配前预处理
     */
    public Mat toGrayAndResize(BufferedImage image, double scale) {
        Mat src = bufferedImageToMat(image);
        Mat gray = new Mat();
        Imgproc.cvtColor(src, gray, Imgproc.COLOR_BGR2GRAY);
        src.release();

        if (scale > 0 && scale < 1.0) {
            Mat scaled = new Mat();
            Imgproc.resize(gray, scaled, new Size(), scale, scale, Imgproc.INTER_LINEAR);
            gray.release();
            return scaled;
        }
        return gray;
    }

    /**
     * 快速灰度化（不缩放）
     */
    public Mat toGray(BufferedImage image) {
        Mat src = bufferedImageToMat(image);
        Mat gray = new Mat();
        Imgproc.cvtColor(src, gray, Imgproc.COLOR_BGR2GRAY);
        src.release();
        return gray;
    }
}
