import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "virtual:uno.css";
import { createI18n } from 'vue-i18n';
import zhCN from './locales/zh-CN';

import App from "./App.vue";
import router from "./router";
import "./styles.css";

const i18n = createI18n({
  locale: 'zh-CN',
  messages: {
    'zh-CN': zhCN
  }
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.use(i18n);
app.mount("#app");
