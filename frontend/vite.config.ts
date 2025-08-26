/// <reference types="vitest" />
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv, UserConfig, UserConfigExport } from 'vite'
import { analyzer } from 'vite-bundle-analyzer'
import vue from '@vitejs/plugin-vue'
import importToCDN from 'vite-plugin-cdn-import'
import pkg from './package.json'

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
          modules: [
            {
              name: '@popperjs/core',
              var: 'Popper',
              path: 'https://cdn.jsdelivr.net/npm/@popperjs/core@${pkg.dependencies.@popperjs/core}/dist/umd/popper.min.js'
            },
            {
              name: 'bootstrap',
              var: 'bootstrap',
              path: 'https://cdn.jsdelivr.net/npm/bootstrap@${pkg.dependencies.bootstrap}/dist/js/bootstrap.min.js'
            },
            {
              name: 'vue',
              var: 'Vue',
              path: 'https://cdn.jsdelivr.net/npm/vue@${pkg.dependencies.vue}/dist/vue.global.prod.js'
            },
            {
              name: 'd3',
              var: 'd3',
              path: 'https://cdn.jsdelivr.net/npm/d3@${pkg.dependencies.d3}/dist/d3.min.js'
            },
            {
              name: 'vega',
              var: 'vega',
              path: 'https://cdn.jsdelivr.net/npm/vega@${pkg.dependencies.vega}/build/vega.min.js'
            },
            {
              name: 'vega-embed',
              var: 'vegaEmbed',
              path: 'https://cdn.jsdelivr.net/npm/vega-embed@${pkg.dependencies.vega-embed}/build/vega-embed.min.js'
            },
            {
              name: 'vega-tooltip',
              var: 'vegaTooltip',
              path: 'https://cdn.jsdelivr.net/npm/vega-tooltip@${pkg.dependencies.vega-tooltip}'
            }
          ]
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
          'bootstrap-custom': './src/assets/styles.scss'
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
