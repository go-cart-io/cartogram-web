import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
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
