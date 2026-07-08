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

// 偷卡API
export function startSteal(id, deviceId) {
  return request({
    url: `/battle/scene/${id}/steal/start`,
    method: 'post',
    data: { deviceId }
  })
}

export function stopSteal(id) {
  return request({
    url: `/battle/scene/${id}/steal/stop`,
    method: 'post'
  })
}

export function getStealStatus(id) {
  return request({
    url: `/battle/scene/${id}/steal/status`,
    method: 'get'
  })
}

// ============ 偷卡配置（设备级）API ============
export function getStealConfigList() {
  return request({ url: '/steal-card/list', method: 'get' })
}

export function getStealConfigByDevice(deviceId) {
  return request({ url: `/steal-card/device/${deviceId}`, method: 'get' })
}

export function saveStealConfig(deviceId, data) {
  return request({ url: `/steal-card/device/${deviceId}`, method: 'post', data })
}

export function startStealByDevice(deviceId) {
  return request({ url: `/steal-card/device/${deviceId}/start`, method: 'post' })
}

export function stopStealByDevice(deviceId) {
  return request({ url: `/steal-card/device/${deviceId}/stop`, method: 'post' })
}

export function getStealRunningDevices() {
  return request({ url: '/steal-card/running', method: 'get' })
}