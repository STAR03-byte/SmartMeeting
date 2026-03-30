<template>
  <section class="login-page">
    <div class="login-container">
      <div class="login-brand">
        <h1>SmartMeeting</h1>
        <p>AI 驱动的智能会议系统</p>
      </div>

      <el-card class="login-card">
        <h2>登录</h2>
        <p class="login-hint">使用你的会议账号进入系统</p>

        <AppErrorAlert :error="error" :closable="false" />

        <el-form label-position="top" @submit.prevent>
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" prefix-icon="Lock" size="large" />
          </el-form-item>
          <el-button type="primary" :loading="loading" @click="submit" size="large" style="width: 100%">登录</el-button>
        </el-form>

        <div class="login-footer">
          <span>默认账号: alice_admin / admin123</span>
        </div>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getApiErrorMessage } from "../api/client";
import AppErrorAlert from "../components/AppErrorAlert.vue";
import { useAuthStore } from "../stores/authStore";
import { resolveSafeRedirect } from "../utils/redirect";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const loading = ref(false);
const error = ref<string | null>(null);

const form = reactive({
  username: "",
  password: "",
});

async function submit() {
  loading.value = true;
  error.value = null;
  try {
    await authStore.signIn(form.username, form.password);
    await router.push(resolveSafeRedirect(route.query.redirect));
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at 30% 20%, #e8f4ff, #f8fbff 60%, #fff9ef);
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  width: min(420px, 100%);
}

.login-brand {
  text-align: center;
}

.login-brand h1 {
  margin: 0;
  font-size: 36px;
  color: #0c4a84;
  letter-spacing: 1px;
}

.login-brand p {
  margin: 8px 0 0;
  color: #5a6f84;
  font-size: 16px;
}

.login-card {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.login-card h2 {
  margin: 0 0 4px;
  font-size: 24px;
  color: #14324f;
}

.login-hint {
  margin: 0 0 20px;
  color: #5a6f84;
  font-size: 14px;
}

.login-footer {
  margin-top: 16px;
  text-align: center;
  font-size: 12px;
  color: #8aa0b8;
}
</style>
