import api from './api'

export async function registerUser(payload) {
  const { data } = await api.post('/auth/register', payload)
  return data
}
export async function loginUser(payload) {
  const { data } = await api.post('/auth/login', payload)
  return data
}

export async function getCurrentUser() {
  const { data } = await api.get('/auth/me')
  return data
}

export async function logoutUser() {
  const { data } = await api.post('/auth/logout')
  return data
}

export async function updateUserProfile(payload) {
  const { data } = await api.patch('/users/profile', payload)
  return data
}
