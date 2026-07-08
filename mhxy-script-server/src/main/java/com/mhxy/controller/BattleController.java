package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.BattleScene;
import com.mhxy.entity.Device;
import com.mhxy.entity.TaskExecution;
import com.mhxy.service.BattleSceneService;
import com.mhxy.service.DeviceService;
import com.mhxy.service.StealCardService;
import com.mhxy.service.TaskExecutionService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/battle")
public class BattleController {

    @Autowired
    private BattleSceneService sceneService;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private TaskExecutionService executionService;

    @Autowired
    private StealCardService stealCardService;

    /**
     * 获取场景列表
     */
    @GetMapping("/scene/list")
    public ApiResponse<List<Map<String, Object>>> getSceneList() {
        List<BattleScene> scenes = sceneService.listActive();
        List<Map<String, Object>> result = new ArrayList<>();
        for (BattleScene s : scenes) {
            result.add(sceneToMap(s));
        }
        return ApiResponse.success(result);
    }

    /**
     * 获取场景详情
     */
    @GetMapping("/scene/{id}")
    public ApiResponse<Map<String, Object>> getScene(@PathVariable Long id) {
        BattleScene scene = sceneService.getById(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }
        return ApiResponse.success(sceneToMap(scene));
    }

    /**
     * 添加场景
     */
    @PostMapping("/scene")
    public ApiResponse<Map<String, Object>> addScene(@RequestBody Map<String, Object> body) {
        BattleScene scene = new BattleScene();
        scene.setSceneName((String) body.get("sceneName"));
        scene.setSceneType((String) body.get("sceneType"));
        scene.setGameType((String) body.getOrDefault("gameType", "dianka"));
        scene.setGameArea((String) body.get("gameArea"));
        scene.setGameServer((String) body.get("gameServer"));
        scene.setRoleName((String) body.get("roleName"));
        scene.setCharacterLevel(body.get("characterLevel") != null ? ((Number) body.get("characterLevel")).intValue() : null);
        scene.setCharacterTeam((String) body.getOrDefault("characterTeam", "single"));
        Object autoBattle = body.get("autoBattle");
        scene.setAutoBattle(autoBattle instanceof Boolean b && b ? 1 : 0);
        Object autoRecovery = body.get("autoRecovery");
        scene.setAutoRecovery(autoRecovery instanceof Boolean b && b ? 1 : 0);
        Object autoRevival = body.get("autoRevival");
        scene.setAutoRevival(autoRevival instanceof Boolean b && b ? 1 : 0);
        Object autoPickup = body.get("autoPickup");
        scene.setAutoPickup(autoPickup instanceof Boolean b && b ? 1 : 0);
        if (body.get("skillConfig") != null) scene.setSkillConfig((String) body.get("skillConfig"));
        if (body.containsKey("battleStrategy")) scene.setBattleStrategy(serializeStrategy(body.get("battleStrategy")));
        scene.setDeviceId(body.get("deviceId") != null ? ((Number) body.get("deviceId")).longValue() : null);
        scene.setUseCount(0);
        scene.setSuccessCount(0);
        scene.setStatus(1);
        scene.setCreateTime(LocalDateTime.now());

        sceneService.save(scene);
        log.info("添加场景: {}", scene.getSceneName());
        return ApiResponse.success("添加成功", sceneToMap(scene));
    }

    /**
     * 更新场景
     */
    @PutMapping("/scene/{id}")
    public ApiResponse<Void> updateScene(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        BattleScene scene = sceneService.getById(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }
        if (body.containsKey("sceneName")) scene.setSceneName((String) body.get("sceneName"));
        if (body.containsKey("sceneType")) scene.setSceneType((String) body.get("sceneType"));
        if (body.containsKey("gameArea")) scene.setGameArea((String) body.get("gameArea"));
        if (body.containsKey("gameServer")) scene.setGameServer((String) body.get("gameServer"));
        if (body.containsKey("characterLevel")) scene.setCharacterLevel(((Number) body.get("characterLevel")).intValue());
        Object autoBattle = body.get("autoBattle");
        if (autoBattle != null) scene.setAutoBattle(autoBattle instanceof Boolean b && b ? 1 : 0);
        Object autoRecovery = body.get("autoRecovery");
        if (autoRecovery != null) scene.setAutoRecovery(autoRecovery instanceof Boolean b && b ? 1 : 0);
        Object autoRevival = body.get("autoRevival");
        if (autoRevival != null) scene.setAutoRevival(autoRevival instanceof Boolean b && b ? 1 : 0);
        Object autoPickup = body.get("autoPickup");
        if (autoPickup != null) scene.setAutoPickup(autoPickup instanceof Boolean b && b ? 1 : 0);
        if (body.containsKey("skillConfig")) scene.setSkillConfig((String) body.get("skillConfig"));
        if (body.containsKey("battleStrategy")) scene.setBattleStrategy(serializeStrategy(body.get("battleStrategy")));

        sceneService.updateById(scene);
        return ApiResponse.success("更新成功", null);
    }

