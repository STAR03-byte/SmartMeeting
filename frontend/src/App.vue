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
  background: #0F172A;
}

.side-rail {
  border-right: 1px solid #1E293B;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #1E293B;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand-block strong {
  font-size: 22px;
  color: #fff;
}

.brand-block span {
  color: #6366F1;
  font-size: 13px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #334155;
  border-radius: 10px;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #F8FAFC;
}

.user-role {
  font-size: 12px;
  color: #94A3B8;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

nav a {
  color: #94A3B8;
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 10px;
  display: block;
  transition: all 0.2s;
}

nav a:hover {
  background: #334155;
  color: #F8FAFC;
}

nav a.router-link-active {
  background: #6366F1;
  color: #fff;
  font-weight: 500;
}

.side-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #334155;
}

.main-stage {
  padding: 22px;
  overflow-y: auto;
  background: #0F172A;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .side-rail {
    border-right: 0;
    border-bottom: 1px solid #334155;
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
