
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');

    return {
        server: {
            port: 8081,
            proxy: {
                '/api/v1': {
                    target: 'http://127.0.0.1:8000',
                    changeOrigin: true,
                },
                '/static': {
                    target: 'http://127.0.0.1:8000',
                    changeOrigin: true,
                },
            },
            fs: {
                allow: [
                    '.',
                    '../shared'
                ]
            }
        },
        base: mode === 'production' ? '/' : '/',
        build: {
            outDir: '../../backend/static/barista',
            emptyOutDir: true,
            // Code splitting configuration
            rollupOptions: {
                output: {
                    manualChunks: {
                        'vendor': ['vue', 'vue-router', 'pinia'],
                    }
                }
            },
            // Minification
            minify: 'esbuild',
            // Source maps only in dev
            sourcemap: mode !== 'production',
        },
        plugins: [
            vue(),
        ],
        resolve: {
            alias: {
                '@': resolve(__dirname, './src'),
                '@shared': resolve(__dirname, '../shared/src'),
            },
        },
        // Optimize deps
        optimizeDeps: {
            include: ['vue', 'vue-router', 'pinia'],
        },
    };
});
