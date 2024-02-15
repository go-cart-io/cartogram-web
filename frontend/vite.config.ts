import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const SERVER_PORT = `${env.VITE_SERVER_PORT ?? '5173'}`
  const SERVER_ORIGIN = `${env.VITE_SERVER_ORIGIN ?? 'http://localhost:5173'}`

  return {
    plugins: [
      vue({
        // This is needed, or else Vite will try to find image paths (which it wont be able to find because this will be called on the web, not directly)
        template: {
          transformAssetUrls: {
            includeAbsolute: false
          }
        }
      })
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        vue: 'vue/dist/vue.esm-bundler.js'
      }
    },
    build: {
      manifest: true,
      outDir: '../internal/static/dist',
      emptyOutDir: true,
      cssCodeSplit: false,
      rollupOptions: {
        input: './src/main.ts'
      }
    },
    server: {
      port: SERVER_PORT,
      origin: SERVER_ORIGIN
    }
  }
})
