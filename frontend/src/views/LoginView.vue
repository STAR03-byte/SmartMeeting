<template>
  <section class="login-page">
    <div class="login-bg">
      <div class="login-bg-gradient"></div>
      <div class="login-bg-grid"></div>
    </div>
    
    <div class="login-container">
      <div class="login-brand">
        <div class="brand-icon">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <defs>
              <linearGradient id="brandGrad" x1="0" y1="0" x2="56" y2="56">
                <stop offset="0%" stop-color="var(--el-color-primary)"/>
                <stop offset="100%" stop-color="var(--el-color-primary-light-3)"/>
              </linearGradient>
            </defs>
            <rect width="56" height="56" rx="16" fill="url(#brandGrad)"/>
            <path d="M16 38c0-9.941 8.059-18 18-18s18 8.059 18 18" stroke="white" stroke-width="3.5" stroke-linecap="round" opacity="0.9"/>
            <circle cx="28" cy="28" r="5" fill="white"/>
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
              <span>测试: logintest / plain-password</span>
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
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--el-bg-color-page);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-bg-gradient {
  position: absolute;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at 30% 20%, var(--el-color-primary-light-9) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, var(--el-color-primary-light-8) 0%, transparent 50%);
}

.login-bg-grid {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(var(--el-border-color-lighter) 1px, transparent 1px),
    linear-gradient(90deg, var(--el-border-color-lighter) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.5;
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 36px;
  width: min(400px, 100%);
  position: relative;
  z-index: 1;
}

.login-brand {
  text-align: center;
}

.brand-icon {
  margin-bottom: 20px;
}

.brand-icon svg {
  display: block;
  margin: 0 auto;
  filter: drop-shadow(var(--el-box-shadow-light));
}

.login-brand h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: -0.5px;
}

.login-brand p {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 15px;
}

.login-card {
  width: 100%;
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
  background: var(--el-bg-color);
}

.login-card :deep(.el-card__body) {
  padding: 32px 36px;
}

.login-card :deep(.el-tabs__header) {
  margin-bottom: 28px;
}

.login-card :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: var(--el-border-color-lighter);
}

.login-card :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  padding: 0 20px;
}

.login-card :deep(.el-tabs__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 600;
}

.login-card :deep(.el-tabs__active-bar) {
  height: 2px;
  background: var(--el-color-primary);
  border-radius: 2px;
}

.login-form-item :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-size: 14px;
  margin-bottom: 8px;
}

.login-form-item :deep(.el-input__wrapper) {
  border-radius: var(--el-border-radius-small);
  box-shadow: 0 0 0 1px var(--el-border-color-light) inset;
  padding: 4px 14px;
  background-color: var(--el-fill-color-lighter);
}

.login-form-item :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary-light-5) inset;
}

.login-form-item :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
  background-color: var(--el-bg-color);
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  border-radius: var(--el-border-radius-small);
  background: var(--el-color-primary);
  border: none;
  margin-top: 12px;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--el-color-primary-light-7);
  background: var(--el-color-primary-light-3);
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>