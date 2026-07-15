package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.Device;
import com.mhxy.entity.StealCardConfig;
import com.mhxy.service.DeviceService;
import com.mhxy.service.StealCardConfigService;
import com.mhxy.service.StealCardService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 偷卡配置（设备级）+ 启停接口。
 * 每个设备可独立配置、独立启动偷卡任务。
 */
@Slf4j
@RestController
@RequestMapping("/api/steal-card")
public class StealCardController {

    @Autowired
    private StealCardConfigService configService;

    @Autowired
    private StealCardService stealCardService;

    @Autowired
    private DeviceService deviceService;

    /** 列表所有偷卡配置（按设备） */
    @GetMapping("/list")
    public ApiResponse<List<Map<String, Object>>> list() {
        List<StealCardConfig> configs = configService.list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (StealCardConfig c : configs) result.add(toMap(c));
        return ApiResponse.success(result);
    }

    /** 获取某设备的配置（不存在则返回默认空配置） */
    @GetMapping("/device/{deviceId}")
    public ApiResponse<Map<String, Object>> getByDevice(@PathVariable Long deviceId) {
        StealCardConfig cfg = configService.getByDeviceId(deviceId);
        if (cfg == null) {
            // 返回默认空配置（前端可显示）
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("deviceId", deviceId);
            empty.put("configName", "偷卡配置");
            empty.put("targetMonsters", "噬天虎,炎魔神,金饶僧");
            empty.put("battleStrategy", defaultStrategy());
            empty.put("autoBattle", 1);
            empty.put("autoRecovery", 1);
            empty.put("autoRevival", 1);
            empty.put("autoPickup", 1);
            empty.put("mapClickArea", "80,180,980,2200");
            empty.put("templateConfidence", 0.80);
            empty.put("walkInterval", 500);
            empty.put("stealAttempts", 3);
            empty.put("status", 1);
            empty.put("running", stealCardService.isRunning(deviceId));
            return ApiResponse.success(empty);
        }
        Map<String, Object> map = toMap(cfg);
        map.put("running", stealCardService.isRunning(deviceId));
        return ApiResponse.success(map);
    }

    /** 保存（新增或更新）某设备的配置 */
    @PostMapping("/device/{deviceId}")
    public ApiResponse<Map<String, Object>> save(@PathVariable Long deviceId, @RequestBody Map<String, Object> body) {
        StealCardConfig cfg = configService.getByDeviceId(deviceId);
        boolean isNew = cfg == null;
        if (isNew) {
            cfg = new StealCardConfig();
            cfg.setDeviceId(deviceId);
            cfg.setCreateTime(LocalDateTime.now());
        }
        if (body.containsKey("configName")) cfg.setConfigName((String) body.get("configName"));
        if (body.containsKey("targetMonsters")) cfg.setTargetMonsters((String) body.get("targetMonsters"));
        if (body.containsKey("battleStrategy")) cfg.setBattleStrategy(serializeJson(body.get("battleStrategy")));
        if (body.containsKey("mapClickArea")) cfg.setMapClickArea((String) body.get("mapClickArea"));
        cfg.setAutoBattle(toInt(body.get("autoBattle"), 1));
        cfg.setAutoRecovery(toInt(body.get("autoRecovery"), 1));
        cfg.setAutoRevival(toInt(body.get("autoRevival"), 1));
        cfg.setAutoPickup(toInt(body.get("autoPickup"), 1));
        cfg.setTemplateConfidence(toDouble(body.get("templateConfidence"), 0.80));
        cfg.setWalkInterval(toInt(body.get("walkInterval"), 500));
        cfg.setStealAttempts(toInt(body.get("stealAttempts"), 3));
        cfg.setStatus(toInt(body.get("status"), 1));
        cfg.setUpdateTime(LocalDateTime.now());

        if (isNew) configService.save(cfg);
        else configService.updateById(cfg);

        log.info("StealCard config saved for device {}: monsters={}", deviceId, cfg.getTargetMonsters());
        return ApiResponse.success("保存成功", toMap(cfg));
    }

