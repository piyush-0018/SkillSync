import api from './api'

const RESPONSE_TIMEOUT = 300_000

export async function getAssistantConversations() {
  const { data } = await api.get('/career-assistant/conversations', { params: { limit: 30 } })
  return data.items
}

export async function getAssistantConversation(conversationId) {
  const { data } = await api.get(`/career-assistant/conversations/${conversationId}`)
  return data
}

export async function sendAssistantMessage(conversationId, content) {
  const { data } = await api.post('/career-assistant/messages', {
    conversation_id: conversationId,
    content,
  }, { timeout: RESPONSE_TIMEOUT })
  return data
}

export async function deleteAssistantConversation(conversationId) {
  await api.delete(`/career-assistant/conversations/${conversationId}`)
}
