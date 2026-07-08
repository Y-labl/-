package com.mhxy.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.mhxy.entity.BattleScene;
import com.mhxy.mapper.BattleSceneMapper;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class BattleSceneService extends ServiceImpl<BattleSceneMapper, BattleScene> {

    public List<BattleScene> listByUserId(Long userId) {
        return list(new LambdaQueryWrapper<BattleScene>()
                .eq(BattleScene::getUserId, userId)
                .orderByDesc(BattleScene::getCreateTime));
    }

    public List<BattleScene> listActive() {
        return list(new LambdaQueryWrapper<BattleScene>()
                .eq(BattleScene::getStatus, 1)
                .orderByDesc(BattleScene::getCreateTime));
    }
}
