package com.mhxy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("template_image")
public class TemplateImage {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String templateName;
    private String templatePath;
    private String category;
    private String description;
    private Double matchThreshold;
    private Integer width;
    private Integer height;
    private Integer fileSize;
    private Integer usageCount;
    private Integer successCount;
    private Long userId;
    private Integer status;
    private LocalDateTime createTime;
}