import api from './api'

export async function getHealthStatus() {
  const { data } = await api.get('/health')
  return data
}
