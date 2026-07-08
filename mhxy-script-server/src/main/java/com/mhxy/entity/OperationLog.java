package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("operation_log")
public class OperationLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String userName;
    private String action;
    private String module;
    private String targetType;
    private Long targetId;
    private String description;
    private String ipAddress;
    private String userAgent;
    private String requestData;
    private String responseData;
    private Integer status;
    private String errorMsg;
    private LocalDateTime createTime;
}
