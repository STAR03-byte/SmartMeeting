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
  display: grid;
  grid-template-columns: 220px 1fr;
  background: radial-gradient(circle at 15% 10%, #fff9ef, #f3f8ff 55%, #f8fbff 100%);
}

.side-rail {
  border-right: 1px solid #dce5ef;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(8px);
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand-block strong {
  font-size: 22px;
  color: #14324f;
}

.brand-block span {
  color: #4c6680;
  font-size: 13px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f0f6ff;
  border-radius: 10px;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #14324f;
}

.user-role {
  font-size: 12px;
  color: #6a8299;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

nav a {
  color: #204668;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 10px;
  display: block;
}

nav a.router-link-active {
  background: #e8f4ff;
  color: #0c4a84;
  font-weight: 500;
}

.side-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #e4ecf5;
}

.main-stage {
  padding: 22px;
  overflow-y: auto;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .side-rail {
    border-right: 0;
    border-bottom: 1px solid #dce5ef;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 12px;
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
}
</style>
