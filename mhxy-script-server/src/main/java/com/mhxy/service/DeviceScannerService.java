package com.mhxy.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class DeviceScannerService {

    // Known emulator ADB ports
    private static final Map<String, int[]> EMULATOR_PORTS = new LinkedHashMap<>() {{
        put("夜神模拟器", new int[]{62001, 62025, 62026});
        put("雷电模拟器", new int[]{5555, 5554});
        put("逍遥模拟器", new int[]{21503});
        put("蓝叠模拟器", new int[]{5555});
        put("MuMu模拟器", new int[]{7555, 16384});
        put("腾讯手游助手", new int[]{5555});
    }};

    /**
     * Scan for available devices (emulators + ADB)
     */
    public List<Map<String, Object>> scanDevices() {
        List<Map<String, Object>> devices = new ArrayList<>();
        devices.addAll(scanEmulators());
        devices.addAll(scanAdbDevices());
        return devices;
    }

    /**
     * Scan known emulators by trying to connect to their ADB ports
     */
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
                    break; // Found this emulator, skip other ports
                }
            }
        }
        return devices;
    }

    /**
     * Scan ADB-connected Android devices
     */
    private List<Map<String, Object>> scanAdbDevices() {
        List<Map<String, Object>> devices = new ArrayList<>();
        try {
            Process process = new ProcessBuilder("adb", "devices", "-l")
                    .redirectErrorStream(true)
                    .start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("List of devices")) continue;
                // Format: serial    device usb:xxx product:xxx model:xxx device:xxx
                if (line.contains("\tdevice")) {
                    String serial = line.split("\t")[0];
                    // Skip emulators we already detected
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
                        String[] parts = resolution.split("x");
                        if (parts.length == 2) {
                            device.put("screenWidth", Integer.parseInt(parts[0].trim()));
                            device.put("screenHeight", Integer.parseInt(parts[1].trim()));
                        }
                    }
                    devices.add(device);
                }
            }
            process.waitFor(5, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.warn("ADB scan failed: {}", e.getMessage());
        }
        return devices;
    }

    /**
     * Get device resolution via ADB
     */
    private String getAdbResolution(String serial) {
        try {
            Process process = new ProcessBuilder("adb", "-s", serial, "shell", "wm", "size")
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

    private String extractAdbProperty(String line, String prefix) {
        int idx = line.indexOf(prefix);
        if (idx < 0) return "";
        String sub = line.substring(idx + prefix.length());
        int spaceIdx = sub.indexOf(' ');
        return spaceIdx > 0 ? sub.substring(0, spaceIdx) : sub;
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
