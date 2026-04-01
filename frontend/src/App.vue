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
  grid-template-columns: 240px 1fr;
  background: #F8FAFC;
}

.side-rail {
  border-right: 1px solid #E2E8F0;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #FFFFFF;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand-block strong {
  font-size: 22px;
  font-weight: 800;
  color: #0F172A;
}

.brand-block span {
  color: #4F46E5;
  font-size: 13px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #F1F5F9;
  border-radius: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #0F172A;
}

.user-role {
  font-size: 12px;
  color: #64748B;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

nav a {
  color: #64748B;
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 10px;
  display: block;
  font-weight: 500;
  transition: all 0.2s;
}

nav a:hover {
  background: #F1F5F9;
  color: #0F172A;
}

nav a.router-link-active {
  background: #4F46E5;
  color: #fff;
  font-weight: 600;
}

.side-footer {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #E2E8F0;
}

.main-stage {
  padding: 24px;
  overflow-y: auto;
  background: #F8FAFC;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .side-rail {
    border-right: 0;
    border-bottom: 1px solid #E2E8F0;
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
