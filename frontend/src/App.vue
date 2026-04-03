<template>
  <div class="min-h-100vh flex bg-page max-[900px]:flex-col">
    <aside class="w-[260px] border-r-1 border-r-solid border-border-light py-8 px-6 flex flex-col gap-8 bg-bg shadow-[2px_0_8px_rgba(0,0,0,0.02)] z-10 max-[900px]:w-full max-[900px]:border-r-0 max-[900px]:border-b-1 max-[900px]:border-b-solid max-[900px]:p-5 max-[900px]:gap-5 max-[900px]:shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
      <div class="flex flex-col gap-1 pl-2">
        <strong class="text-[20px] font-700 text-text tracking-[-0.5px]">SmartMeeting</strong>
        <span class="text-primary text-[12px] font-500 tracking-[0.5px] uppercase">AI Meeting Ops</span>
      </div>

      <div v-if="authStore.token" class="flex items-center gap-3 p-4 bg-primary-light-9 rounded-base border-1 border-solid border-primary-light-8 max-[900px]:hidden">
        <el-avatar :size="32">{{ userInitial }}</el-avatar>
        <div class="flex flex-col overflow-hidden">
          <span class="font-600 text-[14px] text-text whitespace-nowrap text-ellipsis overflow-hidden">{{ authStore.currentUser?.full_name || '已登录' }}</span>
          <span class="text-[12px] text-text-secondary mt-[2px]">{{ authStore.currentUser?.role === 'admin' ? '管理员' : '成员' }}</span>
        </div>
      </div>

      <nav v-if="authStore.token" class="flex flex-col gap-2 max-[900px]:flex-row max-[900px]:flex-wrap">
        <RouterLink to="/" class="nav-link">仪表盘</RouterLink>
        <RouterLink to="/meetings" class="nav-link">会议列表</RouterLink>
        <RouterLink to="/tasks" class="nav-link">任务中心</RouterLink>
        <RouterLink to="/hotwords" class="nav-link">热词设置</RouterLink>
        <RouterLink to="/users" class="nav-link">用户管理</RouterLink>
      </nav>

      <div class="mt-auto pt-6 border-t-1 border-t-solid border-border-lighter max-[900px]:mt-0 max-[900px]:border-t-0 max-[900px]:pt-0">
        <el-button v-if="authStore.token" text type="danger" @click="handleLogout">退出登录</el-button>
        <RouterLink v-else to="/login">
          <el-button type="primary" size="small">去登录</el-button>
        </RouterLink>
      </div>
    </aside>
    <main class="flex-1 py-10 px-12 overflow-y-auto bg-page h-100vh max-[900px]:py-6 max-[900px]:px-5 max-[900px]:h-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/authStore";

const authStore = useAuthStore();
const router = useRouter();

const userInitial = computed(() => {
  const name = authStore.currentUser?.full_name || authStore.currentUser?.username || "";
  return name.charAt(0).toUpperCase() || "?";
});

onMounted(async () => {
  if (authStore.token && !authStore.currentUser) {
    await authStore.loadCurrentUser();
  }
});

function handleLogout() {
  authStore.signOut();
  router.push("/login");
}
</script>

<style scoped>
.nav-link {
  color: var(--el-text-color-regular, #606266);
  text-decoration: none;
  padding: 12px 16px;
  border-radius: var(--el-border-radius-small);
  display: block;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: var(--el-fill-color-light, #f5f7fa);
  color: var(--el-text-color-primary, #303133);
}

.nav-link.router-link-active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
</style>
