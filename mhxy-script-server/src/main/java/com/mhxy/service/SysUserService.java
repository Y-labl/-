package com.mhxy.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.SysUser;
import com.mhxy.mapper.SysUserMapper;
import org.springframework.stereotype.Service;

@Service
public class SysUserService extends ServiceImpl<SysUserMapper, SysUser> {

    public SysUser findByUsername(String username) {
        return lambdaQuery().eq(SysUser::getUsername, username).one();
    }
}
