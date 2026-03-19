<template>
  <div class="app-shell">
    <aside class="side-rail">
      <div class="brand-block">
        <strong>SmartMeeting</strong>
        <span>AI Meeting Ops</span>
      </div>
      <nav>
        <RouterLink to="/">会议总览</RouterLink>
        <RouterLink to="/meetings">会议列表</RouterLink>
        <RouterLink to="/tasks">任务中心</RouterLink>
        <RouterLink to="/users">用户管理</RouterLink>
        <RouterLink to="/login">登录</RouterLink>
      </nav>
    </aside>
    <main class="main-stage">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

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
  gap: 20px;
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

nav a {
  color: #204668;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 10px;
  display: block;
  margin-bottom: 6px;
}

nav a.router-link-active {
  background: #e8f4ff;
}

.main-stage {
  padding: 22px;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .side-rail {
    border-right: 0;
    border-bottom: 1px solid #dce5ef;
  }
}
</style>
