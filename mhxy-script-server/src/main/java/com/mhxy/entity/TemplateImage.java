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
    private String templateType;
    private String filePath;
    private String fileName;
    private Integer fileSize;
    private Integer width;
    private Integer height;
    private Double matchThreshold;
    private String tags;
    private String description;
    private Integer useCount;
    private Integer status;
    private Long userId;
    private LocalDateTime createTime;
}
