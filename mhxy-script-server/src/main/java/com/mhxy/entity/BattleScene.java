package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("battle_scene")
public class BattleScene {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String sceneName;
    private String sceneType;
    private String gameType;
    private String gameArea;
    private String gameServer;
    private String roleName;
    private String levelRange;
    private Integer characterLevel;
    private String characterTeam;
    
    // JSON配置
    /** 战斗策略 JSON: { hpReplenish, mpReplenish, hpThreshold, mpThreshold, autoNavigate, battleOps: {...} } */
    private String battleStrategy;
    private String skillConfig;
    private String medicineConfig;
    private String petConfig;
    private String shoutConfig;
    
    // 执行参数
    private Integer autoBattle;
    private Integer autoRecovery;
    private Integer autoRevival;
    private Integer autoPickup;
    
    private String templatePath;
    private Integer status;
    private Long userId;
    private Integer useCount;
    private Integer successCount;
    private Integer totalDuration;
    
    private LocalDateTime createTime;
    private Long deviceId;

    private LocalDateTime updateTime;
}
