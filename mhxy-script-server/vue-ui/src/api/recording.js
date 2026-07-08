import request from '@/utils/request'

// 录制管理API
export function getRecordingList(params) {
  return request({
    url: '/recording/list',
    method: 'get',
    params
  })
}

export function getRecordingInfo(id) {
  return request({
    url: `/recording/${id}`,
    method: 'get'
  })
}

export function startRecording(data) {
  return request({
    url: '/recording/start',
    method: 'post',
    data
  })
}

export function stopRecording(id) {
  return request({
    url: `/recording/${id}/stop`,
    method: 'post'
  })
}

export function deleteRecording(id) {
  return request({
    url: `/recording/${id}`,
    method: 'delete'
  })
}

export function downloadRecording(id) {
  return request({
    url: `/recording/${id}/download`,
    method: 'get',
    responseType: 'blob'
  })
}
