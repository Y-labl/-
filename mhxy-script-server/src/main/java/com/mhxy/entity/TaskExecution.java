package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("task_execution")
public class TaskExecution {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String taskType;
    private Long taskId;
    private Long deviceId;
    private Long userId;
    
    private Integer status;
    private Integer progress;
    private String currentStep;
    private String errorMsg;
    
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private Integer duration;
    
    private String resultData;
    
    private Integer battleCount;
    private Integer killCount;
    private Integer deathCount;
    private Integer goldEarned;
    private Integer expEarned;
    
    private LocalDateTime createTime;
}
