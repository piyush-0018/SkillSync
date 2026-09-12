import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AuthLayout from './layouts/AuthLayout'
import { GuestRoute, ProfileCompleteRoute, ProtectedRoute } from './components/auth/RouteGuards'
import DashboardLayout from './layouts/DashboardLayout'
import MarketingLayout from './layouts/MarketingLayout'
import DashboardPage from './pages/DashboardPage'
import AnalyticsPage from './pages/AnalyticsPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import ProfilePage from './pages/ProfilePage'
import ProfileSetupPage from './pages/ProfileSetupPage'
import RegisterPage from './pages/RegisterPage'
import ResumePage from './pages/ResumePage'
import ResumeAnalysisPage from './pages/ResumeAnalysisPage'
import JobMatchPage from './pages/JobMatchPage'
import SettingsPage from './pages/SettingsPage'
import InterviewResultsPage from './pages/InterviewResultsPage'
import InterviewSessionPage from './pages/InterviewSessionPage'
import InterviewSetupPage from './pages/InterviewSetupPage'

const CareerAssistantPage = lazy(() => import('./pages/CareerAssistantPage'))

export default function App() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route index element={<LandingPage />} />
      </Route>
      <Route element={<GuestRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="profile/setup" element={<ProfileSetupPage />} />
        <Route element={<DashboardLayout />}>
          <Route element={<ProfileCompleteRoute />}>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="dashboard/home" element={<Navigate to="/dashboard" replace />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="career-assistant" element={<Suspense fallback={<div className="surface-panel mx-auto mt-20 h-32 max-w-3xl animate-pulse" aria-label="Loading Career Assistant" />}><CareerAssistantPage /></Suspense>} />
            <Route path="assistant" element={<Navigate to="/career-assistant" replace />} />
            <Route path="interviews" element={<InterviewSetupPage />} />
            <Route path="interviews/new" element={<Navigate to="/interviews" replace />} />
            <Route path="interviews/:sessionId" element={<InterviewSessionPage />} />
            <Route path="interviews/:sessionId/results" element={<InterviewResultsPage />} />
          </Route>
          <Route path="profile" element={<ProfilePage />} />
          <Route path="resume" element={<ResumePage />} />
          <Route path="resume/analysis" element={<ResumeAnalysisPage />} />
          <Route path="job-match" element={<JobMatchPage />} />
          <Route path="jobs" element={<Navigate to="/job-match" replace />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
