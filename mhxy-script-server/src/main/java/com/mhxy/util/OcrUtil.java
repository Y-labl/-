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
import java.awt.image.RescaleOp;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
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

    private String effectiveDataPath;

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
            String path = effectiveDataPath;
            if (path == null) {
                path = new File("tessdata").getAbsolutePath();
            }
            System.setProperty("TESSDATA_PREFIX", path);
            tesseract.setDatapath(path);
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
        // 将路径标准化为操作系统原生格式，避免正斜杠在 Windows 原生层不兼容
        effectiveDataPath = dataPath;
        if (effectiveDataPath == null || effectiveDataPath.isEmpty()) {
            // Tess4J 5.x datapath应指向tessdata的父目录
            // 从 user.dir 向上递归搜索 tessdata 目录
            String userDir = System.getProperty("user.dir");
            File searchDir = new File(userDir);
            while (searchDir != null) {
                File tessdata = new File(searchDir, "tessdata");
                if (new File(tessdata, "chi_sim.traineddata").exists()) {
                    effectiveDataPath = searchDir.getAbsolutePath();
                    break;
                }
                searchDir = searchDir.getParentFile();
            }
            // 也搜索子目录（处理 IDE 多模块场景）
            if (effectiveDataPath == null) {
                File[] subDirs = new File(userDir).listFiles(File::isDirectory);
                if (subDirs != null) {
                    for (File sub : subDirs) {
                        File tessdata = new File(sub, "tessdata");
                        if (new File(tessdata, "chi_sim.traineddata").exists()) {
                            effectiveDataPath = sub.getAbsolutePath();
                            break;
                        }
                    }
                }
            }
            if (effectiveDataPath == null) {
                effectiveDataPath = userDir;
            }
        }
        effectiveDataPath = new File(effectiveDataPath).getAbsolutePath();
        // 设置环境变量，让 Tesseract 原生库也能找到训练数据
        System.setProperty("TESSDATA_PREFIX", effectiveDataPath);
        tesseract = new Tesseract();
        tesseract.setDatapath(effectiveDataPath);
        tesseract.setLanguage(language);
        tesseract.setOcrEngineMode(1);
        tesseract.setPageSegMode(7);
        checkLanguageData(effectiveDataPath, language);
        log.info("OCR engine initialized: datapath={}, language={}", effectiveDataPath, language);
    }

    /** 检查训练数据文件是否存在，返回缺失的语言列表 */
    private List<String> getMissingLanguages(String datapath, String lang) {
        List<String> missing = new ArrayList<>();
        if (lang == null || lang.isEmpty()) return missing;
        // Tess4J 5.x 内部会拼接 /tessdata/ 子目录，所以检查 datapath/tessdata/ 下的文件
        File tessdataDir = new File(datapath, "tessdata");
        File dir = tessdataDir.exists() && tessdataDir.isDirectory() ? tessdataDir : new File(datapath);
        if (!dir.exists() || !dir.isDirectory()) {
            for (String l : lang.split("\\+")) {
                missing.add(l);
            }
            return missing;
        }
        for (String l : lang.split("\\+")) {
            File trainedData = new File(dir, l + ".traineddata");
            if (!trainedData.exists()) {
                missing.add(l);
            }
        }
        return missing;
    }

    /** 检查训练数据文件是否存在，缺失时在日志中给出明确提示 */
    private void checkLanguageData(String datapath, String lang) {
        List<String> missing = getMissingLanguages(datapath, lang);
        if (missing.isEmpty()) return;
        File dir = new File(datapath);
        if (!dir.exists() || !dir.isDirectory()) {
            log.warn("Tesseract tessdata 目录不存在: {}，OCR 将无法识别文字，请下载对应 .traineddata 文件放入该目录", datapath);
            return;
        }
        for (String l : missing) {
            log.warn("缺少 Tesseract 语言训练数据: {}.traineddata，中文识别请下载 chi_sim.traineddata 放到 {}", l, datapath);
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
        List<String> missing = getMissingLanguages(effectiveDataPath, language);
        if (!missing.isEmpty()) {
            String msg = "[OCR 失败：缺少语言训练数据 " + missing + ".traineddata，请放到 " + effectiveDataPath + "]";
            log.warn(msg);
            return msg;
        }
        lock.lock();
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            return tesseract.doOCR(safe).trim();
        } catch (TesseractException e) {
            String msg = e.getMessage() != null ? e.getMessage() : "";
            if (isLanguageMissingError(msg)) {
                String warn = "[OCR 失败：Tesseract 无法加载语言数据，请检查 " + effectiveDataPath + " 目录]";
                log.error(warn + ": {}", msg);
                return warn;
            }
            log.error("OCR recognition failed: {}", msg);
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
     * 中文识别：放大 ROI、增强对比度并切换到 chi_sim 语言模型
     */
    @SuppressWarnings("deprecation")
    public String recognizeChinese(BufferedImage image) {
        if (image == null) return "";
        List<String> missing = getMissingLanguages(effectiveDataPath, "chi_sim");
        if (!missing.isEmpty()) {
            String msg = "[OCR 失败：缺少语言训练数据 " + missing + ".traineddata，请放到 " + effectiveDataPath + "]";
            log.warn(msg);
            return msg;
        }
        // 放大 2 倍并做灰度/对比度增强，提升小字体识别率
        BufferedImage scaled = scaleForOcr(image, 2.0);
        BufferedImage enhanced = enhanceForOcr(scaled);
        BufferedImage safe = preprocess(enhanced);
        if (safe == null) return "";

        saveDebugImage(safe, "ocr_chinese_input.png");

        lock.lock();
        try {
            // 仅使用 chi_sim，避免 eng 对中文的干扰
            tesseract.setLanguage("chi_sim");
            // 对整块文字区域进行识别，比单行模式更适合地名+坐标的多行结构
            tesseract.setPageSegMode(6);
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            String text = tesseract.doOCR(safe).trim();
            // 恢复默认语言和页面模式
            tesseract.setLanguage(language);
            tesseract.setPageSegMode(7);
            log.debug("Chinese OCR result: {}", text);
            return text;
        } catch (TesseractException e) {
            String msg = e.getMessage() != null ? e.getMessage() : "";
            if (isLanguageMissingError(msg)) {
                String warn = "[OCR 失败：Tesseract 无法加载语言数据，请检查 " + effectiveDataPath + " 目录]";
                log.error(warn + ": {}", msg);
                return warn;
            }
            log.error("Chinese OCR recognition failed: {}", msg);
            return "";
        } catch (Error e) {
            log.error("Tesseract native crash, reinitializing: {}", e.getMessage());
            reinit();
            return "";
        } finally {
            lock.unlock();
        }
    }

    /** 灰度化并增强对比度，让文字更清晰 */
    private BufferedImage enhanceForOcr(BufferedImage image) {
        if (image == null) return null;
        BufferedImage gray = new BufferedImage(image.getWidth(), image.getHeight(), BufferedImage.TYPE_BYTE_GRAY);
        java.awt.Graphics2D g = gray.createGraphics();
        g.drawImage(image, 0, 0, null);
        g.dispose();

        // 简单对比度增强：1.5 倍对比度，10 亮度偏移
        RescaleOp rescale = new RescaleOp(1.5f, 10f, null);
        BufferedImage enhanced = rescale.filter(gray, null);
        return enhanced;
    }

    /** 保存调试图片，便于排查识别问题 */
    private void saveDebugImage(BufferedImage image, String fileName) {
        try {
            File debugDir = new File("screenshots/ocr-debug");
            if (!debugDir.exists()) debugDir.mkdirs();
            File file = new File(debugDir, System.currentTimeMillis() + "_" + fileName);
            ImageIO.write(image, "png", file);
            log.debug("OCR debug image saved: {}", file.getAbsolutePath());
        } catch (IOException e) {
            log.debug("Failed to save OCR debug image: {}", e.getMessage());
        }
    }

    /** 判断异常是否由语言训练数据缺失引起 */
    private boolean isLanguageMissingError(String message) {
        if (message == null) return false;
        String lower = message.toLowerCase();
        return lower.contains("failed loading language") || lower.contains("can not find language data")
                || lower.contains("could not load language") || lower.contains("missing language data");
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