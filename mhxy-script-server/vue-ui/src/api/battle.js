import request from '@/utils/request'

// 打怪场景API
export function getBattleSceneList(params) {
  return request({
    url: '/battle/scene/list',
    method: 'get',
    params
  })
}

export function getBattleSceneInfo(id) {
  return request({
    url: `/battle/scene/${id}`,
    method: 'get'
  })
}

export function addBattleScene(data) {
  return request({
    url: '/battle/scene',
    method: 'post',
    data
  })
}

export function updateBattleScene(id, data) {
  return request({
    url: `/battle/scene/${id}`,
    method: 'put',
    data
  })
}

export function deleteBattleScene(id) {
  return request({
    url: `/battle/scene/${id}`,
    method: 'delete'
  })
}

export function startBattleScene(id, deviceId) {
  return request({
    url: `/battle/scene/${id}/start`,
    method: 'post',
    data: { deviceId }
  })
}

export function stopBattleScene(id) {
  return request({
    url: `/battle/scene/${id}/stop`,
    method: 'post'
  })
}

export function getBattleExecutionList(params) {
  return request({
    url: '/battle/execution/list',
    method: 'get',
    params
  })
}
