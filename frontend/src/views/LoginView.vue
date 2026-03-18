<template>
  <section class="login-page">
    <el-card class="login-card">
      <h1>登录 SmartMeeting</h1>
      <p>使用你的会议账号进入系统。</p>

      <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="submit">登录</el-button>
      </el-form>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { getApiErrorMessage } from "../api/client";
import { useAuthStore } from "../stores/authStore";

const authStore = useAuthStore();
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
    await router.push("/");
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
}

.login-card {
  width: min(420px, 100%);
  border-radius: 16px;
}

.login-card h1 {
  margin: 0 0 8px;
}

.login-card p {
  margin: 0 0 18px;
  color: #5a6f84;
}
</style>
