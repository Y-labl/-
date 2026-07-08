package com.mhxy.util;

import lombok.extern.slf4j.Slf4j;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.awt.image.BufferedImage;
import java.io.File;

/**
 * OCR 文字/数字识别工具类
 * <p>
 * 关键优化：
 * <ul>
 *   <li>LSTM 引擎：比传统 Tesseract 引擎快 2-3 倍</li>
 *   <li>字符白名单：限制只识别数字和特定符号，大幅减少计算量</li>
 *   <li>PSM 模式：单行文本模式，跳过版面分析</li>
 * </ul>
 */
@Slf4j
@Component
public class OcrUtil {

    private ITesseract tesseract;

    @Value("${script.tesseract.datapath:#{null}}")
    private String dataPath;

    @Value("${script.tesseract.language:eng}")
    private String language;

    /** 数字识别默认白名单 */
    private static final String DIGIT_WHITELIST = "0123456789.-";

    /** 常用符号 + 数字 */
    private static final String ALPHANUM_WHITELIST = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-%+/";

    @PostConstruct
    public void init() {
        tesseract = new Tesseract();

        // 设置 tessdata 路径（从配置读取，或自动检测）
        if (dataPath != null && !dataPath.isEmpty()) {
            tesseract.setDatapath(dataPath);
        } else {
            // 默认路径：项目根目录下的 tessdata
            String defaultPath = new File("tessdata").getAbsolutePath();
            tesseract.setDatapath(defaultPath);
        }

        // 默认语言
        tesseract.setLanguage(language);

        // 使用 LSTM 引擎（OEM_LSTM_ONLY = 1）
        // OEM_TESSERACT_LSTM_COMBINED = 3, OEM_LSTM_ONLY = 1
        tesseract.setOcrEngineMode(1);

        // 默认单行模式（PSM_SINGLE_LINE = 7），跳过版面分析
        tesseract.setPageSegMode(7);

        log.info("OCR 引擎初始化完成: datapath={}, language={}", dataPath, language);
    }

    /**
     * 识别数字（限制字符集为 0123456789.-）
     *
     * @param image 预处理后的图像
     * @return 识别出的数字字符串
     */
    @SuppressWarnings("deprecation")
    public String recognizeDigits(BufferedImage image) {
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", DIGIT_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("数字识别失败: {}", e.getMessage());
            return "";
        }
    }

    /**
     * 识别数字 + 字母
     */
    @SuppressWarnings("deprecation")
    public String recognizeAlphanum(BufferedImage image) {
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", ALPHANUM_WHITELIST);
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("字符识别失败: {}", e.getMessage());
            return "";
        }
    }

    /**
     * 完整 OCR 识别（无字符限制）
     */
    @SuppressWarnings("deprecation")
    public String recognize(BufferedImage image) {
        try {
            tesseract.setTessVariable("tessedit_char_whitelist", "");
            return tesseract.doOCR(image).trim();
        } catch (TesseractException e) {
            log.error("OCR 识别失败: {}", e.getMessage());
            return "";
        }
    }

    /**
     * 数字识别（带计时日志，方便性能调优）
     *
     * @param image 预处理后的图像
     * @param label 日志标签，如 "血量"、"蓝量"
     * @return 识别出的数字
     */
    public String recognizeDigits(BufferedImage image, String label) {
        long start = System.nanoTime();
        String result = recognizeDigits(image);
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        log.debug("OCR识别[{}]: {} | 耗时 {}ms", label, result, elapsed);
        return result;
    }

    /**
     * 动态设置页面分割模式
     *
     * @param psm 模式值：
     *            6 - 单行统一文本块
     *            7 - 单行文本（默认）
     *            8 - 单个词
     *            10 - 单个字符
     *            13 - 原始行，按行处理
     */
    public void setPageSegMode(int psm) {
        tesseract.setPageSegMode(psm);
    }

    /**
     * 动态设置字符白名单
     */
    @SuppressWarnings("deprecation")
    public void setWhitelist(String whitelist) {
        tesseract.setTessVariable("tessedit_char_whitelist", whitelist);
    }

    @PreDestroy
    public void destroy() {
        tesseract = null;
        log.info("OCR 引擎已释放");
    }
}
