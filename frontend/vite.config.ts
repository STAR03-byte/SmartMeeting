import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";
import { VitePWA } from "vite-plugin-pwa";

const devBackendUrl = process.env.SMARTMEETING_DEV_BACKEND_URL?.trim() || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [
    vue(),
    UnoCSS(),
    AutoImport({
      dts: "./auto-imports.d.ts",
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      dts: "./components.d.ts",
      resolvers: [
        ElementPlusResolver({
          importStyle: "css",
          directives: true,
        }),
      ],
    }),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: false,
      manifest: false,
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/api\/.*/i,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 },
            },
          },
        ],
      },
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ["vue", "vue-router", "pinia"],
        },
      },
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/api": {
        target: devBackendUrl,
        changeOrigin: true,
      },
      "/health": {
        target: devBackendUrl,
        changeOrigin: true,
      }
    }
  }
});
