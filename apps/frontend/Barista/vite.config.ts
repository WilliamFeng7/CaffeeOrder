import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 后端不在 48080 时，用 VITE_PROXY_TARGET 指过去（和管理端同一个变量）。
const backend = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:48080';

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
            '@shared': fileURLToPath(new URL('../../../packages/shared/src', import.meta.url)),
        },
    },
    server: {
        port: 8081,
        strictPort: true,
        proxy: {
            '/admin-api': { target: backend, changeOrigin: true },
        },
        fs: {
            allow: ['.', '../../../packages/shared'],
        },
    },
    preview: {
        port: 8081,
        strictPort: true,
        proxy: {
            '/admin-api': { target: backend, changeOrigin: true },
        },
    },
});
