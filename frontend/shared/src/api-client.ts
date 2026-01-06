import axios, { InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// 统一的 Token 键名 (Standardized Token Key)
export const TOKEN_KEY = 'coffee_access_token';

// API 基础路径
const API_BASE = '/api/v1';

const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器: 自动注入 Token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// 响应拦截器: 统一错误处理
apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: any) => {
        // Handle 401 Unauthorized
        if (error.response && error.response.status === 401) {
            sessionStorage.removeItem(TOKEN_KEY);
            // Only redirect if not already on login page to avoid loops
            if (!window.location.href.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;
