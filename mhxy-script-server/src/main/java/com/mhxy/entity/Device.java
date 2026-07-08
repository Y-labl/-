package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("device")
public class Device {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String deviceName;
    private String deviceType;
    private String deviceId;
    private String ipAddress;
    private Integer port;
    private Integer screenWidth;
    private Integer screenHeight;
    private Integer status;
    private Long userId;
    private Long currentOrderId;
    private String remark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
