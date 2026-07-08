package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 设备控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/device")
public class DeviceController {

    private final Map<Long, Map<String, Object>> deviceStore = new ConcurrentHashMap<>();
    private final AtomicLong idGenerator = new AtomicLong(1);

    public DeviceController() {
        // 初始化示例设备
        addSampleDevice("夜神模拟器", "windows", "127.0.0.1", 62001, 1280, 720);
        addSampleDevice("雷电模拟器", "windows", "127.0.0.1", 5555, 1920, 1080);
        addSampleDevice("小米手机", "android", "192.168.1.100", 5555, 1080, 2400);
    }

    private void addSampleDevice(String name, String type, String ip, int port, int width, int height) {
        Map<String, Object> device = new HashMap<>();
        device.put("id", idGenerator.getAndIncrement());
        device.put("deviceName", name);
        device.put("deviceType", type);
        device.put("ipAddress", ip);
        device.put("port", port);
        device.put("screenWidth", width);
        device.put("screenHeight", height);
        device.put("status", 1);
        device.put("screenshot", null);
        deviceStore.put((Long) device.get("id"), device);
    }

    /**
     * 获取设备列表
     */
    @GetMapping("/list")
    public ApiResponse<List<Map<String, Object>>> getDeviceList() {
        return ApiResponse.success(new ArrayList<>(deviceStore.values()));
    }

    /**
     * 获取设备详情
     */
    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getDevice(@PathVariable Long id) {
        Map<String, Object> device = deviceStore.get(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        return ApiResponse.success(device);
    }

    /**
     * 添加设备
     */
    @PostMapping
    public ApiResponse<Map<String, Object>> addDevice(@RequestBody Map<String, Object> device) {
        long id = idGenerator.getAndIncrement();
        device.put("id", id);
        device.put("status", 0);
        device.put("screenshot", null);
        deviceStore.put(id, device);
        log.info("添加设备: {}", device.get("deviceName"));
        return ApiResponse.success("添加成功", device);
    }

    /**
     * 更新设备
     */
    @PutMapping("/{id}")
    public ApiResponse<Void> updateDevice(@PathVariable Long id, @RequestBody Map<String, Object> device) {
        if (!deviceStore.containsKey(id)) {
            return ApiResponse.fail("设备不存在");
        }
        device.put("id", id);
        deviceStore.put(id, device);
        return ApiResponse.success("更新成功", null);
    }

    /**
     * 删除设备
     */
    @DeleteMapping("/{id}")
    public ApiResponse<Void> deleteDevice(@PathVariable Long id) {
        deviceStore.remove(id);
        return ApiResponse.success("删除成功", null);
    }

    /**
     * 连接设备
     */
    @PostMapping("/{id}/connect")
    public ApiResponse<Void> connectDevice(@PathVariable Long id) {
        Map<String, Object> device = deviceStore.get(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        device.put("status", 2); // 使用中
        log.info("连接设备: {}", device.get("deviceName"));
        return ApiResponse.success("连接成功", null);
    }

    /**
     * 断开设备
     */
    @PostMapping("/{id}/disconnect")
    public ApiResponse<Void> disconnectDevice(@PathVariable Long id) {
        Map<String, Object> device = deviceStore.get(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        device.put("status", 1); // 在线
        log.info("断开设备: {}", device.get("deviceName"));
        return ApiResponse.success("断开成功", null);
    }

    /**
     * 刷新设备
     */
    @PostMapping("/refresh")
    public ApiResponse<List<Map<String, Object>>> refreshDevices() {
        // 实际应该扫描可用设备
        log.info("刷新设备列表");
        return ApiResponse.success(new ArrayList<>(deviceStore.values()));
    }
}
