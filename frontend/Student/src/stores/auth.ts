import { defineStore } from 'pinia'
// import axios from 'axios'

interface UserLink {
    username: string
    role: string
    uuid: string
    name?: string
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: sessionStorage.getItem('token') || '',
        user: null as UserLink | null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 'admin'
    },

    actions: {
        setToken(token: string) {
            this.token = token
            sessionStorage.setItem('token', token)
        },

        setUser(user: UserLink) {
            this.user = user
        },

        logout() {
            this.token = ''
            this.user = null
            sessionStorage.removeItem('token')
        }
    }
})