    /**
     * 删除场景
     */
    @DeleteMapping("/scene/{id}")
    public ApiResponse<Void> deleteScene(@PathVariable Long id) {
        sceneService.removeById(id);
        log.info("删除场景: {}", id);
        return ApiResponse.success("删除成功", null);
    }

    /**
     * 启动场景
     */
    @PostMapping("/scene/{id}/start")
    public ApiResponse<Map<String, Object>> startScene(@PathVariable Long id, @RequestBody Map<String, Object> params) {
        BattleScene scene = sceneService.getById(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }

        Long deviceId = params.get("deviceId") != null ? ((Number) params.get("deviceId")).longValue() : (scene.getDeviceId() != null ? scene.getDeviceId() : 1L);
        Device device = deviceService.getById(deviceId);
        String deviceName = device != null ? device.getDeviceName() : "未知设备";

        TaskExecution execution = new TaskExecution();
        execution.setTaskType(scene.getSceneType());
        execution.setTaskId(id);
        execution.setDeviceId(deviceId);
        execution.setUserId(scene.getUserId() != null ? scene.getUserId() : 1L);
        execution.setStatus(1);
        execution.setProgress(0);
        execution.setDuration(0);
        execution.setBattleCount(0);
        execution.setKillCount(0);
        execution.setDeathCount(0);
        execution.setGoldEarned(0);
        execution.setExpEarned(0);
        execution.setCreateTime(LocalDateTime.now());

        executionService.save(execution);

        scene.setUseCount((scene.getUseCount() == null ? 0 : scene.getUseCount()) + 1);
        sceneService.updateById(scene);

        log.info("启动场景: {} on device: {}", scene.getSceneName(), deviceId);

        Map<String, Object> result = new HashMap<>();
        result.put("id", execution.getId());
        result.put("sceneId", id);
        result.put("sceneName", scene.getSceneName());
        result.put("deviceId", deviceId);
        result.put("deviceName", deviceName);
        result.put("progress", 0);
        result.put("duration", 0);
        result.put("status", 1);
        result.put("battleCount", 0);
        result.put("killCount", 0);
        result.put("deathCount", 0);
        result.put("goldEarned", 0);
        result.put("expEarned", 0);

        return ApiResponse.success("启动成功", result);
    }

    /**
     * 停止场景
     */
    @PostMapping("/scene/{id}/stop")
    public ApiResponse<Void> stopScene(@PathVariable Long id) {
        BattleScene scene = sceneService.getById(id);
        if (scene != null && "steal_card".equals(scene.getSceneType())) {
            stealCardService.stop();
        }
        List<TaskExecution> running = executionService.listBySceneId(id);
        for (TaskExecution exec : running) {
            if (exec.getStatus() != null && exec.getStatus() == 1) {
                exec.setStatus(0);
                exec.setEndTime(LocalDateTime.now());
                executionService.updateById(exec);
            }
        }
        log.info("停止场景: {}", id);
        return ApiResponse.success("停止成功", null);
    }

    /**
     * 获取执行记录列表
     */
    @GetMapping("/execution/list")
    public ApiResponse<List<Map<String, Object>>> getExecutionList() {
        List<TaskExecution> running = executionService.listRunning();
        List<Map<String, Object>> result = new ArrayList<>();
        for (TaskExecution exec : running) {
            Map<String, Object> map = new HashMap<>();
            map.put("id", exec.getId());
            map.put("sceneId", exec.getTaskId());
            map.put("deviceId", exec.getDeviceId());
            map.put("progress", exec.getProgress() != null ? exec.getProgress() : 0);
            map.put("duration", exec.getDuration() != null ? exec.getDuration() : 0);
            map.put("status", exec.getStatus());
            map.put("battleCount", exec.getBattleCount() != null ? exec.getBattleCount() : 0);
            map.put("killCount", exec.getKillCount() != null ? exec.getKillCount() : 0);
            map.put("deathCount", exec.getDeathCount() != null ? exec.getDeathCount() : 0);
            map.put("goldEarned", exec.getGoldEarned() != null ? exec.getGoldEarned() : 0);
            map.put("expEarned", exec.getExpEarned() != null ? exec.getExpEarned() : 0);
            result.add(map);
        }
        return ApiResponse.success(result);
    }

