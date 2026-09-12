import api from './api'

export async function getResume() {
  try {
    const { data } = await api.get('/resumes/current')
    return data
  } catch (error) {
    if (error.response?.status === 404) return null
    throw error
  }
}

export async function uploadResume(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/resumes', formData, {
    timeout: 60_000,
    onUploadProgress(event) {
      if (!event.total) return
      onProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)))
    },
  })
  return data
}

export async function deleteResume() {
  await api.delete('/resumes/current')
}
