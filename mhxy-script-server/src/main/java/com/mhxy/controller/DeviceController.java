package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.Device;
import com.mhxy.service.DeviceScannerService;
import com.mhxy.service.DeviceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/device")
public class DeviceController {

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private DeviceScannerService scannerService;

    /**
     * 获取设备列表
     */
    @GetMapping("/list")
    public ApiResponse<List<Map<String, Object>>> getDeviceList() {
        List<Device> devices = deviceService.list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Device d : devices) {
            result.add(deviceToMap(d));
        }
        return ApiResponse.success(result);
    }

    /**
     * 扫描可用设备（模拟器端口检测 + ADB扫描）
     */
    @GetMapping("/scan")
    public ApiResponse<List<Map<String, Object>>> scanDevices() {
        log.info("扫描可用设备...");
        List<Map<String, Object>> scanned = scannerService.scanDevices();

        // 标记已绑定的设备
        List<Device> boundDevices = deviceService.list();
        Set<String> boundSerials = new HashSet<>();
        for (Device d : boundDevices) {
            if (d.getDeviceId() != null) boundSerials.add(d.getDeviceId());
        }

        for (Map<String, Object> device : scanned) {
            String serial = (String) device.getOrDefault("serial", "");
            device.put("bound", boundSerials.contains(serial));
        }

        log.info("扫描完成, 发现 {} 台设备", scanned.size());
        return ApiResponse.success(scanned);
    }

    /**
     * 绑定设备（将扫描到的设备保存到数据库）
     */
    @PostMapping("/bind")
    public ApiResponse<Map<String, Object>> bindDevice(@RequestBody Map<String, Object> body) {
        String deviceName = (String) body.get("deviceName");
        String deviceType = (String) body.getOrDefault("deviceType", "windows");
        String ipAddress = (String) body.get("ipAddress");
        Integer port = body.get("port") != null ? ((Number) body.get("port")).intValue() : 5555;
        String serial = (String) body.get("serial");

        // Check if already bound
        if (serial != null && !serial.isEmpty()) {
            Device existing = deviceService.lambdaQuery().eq(Device::getDeviceId, serial).one();
            if (existing != null) {
                return ApiResponse.fail("该设备已绑定");
            }
        }

        Device device = new Device();
        device.setDeviceName(deviceName);
        device.setDeviceType(deviceType);
        device.setIpAddress(ipAddress);
        device.setPort(port);
        device.setDeviceId(serial);
        device.setStatus(1);
        if (body.containsKey("screenWidth")) {
            device.setScreenWidth(((Number) body.get("screenWidth")).intValue());
        }
        if (body.containsKey("screenHeight")) {
            device.setScreenHeight(((Number) body.get("screenHeight")).intValue());
        }

        deviceService.save(device);
        log.info("绑定设备: {} ({})", deviceName, serial);
        return ApiResponse.success("绑定成功", deviceToMap(device));
    }

    /**
     * 获取设备详情
     */
    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        return ApiResponse.success(deviceToMap(device));
    }

    /**
     * 添加设备
     */
    @PostMapping
    public ApiResponse<Map<String, Object>> addDevice(@RequestBody Map<String, Object> body) {
        Device device = new Device();
        device.setDeviceName((String) body.get("deviceName"));
        device.setDeviceType((String) body.getOrDefault("deviceType", "android"));
        device.setIpAddress((String) body.get("ipAddress"));
        device.setPort(body.get("port") != null ? ((Number) body.get("port")).intValue() : 5555);
        device.setScreenWidth(body.get("screenWidth") != null ? ((Number) body.get("screenWidth")).intValue() : null);
        device.setScreenHeight(body.get("screenHeight") != null ? ((Number) body.get("screenHeight")).intValue() : null);
        device.setStatus(0);
        device.setRemark((String) body.get("remark"));

        deviceService.save(device);
        log.info("添加设备: {}", device.getDeviceName());
        return ApiResponse.success("添加成功", deviceToMap(device));
    }

    /**
     * 更新设备
     */
    @PutMapping("/{id}")
    public ApiResponse<Void> updateDevice(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        if (body.containsKey("deviceName")) device.setDeviceName((String) body.get("deviceName"));
        if (body.containsKey("deviceType")) device.setDeviceType((String) body.get("deviceType"));
        if (body.containsKey("ipAddress")) device.setIpAddress((String) body.get("ipAddress"));
        if (body.containsKey("port")) device.setPort(((Number) body.get("port")).intValue());
        if (body.containsKey("screenWidth")) device.setScreenWidth(((Number) body.get("screenWidth")).intValue());
        if (body.containsKey("screenHeight")) device.setScreenHeight(((Number) body.get("screenHeight")).intValue());
        if (body.containsKey("remark")) device.setRemark((String) body.get("remark"));

        deviceService.updateById(device);
        return ApiResponse.success("更新成功", null);
    }

    /**
     * 删除设备
     */
    @DeleteMapping("/{id}")
    public ApiResponse<Void> deleteDevice(@PathVariable Long id) {
        deviceService.removeById(id);
        return ApiResponse.success("删除成功", null);
    }

    /**
     * 连接设备
     */
    @PostMapping("/{id}/connect")
    public ApiResponse<Void> connectDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        deviceService.connectDevice(id);
        log.info("连接设备: {}", device.getDeviceName());
        return ApiResponse.success("连接成功", null);
    }

    /**
     * 断开设备
     */
    @PostMapping("/{id}/disconnect")
    public ApiResponse<Void> disconnectDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("设备不存在");
        }
        deviceService.disconnectDevice(id);
        log.info("断开设备: {}", device.getDeviceName());
        return ApiResponse.success("断开成功", null);
    }

    /**
     * 刷新设备列表
     */
    @PostMapping("/refresh")
    public ApiResponse<List<Map<String, Object>>> refreshDevices() {
        List<Device> devices = deviceService.list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Device d : devices) {
            result.add(deviceToMap(d));
        }
        log.info("刷新设备列表, 共{}台", devices.size());
        return ApiResponse.success(result);
    }

    private Map<String, Object> deviceToMap(Device d) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", d.getId());
        map.put("deviceName", d.getDeviceName());
        map.put("deviceType", d.getDeviceType());
        map.put("ipAddress", d.getIpAddress());
        map.put("port", d.getPort());
        map.put("screenWidth", d.getScreenWidth());
        map.put("screenHeight", d.getScreenHeight());
        map.put("status", d.getStatus());
        map.put("deviceId", d.getDeviceId());
        map.put("screenshot", null);
        return map;
    }
}
