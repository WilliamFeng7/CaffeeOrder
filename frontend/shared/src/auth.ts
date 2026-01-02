import { TOKEN_KEY } from './api-client';

export const auth = {
    setToken(token: string) {
        sessionStorage.setItem(TOKEN_KEY, token);
    },
    getToken(): string | null {
        return sessionStorage.getItem(TOKEN_KEY);
    },
    clearToken() {
        sessionStorage.removeItem(TOKEN_KEY);
    },
    isLoggedIn(): boolean {
        return !!this.getToken();
    }
};
