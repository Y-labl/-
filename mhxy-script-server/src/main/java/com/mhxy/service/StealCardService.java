package com.mhxy.service;

import com.mhxy.entity.Device;
import com.mhxy.entity.StealCardConfig;
import com.mhxy.entity.TemplateImage;
import com.mhxy.mapper.TemplateImageMapper;
import com.mhxy.util.ImageMatchUtil;
import lombok.extern.slf4j.Slf4j;
import org.opencv.core.Point;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.awt.image.BufferedImage;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Steal card automation service.
 * 每个设备独立运行、独立启停。
 */
@Slf4j
@Service
public class StealCardService {

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private DeviceScannerService scannerService;

    @Autowired
    private OcrRecognitionService ocrService;

    @Autowired
    private StealCardConfigService configService;

    @Autowired
    private TemplateImageMapper templateMapper;

    @Autowired
    private ImageMatchUtil imageMatch;

    /** 每个设备一个运行状态标记 */
    private final Map<Long, Boolean> runningMap = new ConcurrentHashMap<>();

    private static final List<String> DEFAULT_TARGET_MONSTERS = Arrays.asList(
        "噬天虎", "炎魔神", "金身僧"
    );

    /** 按 deviceId 启动偷卡任务（独立运行） */
    public synchronized boolean start(Long deviceId) {
        if (Boolean.TRUE.equals(runningMap.get(deviceId))) {
            log.warn("StealCard already running for device {}", deviceId);
            return false;
        }
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) {
            log.warn("Device not found or no serial: {}", deviceId);
            return false;
        }
        runningMap.put(deviceId, true);

        StealCardConfig cfg = configService.getByDeviceId(deviceId);
        String serial = device.getDeviceId();
        log.info("Starting steal card on device {} ({})", deviceId, serial);

