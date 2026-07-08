package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.Device;
import com.mhxy.service.DeviceScannerService;
import com.mhxy.service.DeviceService;
import com.mhxy.service.OcrRecognitionService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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

    @Autowired
    private OcrRecognitionService ocrRecognitionService;

    @GetMapping("/list")
    public ApiResponse<List<Map<String, Object>>> getDeviceList() {
        List<Device> devices = deviceService.list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Device d : devices) {
            result.add(deviceToMap(d));
        }
        return ApiResponse.success(result);
    }

    @GetMapping("/scan")
    public ApiResponse<List<Map<String, Object>>> scanDevices() {
        log.info("Scanning devices...");
        List<Map<String, Object>> scanned = scannerService.scanDevices();

        List<Device> boundDevices = deviceService.list();
        Set<String> boundSerials = new HashSet<>();
        for (Device d : boundDevices) {
            if (d.getDeviceId() != null) boundSerials.add(d.getDeviceId());
        }

        for (Map<String, Object> device : scanned) {
            String serial = (String) device.getOrDefault("serial", "");
            device.put("bound", boundSerials.contains(serial));
        }

        log.info("Scan done, found {} devices", scanned.size());
        return ApiResponse.success(scanned);
    }

    @GetMapping("/{id}/screenshot")
    public ApiResponse<Map<String, String>> getScreenshot(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("Device not found");
        }

        String serial = device.getDeviceId();
        if (serial == null || serial.isEmpty()) {
            return ApiResponse.fail("No device serial configured");
        }

        try {
            byte[] pngBytes = scannerService.captureAdbScreenshot(serial);
            if (pngBytes == null || pngBytes.length == 0) {
                return ApiResponse.fail("Screenshot capture failed");
            }
            String base64 = Base64.getEncoder().encodeToString(pngBytes);
            Map<String, String> data = new HashMap<>();
            data.put("base64", "data:image/png;base64," + base64);
            data.put("serial", serial);
            return ApiResponse.success(data);
        } catch (Exception e) {
            log.error("Screenshot error for {}: {}", serial, e.getMessage());
            return ApiResponse.fail(e.getMessage());
        }
    }

    /**
     * 流式预览端点：返回降分辨率 JPEG 二进制，体积小、传输快，适合实时预览。
     * 后台线程持续截图缓存，此端点几乎零延迟返回最新帧。
     */
    @GetMapping("/{id}/stream")
    public ResponseEntity<byte[]> streamScreenshot(@PathVariable Long id,
                                                  @RequestParam(defaultValue = "480") int width,
                                                  @RequestParam(defaultValue = "0.7") float quality) {
        Device device = deviceService.getById(id);
        if (device == null) return ResponseEntity.notFound().build();
        String serial = device.getDeviceId();
        if (serial == null || serial.isEmpty()) return ResponseEntity.notFound().build();
        try {
            scannerService.ensureStreaming(serial, width, quality);
            byte[] jpeg = scannerService.getLatestFrame(serial);
            if (jpeg == null || jpeg.length == 0) return ResponseEntity.noContent().build();
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.IMAGE_JPEG);
            headers.setCacheControl(CacheControl.noStore().getHeaderValue());
            return new ResponseEntity<>(jpeg, headers, org.springframework.http.HttpStatus.OK);
        } catch (Exception e) {
            log.error("Stream error for {}: {}", serial, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    @GetMapping("/{id}/recognize")
    public ApiResponse<Map<String, Object>> recognizeDevice(@PathVariable Long id) {
        Map<String, Object> result = ocrRecognitionService.recognizeFull(id);
        return ApiResponse.success(result);
    }

    @PostMapping("/bind")
    public ApiResponse<Map<String, Object>> bindDevice(@RequestBody Map<String, Object> body) {
        String deviceName = (String) body.get("deviceName");
        String deviceType = (String) body.getOrDefault("deviceType", "windows");
        String ipAddress = (String) body.get("ipAddress");
        Integer port = body.get("port") != null ? ((Number) body.get("port")).intValue() : 5555;
        String serial = (String) body.get("serial");

        if (serial != null && !serial.isEmpty()) {
            Device existing = deviceService.lambdaQuery().eq(Device::getDeviceId, serial).one();
            if (existing != null) {
                return ApiResponse.fail("Device already bound");
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
        log.info("Bound device: {} ({})", deviceName, serial);
        return ApiResponse.success("Bound", deviceToMap(device));
    }

    @GetMapping("/{id}")
    public ApiResponse<Map<String, Object>> getDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("Device not found");
        }
        return ApiResponse.success(deviceToMap(device));
    }

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
        log.info("Added device: {}", device.getDeviceName());
        return ApiResponse.success("Added", deviceToMap(device));
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> updateDevice(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("Device not found");
        }
        if (body.containsKey("deviceName")) device.setDeviceName((String) body.get("deviceName"));
        if (body.containsKey("deviceType")) device.setDeviceType((String) body.get("deviceType"));
        if (body.containsKey("ipAddress")) device.setIpAddress((String) body.get("ipAddress"));
        if (body.containsKey("port")) device.setPort(((Number) body.get("port")).intValue());
        if (body.containsKey("screenWidth")) device.setScreenWidth(((Number) body.get("screenWidth")).intValue());
        if (body.containsKey("screenHeight")) device.setScreenHeight(((Number) body.get("screenHeight")).intValue());
        if (body.containsKey("remark")) device.setRemark((String) body.get("remark"));

        deviceService.updateById(device);
        return ApiResponse.success("Updated", null);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> deleteDevice(@PathVariable Long id) {
        deviceService.removeById(id);
        return ApiResponse.success("Deleted", null);
    }

    @PostMapping("/{id}/connect")
    public ApiResponse<Void> connectDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("Device not found");
        }
        deviceService.connectDevice(id);
        log.info("Connected device: {}", device.getDeviceName());
        return ApiResponse.success("Connected", null);
    }

    @PostMapping("/{id}/disconnect")
    public ApiResponse<Void> disconnectDevice(@PathVariable Long id) {
        Device device = deviceService.getById(id);
        if (device == null) {
            return ApiResponse.fail("Device not found");
        }
        deviceService.disconnectDevice(id);
        log.info("Disconnected device: {}", device.getDeviceName());
        return ApiResponse.success("Disconnected", null);
    }

    @PostMapping("/refresh")
    public ApiResponse<List<Map<String, Object>>> refreshDevices() {
        List<Device> devices = deviceService.list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Device d : devices) {
            result.add(deviceToMap(d));
        }
        log.info("Refreshed device list, {} devices", devices.size());
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