
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
            port: 8081, // Dedicated port for Barista KDS
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
            outDir: '../../backend/static/barista', // Separate output dir if needed, or just static/barista
            emptyOutDir: true,
        },
        plugins: [vue()],
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url)),
                '@shared': fileURLToPath(new URL('../shared/src', import.meta.url)),
            },
        },
    };
});
