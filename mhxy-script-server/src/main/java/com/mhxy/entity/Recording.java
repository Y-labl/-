package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("recording")
public class Recording {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long deviceId;
    private Long userId;
    private String taskName;
    private String outputPath;
    private String outputFile;
    private Integer duration;
    private Long fileSize;
    private Integer fps;
    private String resolution;
    private Integer status;
    private String errorMsg;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private LocalDateTime createTime;
}
