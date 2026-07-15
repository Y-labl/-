package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.Tesseract1;
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

    private Tesseract1 tesseract;

    @Value("${script.tesseract.datapath:#{null}}")
    private String dataPath;

    @Value("${script.tesseract.language:eng}")
    private String language;

    @Value("${script.tesseract.chinese-whitelist:}")
    private String chineseWhitelist;

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
            String tessPath = resolveTessdataPath(path);
            effectiveDataPath = tessPath;
            log.info("reinit tessdata path: {}", tessPath);
            setTessEnv(tessPath);
            tesseract = new Tesseract1();
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
        int GetShortPathNameW(com.sun.jna.WString lpszLongPath, char[] lpszShortPath, int cchBuffer);
    }

    /**
     * Convert a long Windows path to short 8.3 format to avoid spaces.
     * Falls back to original path if conversion fails.
     */
    private static String toShortPath(String longPath) {
        if (longPath == null || !longPath.contains(" ")) return longPath;
        try {
            char[] buffer = new char[512];
            int result = Kernel32.INSTANCE.GetShortPathNameW(
                new com.sun.jna.WString(longPath), buffer, buffer.length);
            if (result > 0 && result < buffer.length) {
                String shortPath = new String(buffer, 0, result);
                log.debug("Short path: {} -> {}", longPath, shortPath);
                return shortPath;
            }
        } catch (Throwable e) {
            log.debug("GetShortPathNameW failed: {}", e.getMessage());
        }
        return longPath;
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
        log.info("OCR configured datapath from config: {}", dataPath);
        effectiveDataPath = resolveTessdataPath(dataPath);
        log.info("OCR resolved tessdata path: {}", effectiveDataPath);
        setTessEnv(effectiveDataPath);
        tesseract = new Tesseract1();
        tesseract.setDatapath(effectiveDataPath);
        log.info("Tesseract initialized with datapath={}, language={}", effectiveDataPath, language);
        tesseract.setLanguage(language);
        tesseract.setOcrEngineMode(1);
        tesseract.setPageSegMode(7);
        checkLanguageData(effectiveDataPath, language);
    }


    /**
     * Resolve the tessdata directory path (the directory that DIRECTLY contains .traineddata files).
     *
     * Tesseract native behavior: if the datapath string ends with "tessdata",
     * it uses the path as-is; otherwise it appends "tessdata/".
     * So returning the directory itself (named "tessdata") is correct and simplest.
     */
    private String resolveTessdataPath(String configuredPath) {
        if (configuredPath != null && !configuredPath.isEmpty()) {
            File f = new File(configuredPath);
            // Case 1: .traineddata files directly in the configured path
            if (new File(f, "chi_sim.traineddata").exists()) {
                String path = f.getAbsolutePath().replace("\\", "/");
                log.info("Tessdata dir (direct): {}", path);
                return path;
            }
            // Case 2: .traineddata files in {configuredPath}/tessdata/
            File sub = new File(f, "tessdata");
            if (new File(sub, "chi_sim.traineddata").exists()) {
                String path = sub.getAbsolutePath().replace("\\", "/");
                log.info("Tessdata dir (subdir): {}", path);
                return path;
            }
        }
        return autoResolveTessdataDir();
    }

    /** Multi-strategy auto-detection of the tessdata directory */
    private String autoResolveTessdataDir() {
        // Strategy 1: D:/tessdata/ (standard deployment)
        if (new File("D:/tessdata/chi_sim.traineddata").exists()) {
            log.info("Auto-resolved tessdata: D:/tessdata");
            return "D:/tessdata";
        }
        // Strategy 2: {user.dir}/tessdata/
        String userDir = System.getProperty("user.dir");
        if (userDir != null) {
            File f = new File(userDir, "tessdata");
            if (new File(f, "chi_sim.traineddata").exists()) {
                String path = f.getAbsolutePath().replace("\\", "/");
                log.info("Auto-resolved tessdata via user.dir: {}", path);
                return path;
            }
        }
        // Strategy 3: classpath walk — find any ancestor containing tessdata/
        try {
            java.net.URL classUrl = OcrUtil.class.getProtectionDomain().getCodeSource().getLocation();
            File search = new File(classUrl.toURI());
            while (search != null) {
                File sub = new File(search, "tessdata");
                if (new File(sub, "chi_sim.traineddata").exists()) {
                    String path = sub.getAbsolutePath().replace("\\", "/");
                    log.info("Auto-resolved tessdata via classpath: {}", path);
                    return path;
                }
                search = search.getParentFile();
            }
        } catch (Exception e) {
            log.debug("Classpath resolution failed: {}", e.getMessage());
        }
        // Strategy 4: hardcoded fallback
        String[] hard = {"D:/tessdata",
                "D:/Program Files/mhxy-project/mhxy-script-server/tessdata",
                "D:/mhxy-script-server/tessdata"};
        for (String h : hard) {
            if (new File(h, "chi_sim.traineddata").exists()) {
                log.info("Auto-resolved tessdata via hardcoded: {}", h);
                return h;
            }
        }
        log.warn("Cannot find tessdata directory, using D:/tessdata as fallback");
        return "D:/tessdata";
    }

    /** 检查训练数据文件是否存在，返回缺失的语言列表 */
    private List<String> getMissingLanguages(String datapath, String lang) {
        List<String> missing = new ArrayList<>();
        if (lang == null || lang.isEmpty()) return missing;
        // datapath is the directory that directly contains .traineddata files;
        // fall back to datapath/tessdata/ for safety
        File[] candidates = {
            new File(datapath),
            new File(datapath, "tessdata")
        };
        File dir = null;
        for (File c : candidates) {
            if (c.exists() && c.isDirectory()) { dir = c; break; }
        }
        if (dir == null) {
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
        if (image == null) return "";
        lock.lock();
        try {
            // 数字识别用 eng 更快，避免加载 chi_sim 模型
            tesseract.setLanguage("eng");
            tesseract.setPageSegMode(7);
            tesseract.setTessVariable("tessedit_char_whitelist", DIGIT_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("Digit recognition failed: {}", e.getMessage());
            return "";
        } catch (Error e) {
            log.error("Tesseract native crash in recognizeDigits, reinitializing: {}", e.getMessage());
            reinit();
            return "";
        } finally {
            // 恢复默认语言和白名单
            tesseract.setLanguage(language);
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            lock.unlock();
        }
    }

    @SuppressWarnings("deprecation")
    public String recognizeAlphanum(BufferedImage image) {
        if (image == null) return "";
        lock.lock();
        try {
            tesseract.setLanguage(language);
            tesseract.setPageSegMode(7);
            tesseract.setTessVariable("tessedit_char_whitelist", ALPHANUM_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("Alphanum recognition failed: {}", e.getMessage());
            return "";
        } catch (Error e) {
            log.error("Tesseract native crash in recognizeAlphanum, reinitializing: {}", e.getMessage());
            reinit();
            return "";
        } finally {
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            lock.unlock();
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
        // 放大 4 倍并做灰度/对比度/锐化增强，提升小字体识别率
        BufferedImage scaled = scaleForOcr(image, 4.0);
        BufferedImage enhanced = enhanceForOcr(scaled);
        BufferedImage safe = preprocess(enhanced);
        if (safe == null) return "";

        saveDebugImage(safe, "ocr_chinese_input.png");

        lock.lock();
        try {
            // 仅使用 chi_sim，避免 eng 对中文的干扰
            tesseract.setLanguage("chi_sim");
            // PSM 7: 单行模式。比 PSM 6(文本块)更能利用"小_天"上下文区分形近字(西↔6)，且不逐字切出空格
            tesseract.setPageSegMode(7);
            // 场景名+数字白名单：限制识别字符集，消除形近字误判（如 西→本）
            String wl = (chineseWhitelist != null && !chineseWhitelist.isEmpty())
                    ? chineseWhitelist : "";
            tesseract.setTessVariable("tessedit_char_whitelist", wl);
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

    /** 灰度化并增强对比度/锐化，让文字更清晰 */
    private BufferedImage enhanceForOcr(BufferedImage image) {
        if (image == null) return null;
        BufferedImage gray = new BufferedImage(image.getWidth(), image.getHeight(), BufferedImage.TYPE_BYTE_GRAY);
        java.awt.Graphics2D g = gray.createGraphics();
        g.drawImage(image, 0, 0, null);
        g.dispose();

        // 对比度增强：1.6 倍对比度，5 亮度偏移
        RescaleOp rescale = new RescaleOp(1.6f, 5f, null);
        BufferedImage enhanced = rescale.filter(gray, null);

        // 锐化卷积核：突出文字笔画边缘，帮助区分形近字（西↔6）
        float[] kernel = {
            0, -1,  0,
           -1,  5, -1,
            0, -1,  0
        };
        java.awt.image.Kernel sharpenKernel = new java.awt.image.Kernel(3, 3, kernel);
        java.awt.image.ConvolveOp convolve = new java.awt.image.ConvolveOp(
                sharpenKernel, java.awt.image.ConvolveOp.EDGE_NO_OP, null);
        return convolve.filter(enhanced, null);
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