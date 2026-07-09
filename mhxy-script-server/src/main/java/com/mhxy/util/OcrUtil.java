package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.util.concurrent.locks.ReentrantLock;

/**
 * OCR text/number recognition utility.
 * Uses Tesseract LSTM engine for fast recognition.
 */
@Slf4j
@Component
public class OcrUtil {

    private ITesseract tesseract;

    @Value("${script.tesseract.datapath:#{null}}")
    private String dataPath;

    @Value("${script.tesseract.language:eng}")
    private String language;

    private final ReentrantLock lock = new ReentrantLock();

    private static final String DIGIT_WHITELIST = "0123456789.-";
    private static final String ALPHANUM_WHITELIST = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-%+/";


    /** 预处理图片，确保与Tesseract兼容 */
    private BufferedImage preprocess(BufferedImage image) {
        if (image == null) return null;
        // 确保是支持的图像类型
        int type = image.getType();
        if (type == BufferedImage.TYPE_INT_RGB || type == BufferedImage.TYPE_INT_ARGB || type == BufferedImage.TYPE_BYTE_GRAY) {
            return image;
        }
        // 转换为 ARGB 避免 JNA 内存访问问题
        BufferedImage converted = new BufferedImage(image.getWidth(), image.getHeight(), BufferedImage.TYPE_INT_ARGB);
        java.awt.Graphics2D g = converted.createGraphics();
        g.drawImage(image, 0, 0, null);
        g.dispose();
        return converted;
    }

    /** 重新初始化Tesseract（错误恢复） */
    private void reinit() {
        try {
            tesseract = null;
            System.gc();
            Thread.sleep(100);
            tesseract = new Tesseract();
            if (dataPath != null && !dataPath.isEmpty()) {
                tesseract.setDatapath(dataPath);
            } else {
                tesseract.setDatapath(new File("tessdata").getAbsolutePath());
            }
            tesseract.setLanguage(language);
            tesseract.setOcrEngineMode(1);
            tesseract.setPageSegMode(7);
            log.info("Tesseract reinitialized after crash");
        } catch (Exception e) {
            log.error("Tesseract reinit failed: {}", e.getMessage());
        }
    }
    @PostConstruct
    public void init() {
        tesseract = new Tesseract();
        String effectiveDataPath = dataPath;
        if (effectiveDataPath == null || effectiveDataPath.isEmpty()) {
            effectiveDataPath = new File("tessdata").getAbsolutePath();
        }
        tesseract.setDatapath(effectiveDataPath);
        tesseract.setLanguage(language);
        tesseract.setOcrEngineMode(1);
        tesseract.setPageSegMode(7);
        checkLanguageData(effectiveDataPath, language);
        log.info("OCR engine initialized: datapath={}, language={}", effectiveDataPath, language);
    }

    /** 检查训练数据文件是否存在，缺失时在日志中给出明确提示 */
    private void checkLanguageData(String effectiveDataPath, String lang) {
        if (lang == null || lang.isEmpty()) return;
        File dir = new File(effectiveDataPath);
        if (!dir.exists() || !dir.isDirectory()) {
            log.warn("Tesseract tessdata 目录不存在: {}，OCR 将无法识别文字，请下载对应 .traineddata 文件放入该目录", effectiveDataPath);
            return;
        }
        for (String l : lang.split("\\+")) {
            File trainedData = new File(dir, l + ".traineddata");
            if (!trainedData.exists()) {
                log.warn("缺少 Tesseract 语言训练数据: {}，中文识别请下载 chi_sim.traineddata 放到 {}", trainedData.getName(), effectiveDataPath);
            }
        }
    }

    @SuppressWarnings("deprecation")
    public String recognizeDigits(BufferedImage image) {
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", DIGIT_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("Digit recognition failed: {}", e.getMessage());
            return "";
        }
    }

    @SuppressWarnings("deprecation")
    public String recognizeAlphanum(BufferedImage image) {
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", ALPHANUM_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("Alphanum recognition failed: {}", e.getMessage());
            return "";
        }
    }

    @SuppressWarnings("deprecation")
    public String recognize(BufferedImage image) {
        BufferedImage safe = preprocess(image);
        if (safe == null) return "";
        lock.lock();
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            return tesseract.doOCR(safe).trim();
        } catch (TesseractException e) {
            log.error("OCR recognition failed: {}", e.getMessage());
            return "";
        } catch (Error e) {
            log.error("Tesseract native crash, reinitializing: {}", e.getMessage());
            reinit();
            return "";
        } finally {
            lock.unlock();
        }
    }

    /**
     * 中文识别：放大 ROI 并切换到 chi_sim 语言模型
     */
    @SuppressWarnings("deprecation")
    public String recognizeChinese(BufferedImage image) {
        if (image == null) return "";
        BufferedImage scaled = scaleForOcr(image, 2.0);
        BufferedImage safe = preprocess(scaled);
        if (safe == null) return "";
        lock.lock();
        try {
            // 临时切换到中文语言包；若不存在会回退到 eng
            tesseract.setLanguage("chi_sim+eng");
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            String text = tesseract.doOCR(safe).trim();
            // 恢复默认语言
            tesseract.setLanguage(language);
            return text;
        } catch (TesseractException e) {
            log.error("Chinese OCR recognition failed: {}", e.getMessage());
            return "";
        } catch (Error e) {
            log.error("Tesseract native crash, reinitializing: {}", e.getMessage());
            reinit();
            return "";
        } finally {
            lock.unlock();
        }
    }

    /** 放大图像以提升小字体识别率 */
    private BufferedImage scaleForOcr(BufferedImage image, double scale) {
        if (scale <= 1.0) return image;
        int w = (int) (image.getWidth() * scale);
        int h = (int) (image.getHeight() * scale);
        BufferedImage scaled = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        java.awt.Graphics2D g = scaled.createGraphics();
        g.setRenderingHint(java.awt.RenderingHints.KEY_INTERPOLATION, java.awt.RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.drawImage(image, 0, 0, w, h, null);
        g.dispose();
        return scaled;
    }

    public String recognizeDigits(BufferedImage image, String label) {
        long start = System.nanoTime();
        String result = recognizeDigits(image);
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        log.debug("OCR[{}]: {} | {}ms", label, result, elapsed);
        return result;
    }

    public void setPageSegMode(int psm) {
        tesseract.setPageSegMode(psm);
    }

    @SuppressWarnings("deprecation")
    public void setWhitelist(String whitelist) {
        tesseract.setTessVariable("tessedit_char_whitelist", whitelist);
    }

    /**
     * Convert byte array to BufferedImage.
     */
    public BufferedImage bytesToImage(byte[] bytes) {
        try {
            return ImageIO.read(new ByteArrayInputStream(bytes));
        } catch (Exception e) {
            log.error("bytesToImage failed: {}", e.getMessage());
            return null;
        }
    }

    @PreDestroy
    public void destroy() {
        tesseract = null;
        log.info("OCR engine released");
    }
}