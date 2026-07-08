package com.mhxy.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.StealCardConfig;
import com.mhxy.mapper.StealCardConfigMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class StealCardConfigService extends ServiceImpl<StealCardConfigMapper, StealCardConfig> {

    public StealCardConfig getByDeviceId(Long deviceId) {
        List<StealCardConfig> list = list(new LambdaQueryWrapper<StealCardConfig>()
                .eq(StealCardConfig::getDeviceId, deviceId));
        return list.isEmpty() ? null : list.get(0);
    }
}
