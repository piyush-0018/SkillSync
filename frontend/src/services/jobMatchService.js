import api from './api'

const ANALYSIS_TIMEOUT = 300_000

export async function getJobMatches() {
  const { data } = await api.get('/job-matches')
  return data.items
}

export async function analyzeJobDescription(jobDescription, refresh = false) {
  const { data } = await api.post('/job-matches', { job_description: jobDescription }, {
    params: { refresh },
    timeout: ANALYSIS_TIMEOUT,
  })
  return data
}
