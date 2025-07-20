import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Загружаем переменные окружения
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [vue()],
    server: {
      port: parseInt(env.FRONTEND_PORT || '8080'),
      host: '0.0.0.0'
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      }
    },
    build: {
      outDir: 'dist',
      rollupOptions: {
        input: path.resolve(__dirname, 'index.html') 
      }
    },
    define: {
      __DOMAIN__: JSON.stringify(env.DOMAIN || 'localhost'),
      __FRONTEND_URL__: JSON.stringify(env.FRONTEND_URL || 'http://localhost:8080'),
      __BACKEND_URL__: JSON.stringify(env.BACKEND_URL || 'http://localhost:5000/api')
    }
  }
})