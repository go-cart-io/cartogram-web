/// <reference types="vitest" />
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv, UserConfig, UserConfigExport } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default ({ mode }: UserConfig): UserConfigExport => {
  const env = loadEnv(mode || 'development', process.cwd())
  const SERVER_PORT = Number(env.VITE_SERVER_PORT ?? '5173')
  const SERVER_ORIGIN = `${env.VITE_SERVER_ORIGIN ?? 'http://localhost:5173'}`

  return defineConfig({
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
    test: {
      globals: true,
      environment: 'jsdom'
    },
    build: {
      manifest: true,
      outDir: '../internal/static/dist',
      emptyOutDir: true,
      cssCodeSplit: false,
      rollupOptions: {
        input: './src/web/main.ts'
      }
    },
    server: {
      port: SERVER_PORT,
      origin: SERVER_ORIGIN
    }
  })
}
