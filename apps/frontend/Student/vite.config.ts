/**
 * vite.config.ts
 *
 * Vite 构建配置文件 (Vite Configuration).
 *
 * 1. 代理 (Proxy): `/app-api` 和 `/static` 转发到本地 yudao 后端 (默认 127.0.0.1:48080)；
 *    `vite preview` 沿用同一套代理。
 * 2. 构建输出 (Build): `dist/` (Docker 镜像与演示部署都从这里取)。
 * 3. 路径别名 (Alias): `@` 指向 src，`@shared` 指向 packages/shared/src。
 */

import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const studentRequire = createRequire(resolve(__dirname, 'package.json'));
const piniaEntry = resolve(dirname(studentRequire.resolve('pinia/package.json')), 'dist/pinia.mjs');
const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:48080';

export default defineConfig(({ mode }) => {
  return {
    server: {
      proxy: {
        '/app-api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/static': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
      fs: {
        allow: [
          '.',
          '../../../packages/shared'
        ]
      }
    },
    base: '/',
    build: {
      // This used to be '../../backend/static' together with
      // `emptyOutDir: true`, which meant a routine `npm run build` deleted the
      // directory the backend serves product images and uploads from
      // (apps/backend/static, including static/menu/*.jpg). The production image
      // already overrides this with `--outDir dist`, so building to dist keeps the
      // local and Docker behaviours identical.
      outDir: 'dist',
      emptyOutDir: true,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'vue-router', 'pinia'],
          }
        }
      },
      minify: 'esbuild',
      sourcemap: mode !== 'production',
    },
    plugins: [
      vue(),
    ],
    resolve: {
      alias: {
        // Shared components otherwise resolve the hoisted Pinia 2 while this
        // app installs Pinia 3, so their stores cannot see the app's provider.
        'pinia': piniaEntry,
        '@': resolve(__dirname, './src'),
        '@shared': resolve(__dirname, '../../../packages/shared/src'),
      },
      dedupe: ['vue'],
    },
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'dingtalk-jsapi'],
    },
  };
});
