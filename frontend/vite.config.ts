import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
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
    origin: 'http://localhost:5173'
  }
})
