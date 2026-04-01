import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

const devBackendUrl = process.env.SMARTMEETING_DEV_BACKEND_URL?.trim() || "http://127.0.0.1:8888";

export default defineConfig({
  plugins: [
    vue(),
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
    host: "127.0.0.1",
    port: 5173,
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
