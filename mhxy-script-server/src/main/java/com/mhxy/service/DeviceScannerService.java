package com.mhxy.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class DeviceScannerService {

    @Autowired(required = false)
    private SystemConfigService systemConfigService;

    /* ---- 实时预览：后台持续截图缓存 ---- */
    private final Map<String, byte[]> frameCache = new ConcurrentHashMap<>();
    private final Map<String, Boolean> streaming = new ConcurrentHashMap<>();
    private final Map<String, Long> lastAccess = new ConcurrentHashMap<>();
    private static final int STREAM_TIMEOUT_MS = 5000;

    private String resolveAdbPath() {
        if (systemConfigService != null) {
            String configured = systemConfigService.getConfigValue("adb.path");
            if (configured != null && !configured.isEmpty() && Files.exists(Path.of(configured))) {
                log.debug("ADB path from config: {}", configured);
                return configured;
            }
        }

        List<String> wellKnown = List.of(
            Paths.get(System.getProperty("user.home"), "AppData", "Local", "Android", "Sdk", "platform-tools", "adb.exe").toString(),
            "C:\\adb\\adb.exe",
            "D:\\adb\\adb.exe"
        );
        for (String p : wellKnown) {
            if (Files.exists(Path.of(p))) {
                log.debug("ADB found at: {}", p);
                return p;
            }
        }

        try {
            String userHome = System.getProperty("user.home");
            Path base = Paths.get(userHome, "AppData", "Local", "Programs", "Python");
            if (Files.exists(base)) {
                try (var stream = Files.walk(base, 4)) {
                    Optional<Path> found = stream
                        .filter(Files::isRegularFile)
                        .filter(f -> f.getFileName().toString().equalsIgnoreCase("adb.exe"))
                        .filter(f -> f.getParent().getFileName().toString().equals("binaries"))
                        .findFirst();
                    if (found.isPresent()) {
                        log.debug("ADB found via Python adbutils: {}", found.get());
                        return found.get().toString();
                    }
                }
            }
        } catch (Exception ignored) {
        }

        return "C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python38\\lib\\site-packages\\adbutils\\binaries\\adb.exe";
    }

    // 已知模拟器 ADB 端口
    private static final Map<String, int[]> EMULATOR_PORTS = new LinkedHashMap<>() {{
        put("夜神模拟器", new int[]{62001, 62025, 62026});
        put("雷电模拟器", new int[]{5555, 5554});
        put("逍遥模拟器", new int[]{21503});
        put("蓝叠模拟器", new int[]{5555});
        put("MuMu模拟器", new int[]{7555, 16384});
        put("腾讯手游助手", new int[]{5555});
    }};

    public List<Map<String, Object>> scanDevices() {
        List<Map<String, Object>> devices = new ArrayList<>();
        devices.addAll(scanEmulators());
        devices.addAll(scanAdbDevices());
        return devices;
    }

    private List<Map<String, Object>> scanEmulators() {
        List<Map<String, Object>> devices = new ArrayList<>();

        for (Map.Entry<String, int[]> entry : EMULATOR_PORTS.entrySet()) {
            String name = entry.getKey();
            for (int port : entry.getValue()) {
                if (isPortOpen("127.0.0.1", port)) {
                    String serial = "127.0.0.1:" + port;
                    String resolution = getAdbResolution(serial);

                    Map<String, Object> device = new LinkedHashMap<>();
                    device.put("deviceName", name);
                    device.put("deviceType", "windows");
                    device.put("ipAddress", "127.0.0.1");
                    device.put("port", port);
                    device.put("serial", serial);
                    device.put("status", 1);
                    device.put("source", "emulator");
                    if (!resolution.isEmpty()) {
                        String[] parts = resolution.split("x");
                        if (parts.length == 2) {
                            device.put("screenWidth", Integer.parseInt(parts[0].trim()));
                            device.put("screenHeight", Integer.parseInt(parts[1].trim()));
                        }
                    }
                    devices.add(device);
                    break;
                }
            }
        }
        return devices;
    }

    private List<Map<String, Object>> scanAdbDevices() {
        List<Map<String, Object>> devices = new ArrayList<>();
        String adbPath = resolveAdbPath();
        log.info("Using ADB: {}", adbPath);
        try {
            Process process = new ProcessBuilder(adbPath, "devices", "-l")
                    .redirectErrorStream(true)
                    .start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("List of devices") || line.startsWith("*")) continue;

                // ADB 输出用空格分隔，不是 tab
                String[] parts = line.split("\\s+");
                if (parts.length < 2) continue;
                String serial = parts[0];
                String status = parts[1];

                if (!"device".equals(status)) continue;
                if (serial.startsWith("emulator-") || serial.contains("127.0.0.1")) continue;

                String model = extractAdbProperty(line, "model:");
                String deviceName = !model.isEmpty() ? model : serial;
                String resolution = getAdbResolution(serial);

                Map<String, Object> device = new LinkedHashMap<>();
                device.put("deviceName", deviceName);
                device.put("deviceType", "android");
                device.put("ipAddress", serial);
                device.put("port", 5555);
                device.put("serial", serial);
                device.put("status", 1);
                device.put("source", "adb");

                if (!resolution.isEmpty()) {
                    String[] wh = resolution.split("x");
                    if (wh.length == 2) {
                        device.put("screenWidth", Integer.parseInt(wh[0].trim()));
                        device.put("screenHeight", Integer.parseInt(wh[1].trim()));
                    }
                }
                devices.add(device);
            }
            process.waitFor(5, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.warn("ADB scan failed: {}", e.getMessage());
        }
        return devices;
    }

    private String getAdbResolution(String serial) {
        try {
            Process process = new ProcessBuilder(resolveAdbPath(), "-s", serial, "shell", "wm", "size")
                    .redirectErrorStream(true)
                    .start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String output = reader.readLine();
            process.waitFor(3, TimeUnit.SECONDS);
            if (output != null) {
                if (output.contains("Override size:")) {
                    return output.split("Override size:")[1].trim();
                } else if (output.contains("Physical size:")) {
                    return output.split("Physical size:")[1].trim();
                }
            }
        } catch (Exception e) {
            log.debug("Failed to get resolution for {}: {}", serial, e.getMessage());
        }
        return "";
    }

    public byte[] captureAdbScreenshot(String serial) {
        String adbPath = resolveAdbPath();
        try {
            Process process = new ProcessBuilder(adbPath, "-s", serial, "exec-out", "screencap", "-p")
                    .redirectErrorStream(false)
                    .start();
            InputStream in = process.getInputStream();
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            byte[] chunk = new byte[8192];
            int n;
            while ((n = in.read(chunk)) != -1) {
                buffer.write(chunk, 0, n);
            }
            process.waitFor(5, TimeUnit.SECONDS);
            byte[] result = buffer.toByteArray();
            if (result.length > 0) {
                return result;
            }
        } catch (Exception e) {
            log.warn("Screenshot failed for {}: {}", serial, e.getMessage());
        }
        return null;
    }

    /**
     * 截图并转 JPEG + 降分辨率，大幅减小体积以支持流式预览。
     *
     * @param serial   设备序列号
     * @param maxWidth 限制最大宽度（≤0 表示不缩放）
     * @param quality  JPEG 质量 0.0~1.0
     */
    public byte[] captureAdbScreenshotJpeg(String serial, int maxWidth, float quality) {
        byte[] pngBytes = captureAdbScreenshot(serial);
        if (pngBytes == null || pngBytes.length == 0) return null;
        try {
            BufferedImage img = ImageIO.read(new ByteArrayInputStream(pngBytes));
            if (img == null) return null;

            if (maxWidth > 0 && img.getWidth() > maxWidth) {
                int newHeight = (int) ((double) img.getHeight() * maxWidth / img.getWidth());
                BufferedImage scaled = new BufferedImage(maxWidth, newHeight, BufferedImage.TYPE_INT_RGB);
                Graphics2D g = scaled.createGraphics();
                g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
                g.drawImage(img, 0, 0, maxWidth, newHeight, null);
                g.dispose();
                img = scaled;
            } else if (img.getType() != BufferedImage.TYPE_INT_RGB) {
                // JPEG 不支持 alpha，统一转 RGB
                BufferedImage rgb = new BufferedImage(img.getWidth(), img.getHeight(), BufferedImage.TYPE_INT_RGB);
                Graphics2D g = rgb.createGraphics();
                g.drawImage(img, 0, 0, null);
                g.dispose();
                img = rgb;
            }

            ByteArrayOutputStream jpegOut = new ByteArrayOutputStream();
            ImageWriter writer = ImageIO.getImageWritersByFormatName("jpeg").next();
            ImageWriteParam param = writer.getDefaultWriteParam();
            param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
            param.setCompressionQuality(quality);
            ImageOutputStream ios = ImageIO.createImageOutputStream(jpegOut);
            writer.setOutput(ios);
            writer.write(null, new IIOImage(img, null, null), param);
            writer.dispose();
            ios.close();
            return jpegOut.toByteArray();
        } catch (Exception e) {
            log.warn("Screenshot JPEG failed for {}: {}", serial, e.getMessage());
        }
        return null;
    }

    /**
     * 确保后台截图线程在运行。前端每次请求 stream 时调用，
     * 截图由后台线程持续完成并缓存，前端请求几乎零延迟返回最新帧。
     */
    public void ensureStreaming(String serial, int width, float quality) {
        lastAccess.put(serial, System.currentTimeMillis());
        if (Boolean.TRUE.equals(streaming.get(serial))) return;
        streaming.put(serial, true);
        Thread t = new Thread(() -> {
            log.info("Stream started for {}", serial);
            while (Boolean.TRUE.equals(streaming.get(serial))) {
                if (System.currentTimeMillis() - lastAccess.getOrDefault(serial, 0L) > STREAM_TIMEOUT_MS) {
                    streaming.put(serial, false);
                    frameCache.remove(serial);
                    lastAccess.remove(serial);
                    log.info("Stream timeout, stopped for {}", serial);
                    break;
                }
                try {
                    byte[] jpeg = captureAdbScreenshotJpeg(serial, width, quality);
                    if (jpeg != null && jpeg.length > 0) {
                        frameCache.put(serial, jpeg);
                    }
                } catch (Exception e) {
                    log.warn("Stream capture error for {}: {}", serial, e.getMessage());
                }
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }
        }, "adb-stream-" + serial);
        t.setDaemon(true);
        t.start();
    }

    /**
     * 获取缓存的最新一帧 JPEG（同时刷新访问时间）。
     */
    public byte[] getLatestFrame(String serial) {
        lastAccess.put(serial, System.currentTimeMillis());
        return frameCache.get(serial);
    }

    private String extractAdbProperty(String line, String prefix) {
        int idx = line.indexOf(prefix);
        if (idx < 0) return "";
        String sub = line.substring(idx + prefix.length());
        int spaceIdx = sub.indexOf(' ');
        return spaceIdx > 0 ? sub.substring(0, spaceIdx) : sub;
    }


    /**
     * ADB tap at screen coordinates.
     */
    public void adbTap(String serial, int x, int y) {
        String adbPath = resolveAdbPath();
        try {
            new ProcessBuilder(adbPath, "-s", serial, "shell", "input", "tap", String.valueOf(x), String.valueOf(y))
                .redirectErrorStream(true).start().waitFor(2, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.warn("ADB tap failed: {}", e.getMessage());
        }
    }

    /**
     * ADB swipe between two points.
     */
    public void adbSwipe(String serial, int x1, int y1, int x2, int y2, int durationMs) {
        String adbPath = resolveAdbPath();
        try {
            new ProcessBuilder(adbPath, "-s", serial, "shell", "input", "swipe",
                String.valueOf(x1), String.valueOf(y1), String.valueOf(x2), String.valueOf(y2),
                String.valueOf(durationMs))
                .redirectErrorStream(true).start().waitFor(2, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.warn("ADB swipe failed: {}", e.getMessage());
        }
    }

    private boolean isPortOpen(String host, int port) {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 500);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
