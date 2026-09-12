import api from './api'

export async function getCareerAnalytics() {
  const { data } = await api.get('/analytics/dashboard')
  return data
}
