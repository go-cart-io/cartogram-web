import { fileURLToPath } from 'node:url'
import { defineConfig, configDefaults } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    isolate: false,
    pool: 'threads',
    exclude: [...configDefaults.exclude, 'e2e/**'],
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
