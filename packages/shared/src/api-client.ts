import axios, { InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// 统一的 Token 键名 (Standardized Token Key)
// These live in the lowest-level module so auth.ts can import them without
// creating a circular dependency.
export const TOKEN_KEY = 'coffee_access_token';
export const ROLE_KEY = 'coffee_user_role';

// API 基础路径
const API_BASE = '/api/v1';

const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor: attach the bearer token automatically
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

/**
 * What to do when the server rejects our credentials with 401.
 *
 * Each app registers its own handler from main.ts. The previous behaviour was a
 * hard `window.location.href = '/login'` baked into this shared module, which is
 * wrong for any app that is not served from the site root - the Barista KDS is
 * built into a sub-path, so an expired barista session was bounced to the
 * Student app's login page.
 */
type UnauthorizedHandler = () => void;

let onUnauthorized: UnauthorizedHandler = () => {
    // Safe default: stay inside the current document's own directory tree
    // instead of assuming the app owns the root path.
    if (!window.location.pathname.endsWith('/login')) {
        window.location.reload();
    }
};

export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
    onUnauthorized = handler;
}

function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(ROLE_KEY);
}

// Response interceptor: centralised auth-expiry handling
apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: any) => {
        const status = error?.response?.status;
        if (status === 401) {
            clearSession();
            onUnauthorized();
        }
        return Promise.reject(error);
    }
);

export default apiClient;
