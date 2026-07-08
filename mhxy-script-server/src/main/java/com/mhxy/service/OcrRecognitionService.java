package com.mhxy.service;

import com.mhxy.entity.Device;
import com.mhxy.util.OcrUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.awt.image.BufferedImage;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * OCR recognition service - location and coordinate detection.
 * Ported from Python RapidOCR-based scripts for梦幻西游 automation.
 */
@Slf4j
@Service
public class OcrRecognitionService {

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private DeviceScannerService scannerService;

    @Autowired
    private OcrUtil ocrUtil;

    // 游戏中可能出现的地名前缀
    private static final List<String> VALID_LOCATIONS = Arrays.asList(
        "小西天", "长安城", "大唐国境", "五庄观", "花果山",
        "傲来国", "朱紫国", "宝象国", "乌鸡国", "车迟国",
        "东海湾", "长寿村", "化生寺", "方寸山", "女儿村",
        "大雷音寺", "龙窟一层", "龙窟二层", "龙窟三层", "龙窟四层",
        "大唐境外", "江南野外", "建邺城", "北俱芦洲", "麒麟山",
        "子母河", "解阳山", "西凉女国", "宝象国", "碗子山"
    );

    // 坐标正则: 如 (123,456) 或 （123，456） 或 123,456
    private static final Pattern COORD_PATTERN = Pattern.compile(
        "[（(]?\\s*(\\d{1,4})\\s*[,，]\\s*(\\d{1,4})\\s*[）)]?"
    );

    /**
     * Recognize current location name from device screenshot.
     */
    public Optional<String> recognizeLocation(Long deviceId) {
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) return Optional.empty();

        byte[] screenshot = scannerService.captureAdbScreenshot(device.getDeviceId());
        if (screenshot == null || screenshot.length == 0) return Optional.empty();

        // OCR the top-left corner where location text appears (大约左上 350x110 区域)
        BufferedImage img = ocrUtil.bytesToImage(screenshot);
        if (img == null) return Optional.empty();

        int cropW = Math.min(350, img.getWidth());
        int cropH = Math.min(110, img.getHeight());
        BufferedImage crop = img.getSubimage(0, 0, cropW, cropH);

        String text = ocrUtil.recognize(crop);
        if (text == null || text.isEmpty()) return Optional.empty();

        log.debug("OCR location text: {}", text);

        for (String loc : VALID_LOCATIONS) {
            if (text.contains(loc)) return Optional.of(loc);
        }
        return Optional.empty();
    }

    /**
     * Recognize coordinates from device screenshot.
     * Returns (x, y) if found.
     */
    public Optional<int[]> recognizeCoordinates(Long deviceId) {
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) return Optional.empty();

        byte[] screenshot = scannerService.captureAdbScreenshot(device.getDeviceId());
        if (screenshot == null || screenshot.length == 0) return Optional.empty();

        BufferedImage img = ocrUtil.bytesToImage(screenshot);
        if (img == null) return Optional.empty();

        int cropW = Math.min(350, img.getWidth());
        int cropH = Math.min(110, img.getHeight());
        BufferedImage crop = img.getSubimage(0, 0, cropW, cropH);

        String text = ocrUtil.recognize(crop);
        if (text == null || text.isEmpty()) return Optional.empty();

        log.debug("OCR coord text: {}", text);

        Matcher m = COORD_PATTERN.matcher(text);
        if (m.find()) {
            try {
                int x = Integer.parseInt(m.group(1));
                int y = Integer.parseInt(m.group(2));
                return Optional.of(new int[]{x, y});
            } catch (NumberFormatException ignored) {}
        }
        return Optional.empty();
    }

    /**
     * Full recognition: return location + coordinates from device.
     */
    public Map<String, Object> recognizeFull(Long deviceId) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deviceId", deviceId);

        Optional<String> loc = recognizeLocation(deviceId);
        result.put("location", loc.orElse("unknown"));

        Optional<int[]> coord = recognizeCoordinates(deviceId);
        if (coord.isPresent()) {
            result.put("x", coord.get()[0]);
            result.put("y", coord.get()[1]);
        }

        return result;
    }

    /**
     * Check if currently on the specified map location.
     */
    public boolean isAtLocation(Long deviceId, String expectedLocation) {
        return recognizeLocation(deviceId)
            .map(loc -> loc.equals(expectedLocation))
            .orElse(false);
    }
}