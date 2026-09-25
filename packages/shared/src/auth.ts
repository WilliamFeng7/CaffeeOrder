import { TOKEN_KEY, ROLE_KEY } from './api-client';

export { ROLE_KEY };

// Role is recorded at login time (the backend's token response already includes
// it) so guards and screens can reject a token that belongs to the wrong app.
// Previously each app stored the token as soon as /login answered and only ever
// checked *whether* a token existed: an admin or barista account could obtain a
// live session inside the Student app, and a student could get one inside the
// Admin console, where every call then failed with 403 instead of a clean
// "wrong portal" message.

export const UserRole = {
    STUDENT: 'student',
    BARISTA: 'barista',
    ADMIN: 'admin',
} as const;

export type UserRoleValue = (typeof UserRole)[keyof typeof UserRole];

export const auth = {
    setToken(token: string) {
        sessionStorage.setItem(TOKEN_KEY, token);
    },

    /**
     * Store an authenticated session. Login handlers should prefer this over
     * setToken(): it records the role that the route guards check.
     */
    setSession(token: string, role?: string) {
        sessionStorage.setItem(TOKEN_KEY, token);
        if (role) {
            sessionStorage.setItem(ROLE_KEY, String(role).toLowerCase());
        } else {
            sessionStorage.removeItem(ROLE_KEY);
        }
    },

    getToken(): string | null {
        return sessionStorage.getItem(TOKEN_KEY);
    },

    getRole(): string | null {
        return sessionStorage.getItem(ROLE_KEY);
    },

    /**
     * True only when a token exists AND its recorded role is one of `allowed`.
     * A session with no recorded role is treated as unauthorized rather than
     * assumed acceptable, so a stale session cannot slip past a guard.
     */
    hasRole(...allowed: string[]): boolean {
        const role = this.getRole();
        return !!this.getToken() && !!role && allowed.includes(role.toLowerCase());
    },

    clearToken() {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(ROLE_KEY);
    },

    isLoggedIn(): boolean {
        return !!this.getToken();
    },
};
