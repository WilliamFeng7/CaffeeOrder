/**
 * vite.config.ts
 * 
 * Vite 构建配置文件 (Vite Configuration).
 * 
 * 主要功能 (Core Features):
 * 1. 代理配置 (Proxy): 将前端 `/api` 和 `/static` 请求转发到后端 FastAPI 服务 (127.0.0.1:8000)，解决跨域问题。
 * 2. 构建输出 (Build): 将打包后的静态文件输出到 `../../backend/static` 目录，方便后端统一托管。
 * 3. 插件集成 (Plugins): 使用 @vitejs/plugin-vue 支持 Vue 3 单文件组件。
 * 4. 路径别名 (Alias): 配置 `@` 指向项目根目录，方便模块导入。
 */

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
          '../../../packages/shared'
        ]
      }
    },
    base: mode === 'production' ? '/' : '/',
    build: {
      outDir: '../../backend/static',
      emptyOutDir: true,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'vue-router', 'pinia', 'axios'],
          }
        }
      },
      minify: 'esbuild',
      sourcemap: mode !== 'production',
    },
    plugins: [
      vue(),
    ],
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
        '@shared': resolve(__dirname, '../../../packages/shared/src'),
      },
    },
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'axios'],
    },
  };
});
