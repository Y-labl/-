import request from '@/utils/request'

export function getDeviceList(params) {
  return request({ url: '/device/list', method: 'get', params })
}

export function getDeviceInfo(id) {
  return request({ url: `/device/${id}`, method: 'get' })
}

export function addDevice(data) {
  return request({ url: '/device', method: 'post', data })
}

export function updateDevice(id, data) {
  return request({ url: `/device/${id}`, method: 'put', data })
}

export function deleteDevice(id) {
  return request({ url: `/device/${id}`, method: 'delete' })
}

export function connectDevice(id) {
  return request({ url: `/device/${id}/connect`, method: 'post' })
}

export function disconnectDevice(id) {
  return request({ url: `/device/${id}/disconnect`, method: 'post' })
}

export function refreshDevices() {
  return request({ url: '/device/refresh', method: 'post' })
}

export function scanDevices() {
  return request({ url: '/device/scan', method: 'get' })
}

export function bindDevice(data) {
  return request({ url: '/device/bind', method: 'post', data })
}