        Thread t = new Thread(() -> {
            try {
                runStealLoop(serial, deviceId, cfg);
            } catch (Exception e) {
                log.error("Steal card error on device {}: {}", deviceId, e.getMessage());
            } finally {
                runningMap.put(deviceId, false);
                log.info("Steal card stopped for device {}", deviceId);
            }
        }, "steal-card-" + serial);
        t.setDaemon(true);
        t.start();
        return true;
    }

    /** 按 deviceId 停止偷卡任务 */
    public synchronized void stop(Long deviceId) {
        runningMap.put(deviceId, false);
        log.info("Stop signal sent to steal card on device {}", deviceId);
    }

    /** 停止所有正在运行的偷卡任务 */
    public void stopAll() {
        for (Long id : new ArrayList<>(runningMap.keySet())) {
            runningMap.put(id, false);
        }
    }

    public boolean isRunning(Long deviceId) {
        return Boolean.TRUE.equals(runningMap.get(deviceId));
    }

    public List<Long> getRunningDeviceIds() {
        List<Long> ids = new ArrayList<>();
        for (Map.Entry<Long, Boolean> e : runningMap.entrySet()) {
            if (Boolean.TRUE.equals(e.getValue())) ids.add(e.getKey());
        }
        return ids;
    }

    /* ---- 兼容旧 API（场景级别，整体启停） ---- */
    @Deprecated
    public void start(Long deviceId, com.mhxy.entity.BattleScene scene) {
        start(deviceId);
    }
    @Deprecated
    public void stop() { stopAll(); }
    @Deprecated
    public boolean isRunning() {
        return !runningMap.isEmpty() && runningMap.values().stream().anyMatch(Boolean::booleanValue);
    }

    /* ---- 主循环 ---- */
    private void runStealLoop(String serial, Long deviceId, StealCardConfig cfg) {
        List<String> monsters = parseMonsters(cfg);
        int[][] area = parseArea(cfg);
        int walkInterval = cfg != null && cfg.getWalkInterval() != null ? cfg.getWalkInterval() : 500;
        int stealAttempts = cfg != null && cfg.getStealAttempts() != null ? cfg.getStealAttempts() : 3;

        while (Boolean.TRUE.equals(runningMap.get(deviceId))) {
            try {
                Optional<String> location = ocrService.recognizeLocation(deviceId);
                if (location.isEmpty() || !location.get().contains("小西天")) {
                    log.debug("Not on Xixitian map, navigating...");
                    navigateToXixitian(serial);
                    sleep(2000);
                    continue;
                }
                randomWalk(serial, area);
                sleep(walkInterval);

                boolean inBattle = detectBattle(serial);
                if (inBattle) {
                    log.info("Battle detected on device {}, starting steal routine", deviceId);
                    executeBattleSteal(serial, deviceId, monsters, stealAttempts);
                    sleep(3000);
                }
                sleep(200);
            } catch (Exception e) {
                log.warn("Loop iteration error on device {}: {}", deviceId, e.getMessage());
                sleep(1000);
            }
        }
    }

    private List<String> parseMonsters(StealCardConfig cfg) {
        if (cfg != null && cfg.getTargetMonsters() != null && !cfg.getTargetMonsters().isEmpty()) {
            String[] arr = cfg.getTargetMonsters().split(",");
            List<String> list = new ArrayList<>();
            for (String s : arr) {
                String t = s.trim();
                if (!t.isEmpty()) list.add(t);
            }
            if (!list.isEmpty()) {
                log.info("StealCard using monsters: {}", list);
                return list;
            }
        }
        return new ArrayList<>(DEFAULT_TARGET_MONSTERS);
    }

    private int[][] parseArea(StealCardConfig cfg) {
        int[][] def = {{80, 180}, {980, 2200}};
        if (cfg != null && cfg.getMapClickArea() != null && !cfg.getMapClickArea().isEmpty()) {
            try {
                String[] parts = cfg.getMapClickArea().split(",");
                if (parts.length == 4) {
                    int x1 = Integer.parseInt(parts[0].trim());
                    int y1 = Integer.parseInt(parts[1].trim());
                    int x2 = Integer.parseInt(parts[2].trim());
                    int y2 = Integer.parseInt(parts[3].trim());
                    return new int[][]{{x1, y1}, {x2, y2}};
                }
            } catch (Exception e) {
                log.warn("Invalid map_click_area: {}", cfg.getMapClickArea());
            }
        }
        return def;
    }

    private void navigateToXixitian(String serial) {
        clickTemplate(serial, "打开地图");
        sleep(800);
        clickTemplate(serial, "小西天地图");
        sleep(1500);
        clickTemplate(serial, "关闭地图");
        sleep(500);
    }

    private void randomWalk(String serial, int[][] area) {
        int x = area[0][0] + (int)(Math.random() * (area[1][0] - area[0][0]));
        int y = area[0][1] + (int)(Math.random() * (area[1][1] - area[0][1]));
        scannerService.adbTap(serial, x, y);
    }

    private boolean detectBattle(String serial) {
        byte[] screenshot = scannerService.captureAdbScreenshot(serial);
        if (screenshot == null) return false;
        BufferedImage screen = bytesToImage(screenshot);
        if (screen == null) return false;
        TemplateImage battleTemplate = findTemplate("战斗场景");
        if (battleTemplate != null) {
            Optional<Point> found = imageMatch.findTemplate(screen, battleTemplate.getTemplatePath());
            if (found.isPresent()) return true;
        }
        return false;
    }

    private void executeBattleSteal(String serial, Long deviceId, List<String> monsters, int attempts) {
        if (monsters == null || monsters.isEmpty()) monsters = DEFAULT_TARGET_MONSTERS;
        clickTemplate(serial, "战斗法术");
        sleep(500);

        for (int attempt = 0; attempt < attempts && isRunning(deviceId); attempt++) {
            for (String monster : monsters) {
                if (!isRunning(deviceId)) return;
                clickTemplate(serial, "妙手空空技能");
                sleep(400);
                boolean clicked = clickTemplate(serial, monster);
                if (clicked) {
                    log.info("Used steal on: {}", monster);
                    sleep(600);
                }
                clickTemplate(serial, "战斗防御");
                sleep(300);
            }
        }
        for (int i = 0; i < 5 && isRunning(deviceId); i++) {
            sleep(2000);
            if (!detectBattle(serial)) break;
        }
    }

    private boolean clickTemplate(String serial, String templateName) {
        byte[] screenshot = scannerService.captureAdbScreenshot(serial);
        if (screenshot == null) return false;
        BufferedImage screen = bytesToImage(screenshot);
        if (screen == null) return false;
        TemplateImage tpl = findTemplate(templateName);
        if (tpl == null) {
            log.debug("Template not found: {}", templateName);
            return false;
        }
        Optional<Point> found = imageMatch.findTemplate(screen, tpl.getTemplatePath());
        if (found.isEmpty()) return false;
        BufferedImage tplImg = loadTemplateImage(tpl);
        int tw = tplImg != null ? tplImg.getWidth() : 0;
        int th = tplImg != null ? tplImg.getHeight() : 0;
        int cx = (int) found.get().x + tw / 2;
        int cy = (int) found.get().y + th / 2;
        scannerService.adbTap(serial, cx, cy);
        log.debug("Clicked template '{}' at ({}, {})", templateName, cx, cy);
        return true;
    }

    private TemplateImage findTemplate(String name) {
        List<TemplateImage> list = templateMapper.selectList(
            new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TemplateImage>()
                .eq(TemplateImage::getTemplateName, name));
        return list.isEmpty() ? null : list.get(0);
    }

    private BufferedImage loadTemplateImage(TemplateImage tpl) {
        try {
            byte[] bytes = java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(tpl.getTemplatePath()));
            return bytesToImage(bytes);
        } catch (Exception e) {
            return null;
        }
    }

    private BufferedImage bytesToImage(byte[] bytes) {
        try {
            return javax.imageio.ImageIO.read(new java.io.ByteArrayInputStream(bytes));
        } catch (Exception e) {
            return null;
        }
    }

    private void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
