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
 * 打怪场景控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/battle")
public class BattleController {

    private final Map<Long, Map<String, Object>> sceneStore = new ConcurrentHashMap<>();
    private final Map<Long, Map<String, Object>> executionStore = new ConcurrentHashMap<>();
    private final AtomicLong sceneIdGenerator = new AtomicLong(1);
    private final AtomicLong execIdGenerator = new AtomicLong(1);

    public BattleController() {
        // 初始化示例场景
        addSampleScene("日常任务-师门", "pve", "生日快乐", "生日快乐10", "大唐官府01", 69, 156, 152);
        addSampleScene("抓鬼任务", "pve", "生日快乐", "生日快乐10", "大唐官府01", 109, 89, 85);
        addSampleScene("副本-水陆大会", "dungeon", "生日快乐", "生日快乐10", "大唐官府01", 129, 45, 42);
    }

    private void addSampleScene(String name, String type, String area, String server, String role, int level, int useCount, int successCount) {
        Map<String, Object> scene = new HashMap<>();
        scene.put("id", sceneIdGenerator.getAndIncrement());
        scene.put("sceneName", name);
        scene.put("sceneType", type);
        scene.put("gameType", "dianka");
        scene.put("gameArea", area);
        scene.put("gameServer", server);
        scene.put("roleName", role);
        scene.put("characterLevel", level);
        scene.put("characterTeam", "single");
        scene.put("autoBattle", true);
        scene.put("autoRecovery", true);
        scene.put("autoRevival", true);
        scene.put("autoPickup", true);
        scene.put("useCount", useCount);
        scene.put("successCount", successCount);
        sceneStore.put((Long) scene.get("id"), scene);
    }

    /**
     * 获取场景列表
     */
    @GetMapping("/scene/list")
    public ApiResponse<List<Map<String, Object>>> getSceneList() {
        return ApiResponse.success(new ArrayList<>(sceneStore.values()));
    }

    /**
     * 获取场景详情
     */
    @GetMapping("/scene/{id}")
    public ApiResponse<Map<String, Object>> getScene(@PathVariable Long id) {
        Map<String, Object> scene = sceneStore.get(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }
        return ApiResponse.success(scene);
    }

    /**
     * 添加场景
     */
    @PostMapping("/scene")
    public ApiResponse<Map<String, Object>> addScene(@RequestBody Map<String, Object> scene) {
        long id = sceneIdGenerator.getAndIncrement();
        scene.put("id", id);
        scene.put("useCount", 0);
        scene.put("successCount", 0);
        sceneStore.put(id, scene);
        log.info("添加场景: {}", scene.get("sceneName"));
        return ApiResponse.success("添加成功", scene);
    }

    /**
     * 更新场景
     */
    @PutMapping("/scene/{id}")
    public ApiResponse<Void> updateScene(@PathVariable Long id, @RequestBody Map<String, Object> scene) {
        if (!sceneStore.containsKey(id)) {
            return ApiResponse.fail("场景不存在");
        }
        scene.put("id", id);
        sceneStore.put(id, scene);
        return ApiResponse.success("更新成功", null);
    }

    /**
     * 删除场景
     */
    @DeleteMapping("/scene/{id}")
    public ApiResponse<Void> deleteScene(@PathVariable Long id) {
        sceneStore.remove(id);
        return ApiResponse.success("删除成功", null);
    }

    /**
     * 启动场景
     */
    @PostMapping("/scene/{id}/start")
    public ApiResponse<Map<String, Object>> startScene(@PathVariable Long id, @RequestBody Map<String, Object> params) {
        Map<String, Object> scene = sceneStore.get(id);
        if (scene == null) {
            return ApiResponse.fail("场景不存在");
        }

        Long deviceId = params.get("deviceId") != null ? ((Number) params.get("deviceId")).longValue() : 1L;

        Map<String, Object> execution = new HashMap<>();
        execution.put("id", execIdGenerator.getAndIncrement());
        execution.put("sceneId", id);
        execution.put("sceneName", scene.get("sceneName"));
        execution.put("deviceId", deviceId);
        execution.put("deviceName", "夜神模拟器");
        execution.put("progress", 0);
        execution.put("duration", 0);
        execution.put("status", 1);
        execution.put("battleCount", 0);
        execution.put("killCount", 0);
        execution.put("deathCount", 0);
        execution.put("goldEarned", 0);
        execution.put("expEarned", 0);

        executionStore.put((Long) execution.get("id"), execution);
        log.info("启动场景: {} on device: {}", scene.get("sceneName"), deviceId);

        return ApiResponse.success("启动成功", execution);
    }

    /**
     * 停止场景
     */
    @PostMapping("/scene/{id}/stop")
    public ApiResponse<Void> stopScene(@PathVariable Long id) {
        // 停止所有该场景的执行任务
        executionStore.values().removeIf(exec -> (Long) exec.get("sceneId") == id && (Integer) exec.get("status") == 1);
        log.info("停止场景: {}", id);
        return ApiResponse.success("停止成功", null);
    }

    /**
     * 获取执行记录列表
     */
    @GetMapping("/execution/list")
    public ApiResponse<List<Map<String, Object>>> getExecutionList() {
        List<Map<String, Object>> running = executionStore.values().stream()
            .filter(exec -> (Integer) exec.get("status") == 1)
            .toList();
        return ApiResponse.success(running);
    }
}
