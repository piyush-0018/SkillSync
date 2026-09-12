import { useCallback, useEffect, useState } from 'react'
import { getApiErrorMessage } from '../services/api'
import { getCareerAnalytics } from '../services/analyticsService'

export default function useCareerAnalytics() {
  const [analytics, setAnalytics] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      setAnalytics(await getCareerAnalytics())
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Could not load career analytics.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return { analytics, error, isLoading, refresh }
}
