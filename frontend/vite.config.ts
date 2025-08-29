/// <reference types="vitest" />
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv, UserConfig, UserConfigExport } from 'vite'
import { analyzer } from 'vite-bundle-analyzer'
import vue from '@vitejs/plugin-vue'
import importToCDN from 'vite-plugin-cdn-import'
import cdnPackages from './cdn-packages.json'

// https://vitejs.dev/config/
export default ({ mode }: UserConfig): UserConfigExport => {
  const env = loadEnv(mode || 'development', process.cwd())
  const SERVER_PORT = Number(env.VITE_SERVER_PORT ?? '5173')
  const SERVER_ORIGIN = `${env.VITE_SERVER_ORIGIN ?? 'http://0.0.0.0:5173'}`

  return defineConfig({
    plugins: [
      analyzer({ analyzerMode: 'static' }),
      vue({
        // This is needed, or else Vite will try to find image paths (which it wont be able to find because this will be called on the web, not directly)
        template: {
          transformAssetUrls: {
            includeAbsolute: false
          }
        }
      }),
      // Only enable CDN in production
      mode === 'production' &&
        importToCDN({
          modules: cdnPackages
        })
    ].filter(Boolean),
    optimizeDeps: {
      include: ['vue'] // ensure vue is bundled for dev
    },
    css: {
      preprocessorOptions: {
        scss: {
          // Ensure SCSS is processed correctly
          additionalData: ''
        }
      }
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
        // vue: 'vue/dist/vue.esm-bundler.js'
      }
    },
    test: {
      globals: true,
      environment: 'node',
      isolate: false,
      pool: 'threads'
    },
    build: {
      manifest: true,
      outDir: '../internal/static/dist',
      emptyOutDir: true,
      cssCodeSplit: false,
      assetsInlineLimit: 4096,
      rollupOptions: {
        input: {
          viewer: './src/viewer.ts',
          maker: './src/maker.ts',
          styles: './src/styles.ts' // Ensure that all styles are build to style.css. The styles.js should be empty.
        },
        // Tree shaking optimization
        treeshake: {
          moduleSideEffects: false
        }
      }
    },
    server: {
      cors: true,
      host: true,
      port: SERVER_PORT,
      origin: SERVER_ORIGIN,
      watch: {
        usePolling: true
      }
    }
  })
}
