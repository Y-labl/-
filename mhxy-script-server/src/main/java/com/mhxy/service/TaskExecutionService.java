package com.mhxy.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.TaskExecution;
import com.mhxy.mapper.TaskExecutionMapper;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class TaskExecutionService extends ServiceImpl<TaskExecutionMapper, TaskExecution> {

    public List<TaskExecution> listByUserId(Long userId) {
        return list(new LambdaQueryWrapper<TaskExecution>()
                .eq(TaskExecution::getUserId, userId)
                .orderByDesc(TaskExecution::getCreateTime));
    }

    public List<TaskExecution> listRunning() {
        return list(new LambdaQueryWrapper<TaskExecution>()
                .eq(TaskExecution::getStatus, 1));
    }

    public List<TaskExecution> listBySceneId(Long sceneId) {
        return list(new LambdaQueryWrapper<TaskExecution>()
                .eq(TaskExecution::getTaskId, sceneId)
                .orderByDesc(TaskExecution::getCreateTime));
    }
}