    /**
     * 启动偷卡自动化
     */
    @PostMapping("/scene/{id}/steal/start")
    public ApiResponse<Map<String, Object>> startSteal(@PathVariable Long id, @RequestBody Map<String, Object> params) {
        BattleScene scene = sceneService.getById(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }

        Long deviceId = params.get("deviceId") != null ? ((Number) params.get("deviceId")).longValue() : (scene.getDeviceId() != null ? scene.getDeviceId() : 1L);
        Device device = deviceService.getById(deviceId);
        if (device == null || device.getDeviceId() == null) {
            return ApiResponse.fail("设备不存在或未连接");
        }

        if (device.getStatus() == null || device.getStatus() != 1) {
            return ApiResponse.fail("设备离线，请先连接设备");
        }

        if (stealCardService.isRunning()) {
            return ApiResponse.fail("偷卡已在运行中，请先停止");
        }

        stealCardService.start(deviceId, scene);

        Map<String, Object> result = new HashMap<>();
        result.put("sceneId", id);
        result.put("sceneName", scene.getSceneName());
        result.put("deviceId", deviceId);
        result.put("deviceName", device.getDeviceName());
        result.put("status", "running");

        log.info("启动偷卡: {} on device: {}", scene.getSceneName(), deviceId);
        return ApiResponse.success("偷卡已启动", result);
    }

    /**
     * 停止偷卡自动化
     */
    @PostMapping("/scene/{id}/steal/stop")
    public ApiResponse<Void> stopSteal(@PathVariable Long id) {
        stealCardService.stop();
        log.info("停止偷卡场景: {}", id);
        return ApiResponse.success("偷卡已停止", null);
    }

    /**
     * 获取偷卡运行状态
     */
    @GetMapping("/scene/{id}/steal/status")
    public ApiResponse<Map<String, Object>> getStealStatus(@PathVariable Long id) {
        Map<String, Object> result = new HashMap<>();
        result.put("sceneId", id);
        result.put("running", stealCardService.isRunning());
        return ApiResponse.success(result);
    }

    private Map<String, Object> sceneToMap(BattleScene s) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", s.getId());
        map.put("sceneName", s.getSceneName());
        map.put("sceneType", s.getSceneType());
        map.put("gameType", s.getGameType());
        map.put("gameArea", s.getGameArea());
        map.put("gameServer", s.getGameServer());
        map.put("roleName", s.getRoleName());
        map.put("characterLevel", s.getCharacterLevel());
        map.put("characterTeam", s.getCharacterTeam());
        map.put("autoBattle", s.getAutoBattle() != null && s.getAutoBattle() == 1);
        map.put("autoRecovery", s.getAutoRecovery() != null && s.getAutoRecovery() == 1);
        map.put("autoRevival", s.getAutoRevival() != null && s.getAutoRevival() == 1);
        map.put("autoPickup", s.getAutoPickup() != null && s.getAutoPickup() == 1);
        map.put("skillConfig", s.getSkillConfig());
        map.put("battleStrategy", parseStrategy(s.getBattleStrategy()));
        map.put("useCount", s.getUseCount());
        map.put("successCount", s.getSuccessCount());
        map.put("deviceId", s.getDeviceId());
        return map;
    }

    /* ---- battleStrategy JSON 序列化/反序列化 ---- */
    private static final ObjectMapper STRATEGY_MAPPER = new ObjectMapper();

    /** 默认策略：避免 null */
    private static final Map<String, Object> DEFAULT_STRATEGY = defaultStrategy();

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
        return s;
    }

    private String serializeStrategy(Object raw) {
        try {
            if (raw == null) return STRATEGY_MAPPER.writeValueAsString(DEFAULT_STRATEGY);
            if (raw instanceof String s) {
                if (s.isEmpty()) return STRATEGY_MAPPER.writeValueAsString(DEFAULT_STRATEGY);
                // 验证是否合法 JSON
                STRATEGY_MAPPER.readTree(s);
                return s;
            }
            return STRATEGY_MAPPER.writeValueAsString(raw);
        } catch (Exception e) {
            log.warn("serializeStrategy failed: {}", e.getMessage());
            try { return STRATEGY_MAPPER.writeValueAsString(DEFAULT_STRATEGY); }
            catch (Exception ex) { return "{}"; }
        }
    }

    private Map<String, Object> parseStrategy(String json) {
        Map<String, Object> def = new LinkedHashMap<>(DEFAULT_STRATEGY);
        Map<String, Object> opsDef = new LinkedHashMap<>((Map<String, Object>) def.get("battleOps"));
        if (json == null || json.isEmpty()) {
            def.put("battleOps", opsDef);
            return def;
        }
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = STRATEGY_MAPPER.readValue(json, Map.class);
            def.putAll(map);
            if (map.get("battleOps") instanceof Map<?, ?> opsIn) {
                Map<String, Object> ops = new LinkedHashMap<>(opsDef);
                for (Map.Entry<?, ?> e : opsIn.entrySet()) {
                    ops.put(String.valueOf(e.getKey()), e.getValue());
                }
                def.put("battleOps", ops);
            }
            return def;
        } catch (Exception e) {
            def.put("battleOps", opsDef);
            return def;
        }
    }
}