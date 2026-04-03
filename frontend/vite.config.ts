import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

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
