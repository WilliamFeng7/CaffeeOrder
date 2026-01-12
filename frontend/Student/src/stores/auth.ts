import { defineStore } from 'pinia'
import { auth } from '@shared/auth'

interface UserLink {
    username: string
    role: string
    uuid: string
    name?: string
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: auth.getToken() || '',
        user: null as UserLink | null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 'admin'
    },

    actions: {
        setToken(token: string) {
            this.token = token
            auth.setToken(token)
        },

        setUser(user: UserLink) {
            this.user = user
        },

        logout() {
            this.token = ''
            this.user = null
            auth.clearToken()
        }
    }
})
