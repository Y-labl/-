package com.mhxy;

import net.sourceforge.tess4j.ITessAPI;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import net.sourceforge.tess4j.util.LoadLibs;
import org.bytedeco.javacv.*;
import org.bytedeco.javacv.Frame;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.Size;
import org.bytedeco.opencv.global.opencv_imgproc;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class Test {

    // 👇【请确认】你的 tessdata 路径（必须存在 chi_sim.traineddata）
    private static final String DATAPATH = "D:/tessdata"; // ← 修改为你实际的 tessdata 目录
    private static final String LANG = "chi_sim";

    public static void main(String[] args) {
        // ✅ 硬编码图片路径（你指定的）
        String imagePath = "D:/pythonDemo/OCR/images/小西天1.png";
        File imageFile = new File(imagePath);

        if (!imageFile.exists()) {
            System.err.println("❌ 图片不存在: " + imagePath);
            return;
        }

        try {
            String result = recognize(imageFile);
            System.out.println("\n✅ 识别结果：");
            System.out.println("--------------------------------------------------");
            System.out.println(result);
            System.out.println("--------------------------------------------------");
        } catch (Exception e) {
            System.err.println("❌ OCR 失败：" + e.getMessage());
            e.printStackTrace();
        }
    }

    private static String recognize(File imageFile) throws IOException, TesseractException {
        BufferedImage src = ImageIO.read(imageFile);
        if (src == null) {
            throw new IOException("无法读取图片: " + imageFile.getAbsolutePath());
        }

        System.out.println("📸 已保存预处理图: " + savePreprocessedImage(src));

        // 预处理：放大 + 二值化
        BufferedImage processed = preprocessImage(src);

        // 初始化 Tesseract
        ITesseract tesseract = new Tesseract();
        tesseract.setDatapath(DATAPATH);
        tesseract.setLanguage(LANG);

        // ✅ 修正：使用 ITessAPI.TessPageSegMode
        tesseract.setPageSegMode(ITessAPI.TessPageSegMode.PSM_SINGLE_BLOCK);

        // ✅ 关键：只允许“小西天”三个字（防错识别）
//        tesseract.setVariable("tessedit_char_whitelist", "小西天");

        // 执行识别
        String result = tesseract.doOCR(processed).trim();
        return result.isEmpty() ? "[空]" : result;
    }

    /**
     * 图像预处理：灰度化 → OTSU二值化 → 形态学去噪 → 放大2.5倍
     */
    private static BufferedImage preprocessImage(BufferedImage src) {
        try (Java2DFrameConverter java2dConverter = new Java2DFrameConverter();
             OpenCVFrameConverter.ToMat openCvConverter = new OpenCVFrameConverter.ToMat()) {

            // 1. BufferedImage → Frame → Mat
            Frame frame = java2dConverter.convert(src);
            Mat srcMat = openCvConverter.convert(frame);

            Mat gray = new Mat();
            Mat binary = new Mat();

            // 2. 灰度化 + OTSU 二值化
            opencv_imgproc.cvtColor(srcMat, gray, opencv_imgproc.COLOR_BGR2GRAY);
            opencv_imgproc.threshold(gray, binary, 0, 255,
                    opencv_imgproc.THRESH_BINARY | opencv_imgproc.THRESH_OTSU);

            // 3. 形态学开运算去噪（kernel 2x2）
            Mat kernel = opencv_imgproc.getStructuringElement(
                    opencv_imgproc.MORPH_RECT, new Size(2, 2));
            opencv_imgproc.morphologyEx(binary, binary, opencv_imgproc.MORPH_OPEN, kernel);

            // 4. Mat → Frame → BufferedImage
            Frame resultFrame = openCvConverter.convert(binary);
            BufferedImage processed = java2dConverter.convert(resultFrame);

            // ✅ 关键步骤：放大2.5倍（提升小字识别率）
            double scale = 2.5;
            int w = processed.getWidth();
            int h = processed.getHeight();
            BufferedImage scaled = new BufferedImage(
                    (int) (w * scale), (int) (h * scale), BufferedImage.TYPE_BYTE_BINARY);
            Graphics2D g = scaled.createGraphics();
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            g.drawImage(processed, 0, 0, (int) (w * scale), (int) (h * scale), null);
            g.dispose();

            return scaled;

        } catch (Exception e) {
            System.err.println("⚠️ OpenCV 预处理失败，降级使用简易灰度+阈值: " + e.getMessage());
            return fallbackPreprocess(src);
        }
    }

    /**
     * 降级预处理（纯 Java，无 OpenCV）
     */
    private static BufferedImage fallbackPreprocess(BufferedImage src) {
        int w = src.getWidth();
        int h = src.getHeight();
        BufferedImage gray = new BufferedImage(w, h, BufferedImage.TYPE_BYTE_GRAY);
        Graphics2D g = gray.createGraphics();
        g.drawImage(src, 0, 0, w, h, null);
        g.dispose();

        BufferedImage binary = new BufferedImage(w, h, BufferedImage.TYPE_BYTE_BINARY);
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                int grayVal = gray.getRGB(x, y) & 0xFF;
                int binVal = grayVal > 180 ? 0xFF : 0; // 黑字白底
                binary.setRGB(x, y, binVal | (binVal << 8) | (binVal << 16) | 0xFF000000);
            }
        }

        // 放大2.5倍
        double scale = 2.5;
        BufferedImage scaled = new BufferedImage((int)(w * scale), (int)(h * scale), BufferedImage.TYPE_BYTE_BINARY);
        g = scaled.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.drawImage(binary, 0, 0, (int)(w * scale), (int)(h * scale), null);
        g.dispose();
        return scaled;
    }

    /**
     * 保存预处理前的图像（用于调试）
     */
    private static String savePreprocessedImage(BufferedImage src) throws IOException {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmssSSS"));
        String filename = "D:/pythonDemo/OCR/images/" + timestamp + "_ocr_input.png";
        File file = new File(filename);
        ImageIO.write(src, "png", file);
        return filename;
    }
}