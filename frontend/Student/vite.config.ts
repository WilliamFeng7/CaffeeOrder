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

// ESM 路径解析 (ESM path resolution)
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Vite 配置导出
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');

  return {
    // 开发服务器配置 (Dev server configuration)
    server: {
      proxy: {
        // API 请求代理: 转发到后端 FastAPI
        '/api/v1': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        // 静态资源代理: 确保图片等资源能从后端获取
        '/static': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    // 基础路径: 生产环境使用 /static/ 前缀，开发环境使用 /
    base: mode === 'production' ? '/' : '/',

    // 构建配置 (Build options)
    build: {
      // 输出目录设置为后端的 static 文件夹
      outDir: '../../backend/static',
      // 构建前清空输出目录
      emptyOutDir: true,
    },

    // 插件列表
    plugins: [vue()],

    // 定义全局常量 (Define global constants)
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
    },

    // 路径别名解析 (Resolve configuration)
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '@shared': fileURLToPath(new URL('../shared/src', import.meta.url)),
      },
    },
  };
});
