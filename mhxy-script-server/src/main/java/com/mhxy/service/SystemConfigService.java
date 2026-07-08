package com.mhxy.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.SystemConfig;
import com.mhxy.mapper.SystemConfigMapper;
import org.springframework.stereotype.Service;

@Service
public class SystemConfigService extends ServiceImpl<SystemConfigMapper, SystemConfig> {

    public String getConfigValue(String key) {
        SystemConfig config = lambdaQuery().eq(SystemConfig::getConfigKey, key).one();
        return config != null ? config.getConfigValue() : null;
    }
}
