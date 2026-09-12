import api from './api'

const AI_TIMEOUT = 300_000

export async function getInterviews() {
  const { data } = await api.get('/interviews')
  return data.items
}

export async function getInterview(sessionId) {
  const { data } = await api.get(`/interviews/${sessionId}`)
  return data
}

export async function startInterview(payload) {
  const { data } = await api.post('/interviews', payload, { timeout: AI_TIMEOUT })
  return data
}

export async function submitInterviewAnswer(sessionId, answer) {
  const { data } = await api.post(`/interviews/${sessionId}/answers`, { answer }, { timeout: AI_TIMEOUT })
  return data
}

export async function finishInterview(sessionId) {
  const { data } = await api.post(`/interviews/${sessionId}/finish`, null, { timeout: AI_TIMEOUT })
  return data
}
