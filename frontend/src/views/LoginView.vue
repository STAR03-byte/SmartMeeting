<template>
  <section class="login-page">
    <div class="login-container">
      <div class="login-brand">
        <h1>SmartMeeting</h1>
        <p>AI 驱动的智能会议系统</p>
      </div>

      <el-card class="login-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
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
              <span>账号: logintest / plain-password</span>
            </div>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <p class="login-hint">创建新账号开始使用智能会议系统</p>

            <AppErrorAlert :error="registerError" :closable="false" />

            <el-form label-position="top" @submit.prevent>
              <el-form-item label="用户名">
                <el-input v-model="registerForm.username" placeholder="请输入用户名（至少3位）" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" prefix-icon="Message" size="large" />
              </el-form-item>
              <el-form-item label="姓名">
                <el-input v-model="registerForm.full_name" placeholder="请输入姓名" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="registerForm.password_hash" type="password" show-password placeholder="请输入密码（至少8位）" prefix-icon="Lock" size="large" />
              </el-form-item>
              <el-form-item label="确认密码">
                <el-input v-model="registerConfirmPassword" type="password" show-password placeholder="请再次输入密码" prefix-icon="Lock" size="large" />
              </el-form-item>
              <el-form-item label="角色">
                <el-select v-model="registerForm.role" size="large" style="width: 100%">
                  <el-option label="成员" value="member" />
                  <el-option label="管理员" value="admin" />
                </el-select>
              </el-form-item>
              <el-button type="primary" :loading="registerLoading" @click="register" size="large" style="width: 100%">注册</el-button>
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
    form.username = registerForm.username;
    registerForm.username = "";
    registerForm.email = "";
    registerForm.full_name = "";
    registerForm.password_hash = "";
    registerConfirmPassword.value = "";
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -200px;
  right: -200px;
  animation: float 6s ease-in-out infinite;
}

.login-page::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 50%;
  bottom: -150px;
  left: -150px;
  animation: float 8s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 30px); }
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  width: min(440px, 100%);
  position: relative;
  z-index: 1;
}

.login-brand {
  text-align: center;
}

.login-brand h1 {
  margin: 0;
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.login-brand p {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 18px;
  font-weight: 300;
}

.login-card {
  width: 100%;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.login-card :deep(.el-card__body) {
  padding: 32px 40px;
}

.login-card :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.login-card :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.login-card :deep(.el-tabs__item) {
  font-size: 17px;
  font-weight: 600;
  color: #606266;
  transition: all 0.3s;
}

.login-card :deep(.el-tabs__item.is-active) {
  color: #667eea;
  font-size: 18px;
}

.login-card :deep(.el-tabs__active-bar) {
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
}

.login-hint {
  margin: 0 0 24px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.login-form-item :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

.login-form-item :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.3s;
}

.login-form-item :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.login-form-item :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.login-card :deep(.el-button--primary) {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s;
  margin-top: 8px;
}

.login-card :deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: #909399;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.login-footer span {
  background: #f5f7fa;
  padding: 6px 16px;
  border-radius: 20px;
}
</style>