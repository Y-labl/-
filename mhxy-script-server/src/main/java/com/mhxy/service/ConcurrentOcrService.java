package com.mhxy.service;

import com.mhxy.util.ImagePreprocessUtil;
import com.mhxy.util.OcrUtil;
import com.mhxy.util.ScreenCaptureUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.awt.image.BufferedImage;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Function;

/**
 * 并发 OCR 识别服务 —— 游戏多区域数字/文字并发识别
 * <p>
 * 设计要点：
 * <ul>
 *   <li>固定线程池：线程数 = CPU 核心数（游戏区域通常 3-8 个，4 核即可）</li>
 *   <li>截图 → 预处理 → OCR 三步流水线，每步可并行</li>
 *   <li>超时保护：单个区域识别超时 500ms 自动放弃</li>
 *   <li>预定义区域配置：血量、蓝条、金币等常用游戏区域</li>
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ConcurrentOcrService {

    private final ScreenCaptureUtil screenCapture;
    private final ImagePreprocessUtil preprocess;
    private final OcrUtil ocr;

    /** OCR 线程池，线程数 = CPU 核心数 */
    private final ExecutorService ocrExecutor = Executors.newFixedThreadPool(
            Runtime.getRuntime().availableProcessors(),
            r -> {
                Thread t = new Thread(r, "ocr-worker");
                t.setDaemon(true);
                return t;
            });

    /** 单区域 OCR 超时毫秒 */
    private static final long OCR_TIMEOUT_MS = 500;

    // ==================== 预定义游戏区域 ====================

    /**
     * 游戏数字区域定义
     */
    public record GameRegion(String name, int x, int y, int width, int height) {}

    /** 常见游戏区域预设（需根据实际游戏画面调整坐标） */
    public static final List<GameRegion> DEFAULT_REGIONS = List.of(
            new GameRegion("血量",    100, 50,  60, 20),
            new GameRegion("蓝量",    100, 75,  60, 20),
            new GameRegion("金币",    200, 30,  80, 22),
            new GameRegion("等级",    50,  10,  40, 18),
            new GameRegion("经验值",  150, 50,  70, 18)
    );

    // ==================== 核心 API ====================

    /**
     * 并发识别多个 ROI 区域的数字（一步完成：截图 + 预处理 + OCR）
     *
     * @param regions 要识别的区域列表
     * @return 区域名 → 识别结果 的映射（保持插入顺序）
     */
    public Map<String, String> recognizeMultipleRegions(List<GameRegion> regions) {
        return recognizeMultipleRegions(regions, 0.7);
    }

    /**
     * 并发识别多个 ROI 区域的数字
     *
     * @param regions 区域列表
     * @param scale   预处理缩放比例（0.5-1.0）
     * @return 区域名 → 识别结果
     */
    public Map<String, String> recognizeMultipleRegions(List<GameRegion> regions, double scale) {
        if (regions == null || regions.isEmpty()) {
            return Collections.emptyMap();
        }

        long startTotal = System.nanoTime();
        int n = regions.size();

        // 1. 并发截图所有区域
        List<CompletableFuture<BufferedImage>> captureFutures = new ArrayList<>(n);
        for (GameRegion region : regions) {
            CompletableFuture<BufferedImage> future = CompletableFuture.supplyAsync(
                    () -> screenCapture.captureRegion(region.x, region.y, region.width, region.height),
                    ocrExecutor);
            captureFutures.add(future);
        }

        // 2. 等待所有截图完成
        CompletableFuture.allOf(captureFutures.toArray(new CompletableFuture[0])).join();

        // 3. 并发预处理 + OCR
        List<CompletableFuture<Map.Entry<String, String>>> ocrFutures = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            final int idx = i;
            final GameRegion region = regions.get(i);
            final BufferedImage rawImage = captureFutures.get(i).join();

            CompletableFuture<Map.Entry<String, String>> ocrFuture = CompletableFuture.supplyAsync(() -> {
                long start = System.nanoTime();
                try {
                    BufferedImage processed = preprocess.matToBufferedImage(
                            preprocess.preprocessForOCR(rawImage, scale));
                    String text = ocr.recognizeDigits(processed);
                    long elapsed = (System.nanoTime() - start) / 1_000_000;
                    log.debug("[{}] 截图+预处理+OCR: {}ms → {}", region.name, elapsed, text);
                    return new AbstractMap.SimpleEntry<>(region.name, text);
                } catch (Exception e) {
                    log.warn("[{}] OCR 异常: {}", region.name, e.getMessage());
                    return new AbstractMap.SimpleEntry<>(region.name, "ERR");
                }
            }, ocrExecutor);

            ocrFutures.add(ocrFuture);
        }

        // 4. 收集结果（带超时保护）
        Map<String, String> results = new LinkedHashMap<>();
        for (int i = 0; i < n; i++) {
            try {
                Map.Entry<String, String> entry = ocrFutures.get(i).get(OCR_TIMEOUT_MS, TimeUnit.MILLISECONDS);
                results.put(entry.getKey(), entry.getValue());
            } catch (TimeoutException e) {
                results.put(regions.get(i).name, "TIMEOUT");
                log.warn("[{}] OCR 超时", regions.get(i).name);
            } catch (Exception e) {
                results.put(regions.get(i).name, "ERR");
                log.error("[{}] OCR 失败: {}", regions.get(i).name, e.getMessage());
            }
        }

        long totalElapsed = (System.nanoTime() - startTotal) / 1_000_000;
        log.info("并发OCR完成: {}个区域, 总耗时{}ms, 结果: {}", n, totalElapsed, results);

        return results;
    }

    /**
     * 单区域快速数字识别（含计时）
     *
     * @param x, y, width, height ROI 坐标
     * @return 识别出的数字字符串
     */
    public String recognizeSingleRegion(int x, int y, int width, int height) {
        long start = System.nanoTime();
        BufferedImage raw = screenCapture.captureRegion(x, y, width, height);
        BufferedImage processed = preprocess.matToBufferedImage(
                preprocess.preprocessForOCR(raw, 0.7));
        String result = ocr.recognizeDigits(processed);
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        log.info("单区域OCR: ({},{},{},{}) → {} | 耗时{}ms", x, y, width, height, result, elapsed);
        return result;
    }

    /**
     * 使用预设区域并发识别
     */
    public Map<String, String> recognizeDefaultRegions() {
        return recognizeMultipleRegions(DEFAULT_REGIONS);
    }

    /**
     * 连续监控：每隔 intervalMs 毫秒识别一次，通过回调输出结果
     *
     * @param regions    监控区域
     * @param intervalMs 间隔毫秒
     * @param callback   结果回调
     * @return 可用于取消的 Future
     */
    public ScheduledFuture<?> startMonitor(
            List<GameRegion> regions,
            long intervalMs,
            Function<Map<String, String>, Boolean> callback) {

        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "ocr-monitor");
            t.setDaemon(true);
            return t;
        });

        return scheduler.scheduleWithFixedDelay(() -> {
            try {
                Map<String, String> results = recognizeMultipleRegions(regions);
                boolean shouldContinue = callback.apply(results);
                if (!shouldContinue) {
                    scheduler.shutdown();
                }
            } catch (Exception e) {
                log.error("监控识别异常: {}", e.getMessage());
            }
        }, 0, intervalMs, TimeUnit.MILLISECONDS);
    }
}
