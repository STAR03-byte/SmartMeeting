import { defineConfig, presetUno } from "unocss";

export default defineConfig({
  presets: [presetUno()],
  shortcuts: {
    "wb-surface": "rounded-base bg-bg shadow-light text-text",
    "wb-muted": "text-text-secondary bg-page",
    "wb-drawer-header": "px-6 py-4 border-b border-border-light m-0 font-semibold text-lg text-text",
    "wb-drawer-body": "p-6 text-text overflow-y-auto bg-bg",
    "wb-drawer-footer": "px-6 py-4 border-t border-border-light bg-fill-light",
    "wb-context-menu": "absolute z-50 bg-bg border border-border-light rounded-base shadow-light p-1 outline-none select-none",
    "wb-context-menu-item": "px-3 py-2 text-sm text-text hover:bg-fill-light cursor-pointer rounded-sm transition-colors flex items-center gap-2",
  },
  theme: {
    spacing: {
      px: "1px",
      0: "0px",
      1: "0.25rem",
      2: "0.5rem",
      3: "0.75rem",
      4: "1rem",
      5: "1.25rem",
      6: "1.5rem",
      8: "2rem",
      10: "2.5rem",
      12: "3rem",
    },
    colors: {
      primary: "var(--el-color-primary)",
      "primary-hover": "var(--el-color-primary-light-3)",
      "primary-light-8": "var(--el-color-primary-light-8, #d9e0f0)",
      "primary-light-9": "var(--el-color-primary-light-9)",
      text: "var(--el-text-color-primary)",
      "text-secondary": "var(--el-text-color-secondary)",
      "text-muted": "var(--el-text-color-regular)",
      bg: "var(--el-bg-color)",
      page: "var(--el-bg-color-page)",
      border: "var(--el-border-color)",
      "border-light": "var(--el-border-color-light, #ebeef5)",
      "border-lighter": "var(--el-border-color-lighter, #ebeef5)",
      "fill-light": "var(--el-fill-color-light, #f5f7fa)",
    },
    borderRadius: {
      sm: "var(--el-border-radius-small)",
      base: "var(--el-border-radius-base)",
      round: "var(--el-border-radius-round)",
    },
    boxShadow: {
      light: "var(--el-box-shadow-light)",
    },
    fontSize: {
      base: ["var(--el-font-size-base)", { lineHeight: "1.5" }],
      sm: ["0.875rem", { lineHeight: "1.5" }],
      lg: ["1.125rem", { lineHeight: "1.5" }],
    },
    fontFamily: {
      sans: 'var(--el-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif)',
    },
  },
});
