import { defineStore } from 'pinia'
import { api, setToken, getToken } from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), me: null }),
  actions: {
    setAuth(token, user) {
      this.token = token
      this.me = user || null
      setToken(token)
    },
    async fetchMe() {
      if (!this.token) return null
      this.me = await api.me()
      return this.me
    },
    clear() {
      this.token = ''
      this.me = null
      setToken('')
    }
  }
})
