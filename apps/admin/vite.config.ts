import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import { createVitePlugins } from './build/vite'
export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd())
  return {
    plugins: createVitePlugins(command === 'build', env),
    resolve: { alias: { '@': resolve(__dirname, 'src') } },
    server: { port: Number(env.VITE_PORT || 8080), strictPort: true, host: '127.0.0.1', proxy: {
      '/admin-api': { target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:48080', changeOrigin: true },
      '/static': { target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:48080', changeOrigin: true }
    } },
    css: { preprocessorOptions: { scss: { additionalData: '@use "@/styles/variables.scss" as *;' } } },
    build: { chunkSizeWarningLimit: 1500 }
  }
})
