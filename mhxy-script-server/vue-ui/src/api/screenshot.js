import request from '@/utils/request'

// 截图管理API
export function getScreenshotList(params) {
  return request({
    url: '/screenshot/list',
    method: 'get',
    params
  })
}

export function captureFullScreen(deviceId) {
  return request({
    url: '/screenshot/full',
    method: 'get',
    params: { deviceId }
  })
}

export function captureRegion(deviceId, data) {
  return request({
    url: '/screenshot/region',
    method: 'post',
    data: { deviceId, ...data }
  })
}

export function deleteScreenshot(id) {
  return request({
    url: `/screenshot/${id}`,
    method: 'delete'
  })
}

export function batchDeleteScreenshots(ids) {
  return request({
    url: '/screenshot/batch',
    method: 'delete',
    data: { ids }
  })
}
