<template>
  <section class="login-page">
    <div class="login-bg-pattern"></div>
    <div class="login-container">
      <div class="login-brand">
        <div class="brand-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#brandGrad)"/>
            <path d="M14 32c0-7.732 6.268-14 14-14s14 6.268 14 14" stroke="white" stroke-width="3" stroke-linecap="round"/>
            <circle cx="24" cy="24" r="4" stroke="white" stroke-width="2"/>
            <defs>
              <linearGradient id="brandGrad" x1="0" y1="0" x2="48" y2="48">
                <stop stop-color="#6366F1"/>
                <stop offset="1" stop-color="#818CF8"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1>SmartMeeting</h1>
        <p>AI 驱动的智能会议系统</p>
      </div>

      <el-card class="login-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form label-position="top" @submit.prevent>
              <el-form-item label="用户名" class="login-form-item">
                <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
              </el-form-item>
              <el-form-item label="密码" class="login-form-item">
                <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password />
              </el-form-item>
              <el-button type="primary" :loading="loading" @click="submit" size="large" class="login-btn">登录</el-button>
            </el-form>

            <div class="login-footer">
              <span>测试账号: logintest / plain-password</span>
            </div>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form label-position="top" @submit.prevent>
              <el-form-item label="用户名" class="login-form-item">
                <el-input v-model="registerForm.username" placeholder="至少3位" size="large" />
              </el-form-item>
              <el-form-item label="邮箱" class="login-form-item">
                <el-input v-model="registerForm.email" placeholder="请输入邮箱" size="large" />
              </el-form-item>
              <el-form-item label="姓名" class="login-form-item">
                <el-input v-model="registerForm.full_name" placeholder="请输入姓名" size="large" />
              </el-form-item>
              <el-form-item label="密码" class="login-form-item">
                <el-input v-model="registerForm.password_hash" type="password" placeholder="至少8位" size="large" show-password />
              </el-form-item>
              <el-form-item label="确认密码" class="login-form-item">
                <el-input v-model="registerConfirmPassword" type="password" placeholder="再次输入密码" size="large" show-password />
              </el-form-item>
              <el-form-item label="角色" class="login-form-item">
                <el-select v-model="registerForm.role" size="large" style="width: 100%">
                  <el-option label="成员" value="member" />
                  <el-option label="管理员" value="admin" />
                </el-select>
              </el-form-item>
              <el-button type="primary" :loading="registerLoading" @click="register" size="large" class="login-btn">注册</el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import AppErrorAlert from "../components/AppErrorAlert.vue";
import { registerUser } from "../api/users";
import { useAuthStore } from "../stores/authStore";
import { notifyApiError } from "../utils/notify";
import { resolveSafeRedirect } from "../utils/redirect";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const activeTab = ref("login");
const loading = ref(false);
const error = ref<string | null>(null);
const registerLoading = ref(false);
const registerError = ref<string | null>(null);

const form = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  email: "",
  full_name: "",
  password_hash: "",
  role: "member" as "admin" | "member",
});

const registerConfirmPassword = ref("");

async function submit() {
  if (!form.username) {
    ElMessage.warning("请输入用户名");
    return;
  }
  if (!form.password) {
    ElMessage.warning("请输入密码");
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    await authStore.signIn(form.username, form.password);
    await router.push(resolveSafeRedirect(route.query.redirect));
  } catch (err) {
    error.value = notifyApiError(err, { prefix: "登录失败" });
  } finally {
    loading.value = false;
  }
}

async function register() {
  if (!registerForm.username || registerForm.username.length < 3) {
    ElMessage.warning("用户名至少需要3个字符");
    return;
  }
  if (!registerForm.email) {
    ElMessage.warning("请输入邮箱地址");
    return;
  }
  if (!registerForm.full_name) {
    ElMessage.warning("请输入姓名");
    return;
  }
  if (!registerForm.password_hash || registerForm.password_hash.length < 8) {
    ElMessage.warning("密码至少需要8个字符");
    return;
  }
  if (registerForm.password_hash !== registerConfirmPassword.value) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }

  registerLoading.value = true;
  registerError.value = null;
  try {
    await registerUser(registerForm);
    ElMessage.success("注册成功，请登录");
    activeTab.value = "login";
  } catch (err) {
    registerError.value = notifyApiError(err, { prefix: "注册失败" });
  } finally {
    registerLoading.value = false;
  }
}
</script>

<style scoped>
:root {
  --primary: #4F46E5;
  --primary-light: #818CF8;
  --primary-dark: #3730A3;
  --accent: #059669;
  --bg: #0F172A;
  --bg-light: #1E293B;
  --card: #1E293B;
  --card-hover: #334155;
  --muted: #334155;
  --border: #475569;
  --text: #F8FAFC;
  --text-muted: #94A3B8;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--bg);
  position: relative;
  overflow: hidden;
}

.login-bg-pattern {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(79, 70, 229, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(56, 189, 248, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  width: min(400px, 100%);
  position: relative;
  z-index: 1;
}

.login-brand {
  text-align: center;
}

.brand-icon {
  margin-bottom: 16px;
}

.brand-icon svg {
  display: block;
  margin: 0 auto;
}

.login-brand h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.5px;
}

.login-brand p {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 15px;
}

.login-card {
  width: 100%;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  background: var(--card);
}

.login-card :deep(.el-card__body) {
  padding: 28px 32px;
}

.login-card :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.login-card :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.login-card :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-muted);
  padding: 0 16px;
}

.login-card :deep(.el-tabs__item.is-active) {
  color: var(--primary);
}

.login-card :deep(.el-tabs__active-bar) {
  height: 3px;
  background: var(--primary);
  border-radius: 2px;
}

.login-form-item :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text);
  font-size: 14px;
  margin-bottom: 8px;
}

.login-form-item :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
  padding: 4px 12px;
}

.login-form-item :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
}

.login-form-item :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) inset;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  background: var(--primary);
  border: none;
  margin-top: 8px;
}

.login-btn:hover {
  background: var(--primary-dark);
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
</style>