package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("steal_card_config")
public class StealCardConfig {
    @TableId(type = IdType.AUTO)
    private Long id;

    private Long deviceId;
    private String configName;
    private String targetMonsters;
    /** 完整战斗策略 JSON（加血加蓝、阈值、自动导路、战斗操作、妙手空空 8 场景等） */
    private String battleStrategy;

    private Integer autoBattle;
    private Integer autoRecovery;
    private Integer autoRevival;
    private Integer autoPickup;

    private String mapClickArea;
    private Double templateConfidence;
    private Integer walkInterval;
    private Integer stealAttempts;

    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
