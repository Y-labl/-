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
import java.util.Map;
import java.lang.reflect.Field;
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
            String path = effectiveDataPath;
            if (path == null) {
                path = System.getProperty("user.dir");
            }
            String tessPath = new File(path, "tessdata").getAbsolutePath();
            log.info("reinit tessdata path: {}", tessPath);
            setTessEnv(tessPath);
            tesseract = new Tesseract();
            tesseract.setDatapath(tessPath);
            tesseract.setLanguage(language);
            tesseract.setOcrEngineMode(1);
            tesseract.setPageSegMode(7);
            log.info("Tesseract reinitialized after crash");
        } catch (Exception e) {
            log.error("Tesseract reinit failed: {}", e.getMessage());
        }
    }

    /**
     * Kernel32 interface for calling SetEnvironmentVariableW via JNA (already on classpath from Tess4J).
     */
    private interface Kernel32 extends com.sun.jna.Library {
        Kernel32 INSTANCE = com.sun.jna.Native.load("kernel32", Kernel32.class);
        boolean SetEnvironmentVariableW(com.sun.jna.WString lpName, com.sun.jna.WString lpValue);
    }

    /**
     * Set TESSDATA_PREFIX at the OS level.  The Win32 call makes it visible to the
     * native Tesseract C library immediately.  The ProcessEnvironment call updates
     * Java cached env map used by System.getenv().
     */
    private static void setTessEnv(String tessDataPrefix) {
        boolean ok = false;
        try {
            Kernel32.INSTANCE.SetEnvironmentVariableW(
                new com.sun.jna.WString("TESSDATA_PREFIX"),
                new com.sun.jna.WString(tessDataPrefix));
            ok = true;
            log.info("TESSDATA_PREFIX set via Win32 API: {}", tessDataPrefix);
        } catch (Throwable e) {
            log.debug("Win32 SetEnvironmentVariableW failed: {}", e.getMessage());
        }
        try {
            Class<?> pe = Class.forName("java.lang.ProcessEnvironment");
            java.lang.reflect.Field f = pe.getDeclaredField("theCaseInsensitiveEnvironment");
            f.setAccessible(true);
            @SuppressWarnings("unchecked")
            java.util.Map<String, String> env = (java.util.Map<String, String>) f.get(null);
            env.put("TESSDATA_PREFIX", tessDataPrefix);
            ok = true;
            log.info("TESSDATA_PREFIX set via ProcessEnvironment: {}", tessDataPrefix);
        } catch (Throwable e) {
            log.debug("ProcessEnvironment fallback failed: {}", e.getMessage());
        }
        if (!ok) {
            log.warn("Failed to set TESSDATA_PREFIX at OS level, relying on setDatapath only");
        }
    }

    @PostConstruct
    public void init() {
        // 获取配置的 datapath（可能来自 application.yml）
        effectiveDataPath = dataPath;
        log.info("OCR configured datapath from config: {}", effectiveDataPath);
        // 如果配置了但路径无效（无 tessdata 子目录），则回退到自动解析
        if (effectiveDataPath != null && !effectiveDataPath.isEmpty()) {
            File testDir = new File(new File(effectiveDataPath), "tessdata");
            if (!testDir.exists() || !testDir.isDirectory()) {
                log.warn("Configured datapath has no tessdata/ subdir: {}, falling back to auto-resolve", effectiveDataPath);
                effectiveDataPath = null;
            }
        }
        if (effectiveDataPath == null || effectiveDataPath.isEmpty()) {
            effectiveDataPath = autoResolveTessdataDir();
        }
        effectiveDataPath = new File(effectiveDataPath).getAbsolutePath();
        log.info("OCR final effectiveDataPath: {}", effectiveDataPath);
        // Tesseract datapath must point to the tessdata/ subdirectory directly
        String tessdataDir = new File(effectiveDataPath, "tessdata").getAbsolutePath();
        log.info("OCR tessdata directory: {}", tessdataDir);
        // 注入 OS 环境变量 + Java 缓存
        setTessEnv(tessdataDir);
        tesseract = new Tesseract();
        tesseract.setDatapath(tessdataDir);
        log.info("Tesseract initialized with datapath={}, language={}", tessdataDir, language);
        tesseract.setLanguage(language);
        tesseract.setOcrEngineMode(1);
        tesseract.setPageSegMode(7);
        checkLanguageData(effectiveDataPath, language);
    }

    /** 多策略自动解析包含 tessdata/ 子目录的路径 */
    private String autoResolveTessdataDir() {
        // 策略1: classpath 向上查找
        try {
            java.net.URL classUrl = OcrUtil.class.getProtectionDomain().getCodeSource().getLocation();
            File classDir = new File(classUrl.toURI());
            File root = classDir;
            while (root != null && !"mhxy-script-server".equals(root.getName())) {
                if (new File(new File(root, "tessdata"), "chi_sim.traineddata").exists()) {
                    log.info("OCR resolved tessdata via classpath walk: {}", root.getAbsolutePath());
                    return root.getAbsolutePath();
                }
                root = root.getParentFile();
            }
            if (root != null) {
                File f = new File(new File(root, "tessdata"), "chi_sim.traineddata");
                if (f.exists()) {
                    log.info("OCR resolved tessdata via project root: {}", root.getAbsolutePath());
                    return root.getAbsolutePath();
                }
            }
        } catch (Exception e) {
            log.debug("Classpath resolution failed: {}", e.getMessage());
        }
        // 策略2: user.dir
        String userDir = System.getProperty("user.dir");
        if (userDir != null) {
            File f = new File(new File(userDir, "tessdata"), "chi_sim.traineddata");
            if (f.exists()) {
                log.info("OCR resolved tessdata via user.dir: {}", userDir);
                return userDir;
            }
            // 也检查父目录
            File parent = new File(userDir).getParentFile();
            if (parent != null) {
                f = new File(new File(parent, "tessdata"), "chi_sim.traineddata");
                if (f.exists()) {
                    log.info("OCR resolved tessdata via user.dir parent: {}", parent.getAbsolutePath());
                    return parent.getAbsolutePath();
                }
            }
        }
        // 策略3: 硬编码路径
        String[] hard = {"D:/Program Files/mhxy-project/mhxy-script-server", "D:/mhxy-script-server"};
        for (String h : hard) {
            if (new File(new File(h, "tessdata"), "chi_sim.traineddata").exists()) {
                log.info("OCR resolved tessdata via hardcoded path: {}", h);
                return h;
            }
        }
        log.warn("Cannot find tessdata directory, using user.dir as fallback");
        return System.getProperty("user.dir");
    }

    /** 检查训练数据文件是否存在，返回缺失的语言列表 */
    private List<String> getMissingLanguages(String datapath, String lang) {
        List<String> missing = new ArrayList<>();
        if (lang == null || lang.isEmpty()) return missing;
        // datapath now points directly to tessdata/ directory
        File dir = new File(datapath);
        // Also check parent/tessdata for backward compatibility
        if (!dir.exists() || !dir.isDirectory()) {
            File alt = new File(new File(datapath), "tessdata");
            if (alt.exists() && alt.isDirectory()) dir = alt;
        }
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