    /** 启动某设备的偷卡任务 */
    @PostMapping("/device/{deviceId}/start")
    public ApiResponse<Map<String, Object>> start(@PathVariable Long deviceId) {
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) {
            return ApiResponse.fail("设备不存在或未连接");
        }
        if (device.getStatus() == null || device.getStatus() == 0) {
            return ApiResponse.fail("设备离线，请先连接设备");
        }
        if (stealCardService.isRunning(deviceId)) {
            return ApiResponse.fail("该设备偷卡已在运行中");
        }
        boolean ok = stealCardService.start(deviceId);
        if (!ok) return ApiResponse.fail("启动失败");
        Map<String, Object> result = new HashMap<>();
        result.put("deviceId", deviceId);
        result.put("deviceName", device.getDeviceName());
        result.put("running", true);
        return ApiResponse.success("偷卡已启动", result);
    }

    /** 停止某设备的偷卡任务 */
    @PostMapping("/device/{deviceId}/stop")
    public ApiResponse<Void> stop(@PathVariable Long deviceId) {
        stealCardService.stop(deviceId);
        log.info("停止偷卡: device {}", deviceId);
        return ApiResponse.success("偷卡已停止", null);
    }

    /** 查询某设备偷卡运行状态 */
    @GetMapping("/device/{deviceId}/status")
    public ApiResponse<Map<String, Object>> status(@PathVariable Long deviceId) {
        Map<String, Object> result = new HashMap<>();
        result.put("deviceId", deviceId);
        result.put("running", stealCardService.isRunning(deviceId));
        return ApiResponse.success(result);
    }

    /** 查询所有正在运行偷卡的设备 */
    @GetMapping("/running")
    public ApiResponse<List<Map<String, Object>>> running() {
        List<Long> ids = stealCardService.getRunningDeviceIds();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Long id : ids) {
            Device d = deviceService.getById(id);
            Map<String, Object> m = new HashMap<>();
            m.put("deviceId", id);
            m.put("deviceName", d != null ? d.getDeviceName() : "");
            m.put("running", true);
            result.add(m);
        }
        return ApiResponse.success(result);
    }

    /* ---- helpers ---- */
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();

    /** 默认战斗策略（与前端 defaultStrategy 对应） */
    private static Map<String, Object> defaultStrategy() {
        Map<String, Object> ops = new LinkedHashMap<>();
        ops.put("1_capture", true);
        ops.put("2_steal", true);
        ops.put("3_1_after_skill", true);
        ops.put("3_2_after_normal_attack", false);
        ops.put("3_3_after_defense", false);
        ops.put("3_4_direct_battle", false);
        ops.put("3_5_escape", false);
        Map<String, Object> s = new LinkedHashMap<>();
        s.put("hpReplenish", "酒肆");
        s.put("mpReplenish", "酒肆");
        s.put("hpThreshold", 40);
        s.put("mpThreshold", 30);
        s.put("autoNavigate", true);
        s.put("battleOps", ops);
        s.put("stealBoundDeviceId", null);
        s.put("stealScenes", new java.util.ArrayList<>());
        return s;
    }

    /** 序列化对象为 JSON 字符串（输入可能是 Map/Object/String） */
    private String serializeJson(Object raw) {
        try {
            if (raw == null) return null;
            if (raw instanceof String s) {
                if (s.isEmpty()) return null;
                JSON_MAPPER.readTree(s); // 验证合法
                return s;
            }
            return JSON_MAPPER.writeValueAsString(raw);
        } catch (Exception e) {
            log.warn("serializeJson failed: {}", e.getMessage());
            return null;
        }
    }

    /** 把 JSON 字符串解析为 Map（失败返回默认策略） */
    private Object parseJson(String json) {
        if (json == null || json.isEmpty()) return defaultStrategy();
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> parsed = JSON_MAPPER.readValue(json, Map.class);
            Map<String, Object> def = defaultStrategy();
            def.putAll(parsed);
            return def;
        } catch (Exception e) {
            return defaultStrategy();
        }
    }

    private static int toInt(Object o, int def) {
        if (o == null) return def;
        if (o instanceof Boolean b) return b ? 1 : 0;
        if (o instanceof Number n) return n.intValue();
        try { return Integer.parseInt(o.toString()); } catch (Exception e) { return def; }
    }

    private static double toDouble(Object o, double def) {
        if (o == null) return def;
        if (o instanceof Number n) return n.doubleValue();
        try { return Double.parseDouble(o.toString()); } catch (Exception e) { return def; }
    }

    private Map<String, Object> toMap(StealCardConfig c) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", c.getId());
        m.put("deviceId", c.getDeviceId());
        m.put("configName", c.getConfigName());
        m.put("targetMonsters", c.getTargetMonsters());
        m.put("battleStrategy", parseJson(c.getBattleStrategy()));
        m.put("autoBattle", c.getAutoBattle());
        m.put("autoRecovery", c.getAutoRecovery());
        m.put("autoRevival", c.getAutoRevival());
        m.put("autoPickup", c.getAutoPickup());
        m.put("mapClickArea", c.getMapClickArea());
        m.put("templateConfidence", c.getTemplateConfidence());
        m.put("walkInterval", c.getWalkInterval());
        m.put("stealAttempts", c.getStealAttempts());
        m.put("status", c.getStatus());
        m.put("createTime", c.getCreateTime());
        m.put("updateTime", c.getUpdateTime());
        return m;
    }
}
