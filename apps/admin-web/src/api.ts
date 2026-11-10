import { reactive } from 'vue'

export interface AdminSession {
  id: string
  display_name: string
  avatar_url: string | null
  role: 'editor' | 'publisher' | 'owner'
  expires_at: string
  csrf_token: string
}

export const authState = reactive<{
  loading: boolean
  identity: AdminSession | null
}>({ loading: true, identity: null })

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && authState.identity?.csrf_token) {
    headers.set('X-CSRF-Token', authState.identity.csrf_token)
  }
  const response = await fetch(path, { ...init, method, headers, credentials: 'same-origin' })
  if (response.status === 401) {
    authState.identity = null
    throw new Error('登录已过期')
  }
  const type = response.headers.get('content-type') || ''
  const payload = type.includes('application/json') ? await response.json() : null
  if (!response.ok) {
    const detail = payload?.detail
    throw new Error(typeof detail === 'string' ? detail : '请求失败，请稍后重试')
  }
  return payload as T
}

export async function loadSession() {
  authState.loading = true
  try {
    authState.identity = await api<AdminSession>('/auth/session')
  } catch {
    authState.identity = null
  } finally {
    authState.loading = false
  }
}
