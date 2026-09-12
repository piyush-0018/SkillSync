import api from './api'

const ANALYSIS_TIMEOUT = 300_000

export async function getLatestResumeAnalysis() {
  try {
    const { data } = await api.get('/resume-analyses/latest')
    return data
  } catch (error) {
    if (error.response?.status === 404) return null
    throw error
  }
}

export async function getResumeAnalysisHistory() {
  const { data } = await api.get('/resume-analyses')
  return data.items
}

export async function runResumeAnalysis(refresh = false) {
  const { data } = await api.post('/resume-analyses', null, {
    params: { refresh },
    timeout: ANALYSIS_TIMEOUT,
  })
  return data
}
