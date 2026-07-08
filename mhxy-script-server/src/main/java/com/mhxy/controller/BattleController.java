package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.entity.BattleScene;
import com.mhxy.entity.Device;
import com.mhxy.entity.TaskExecution;
import com.mhxy.service.BattleSceneService;
import com.mhxy.service.DeviceService;
import com.mhxy.service.TaskExecutionService;
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

        sceneService.updateById(scene);
        return ApiResponse.success("更新成功", null);
    }

    /**
     * 删除场景
     */
    @DeleteMapping("/scene/{id}")
    public ApiResponse<Void> deleteScene(@PathVariable Long id) {
        sceneService.removeById(id);
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

        Long deviceId = params.get("deviceId") != null ? ((Number) params.get("deviceId")).longValue() : 1L;
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

        // 更新场景使用次数
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
        map.put("useCount", s.getUseCount());
        map.put("successCount", s.getSuccessCount());
        return map;
    }
}
