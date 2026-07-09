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
        if (dataPath != null && !dataPath.isEmpty()) {
            tesseract.setDatapath(dataPath);
        } else {
            tesseract.setDatapath(new File("tessdata").getAbsolutePath());
        }
        tesseract.setLanguage(language);
        tesseract.setOcrEngineMode(1);
        tesseract.setPageSegMode(7);
        log.info("OCR engine initialized: datapath={}, language={}", dataPath, language);
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