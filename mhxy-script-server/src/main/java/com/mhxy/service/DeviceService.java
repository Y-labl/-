package com.mhxy.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.Device;
import com.mhxy.mapper.DeviceMapper;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class DeviceService extends ServiceImpl<DeviceMapper, Device> {

    public List<Device> listByUserId(Long userId) {
        return list(new LambdaQueryWrapper<Device>().eq(Device::getUserId, userId));
    }

    public List<Device> listOnline() {
        return list(new LambdaQueryWrapper<Device>().in(Device::getStatus, 1, 2));
    }

    public boolean connectDevice(Long id) {
        Device device = getById(id);
        if (device == null) return false;
        device.setStatus(2);
        return updateById(device);
    }

    public boolean disconnectDevice(Long id) {
        Device device = getById(id);
        if (device == null) return false;
        device.setStatus(1);
        return updateById(device);
    }
}
