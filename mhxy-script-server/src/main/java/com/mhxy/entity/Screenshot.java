package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("screenshot")
public class Screenshot {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long deviceId;
    private Long userId;
    private String fileName;
    private String filePath;
    private Integer fileSize;
    private String thumbnailPath;
    private Integer screenWidth;
    private Integer screenHeight;
    private String label;
    private String tags;
    private LocalDateTime createTime;
}
