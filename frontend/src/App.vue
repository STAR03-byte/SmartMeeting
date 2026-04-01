<template>
  <div class="app-shell">
    <aside class="side-rail">
      <div class="brand-block">
        <strong>SmartMeeting</strong>
        <span>AI Meeting Ops</span>
      </div>

      <div v-if="authStore.token" class="user-info">
        <el-avatar :size="32">{{ userInitial }}</el-avatar>
        <div class="user-meta">
          <span class="user-name">{{ authStore.currentUser?.full_name || '已登录' }}</span>
          <span class="user-role">{{ authStore.currentUser?.role === 'admin' ? '管理员' : '成员' }}</span>
        </div>
      </div>

      <nav v-if="authStore.token">
        <RouterLink to="/">仪表盘</RouterLink>
        <RouterLink to="/meetings">会议列表</RouterLink>
        <RouterLink to="/tasks">任务中心</RouterLink>
        <RouterLink to="/users">用户管理</RouterLink>
      </nav>

      <div class="side-footer">
        <el-button v-if="authStore.token" text type="danger" @click="handleLogout">退出登录</el-button>
        <RouterLink v-else to="/login">
          <el-button type="primary" size="small">去登录</el-button>
        </RouterLink>
      </div>
    </aside>
    <main class="main-stage">
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
.app-shell {
  min-height: 100vh;
  display: flex;
  background: var(--el-bg-color-page);
}

.side-rail {
  width: 260px;
  border-right: 1px solid var(--el-border-color-light, #ebeef5);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  background: var(--el-bg-color);
  box-shadow: 2px 0 8px rgba(0,0,0,0.02);
  z-index: 10;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 8px;
}

.brand-block strong {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary, #303133);
  letter-spacing: -0.5px;
}

.brand-block span {
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-color-primary-light-9);
  border-radius: var(--el-border-radius-base);
  border: 1px solid var(--el-color-primary-light-8, #d9e0f0);
}

.user-meta {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary, #303133);
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.user-role {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  margin-top: 2px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

nav a {
  color: var(--el-text-color-regular, #606266);
  text-decoration: none;
  padding: 12px 16px;
  border-radius: var(--el-border-radius-small);
  display: block;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

nav a:hover {
  background: var(--el-fill-color-light, #f5f7fa);
  color: var(--el-text-color-primary, #303133);
}

nav a.router-link-active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}

.side-footer {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter, #ebeef5);
}

.main-stage {
  flex: 1;
  padding: 40px 48px;
  overflow-y: auto;
  background: var(--el-bg-color-page);
  height: 100vh;
}

@media (max-width: 900px) {
  .app-shell {
    flex-direction: column;
  }

  .side-rail {
    width: 100%;
    border-right: 0;
    border-bottom: 1px solid var(--el-border-color-light, #ebeef5);
    padding: 20px;
    gap: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  }
  
  .user-info {
    display: none; /* Hide on mobile to save space */
  }

  nav {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .side-footer {
    margin-top: 0;
    border-top: 0;
    padding-top: 0;
  }
  
  .main-stage {
    padding: 24px 20px;
    height: auto;
  }
}
</style>
