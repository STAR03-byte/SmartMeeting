<template>
  <section class="dashboard-page">
    <header class="hero-header">
      <div class="hero-content">
        <div class="hero-text">
          <h1>{{ greeting }}</h1>
          <p>高效会议管理，智能任务追踪</p>
        </div>
        <div class="hero-actions">
          <router-link to="/meetings">
            <el-button type="primary" size="large">会议管理</el-button>
          </router-link>
          <router-link to="/tasks">
            <el-button size="large">任务中心</el-button>
          </router-link>
          <router-link to="/users">
            <el-button size="large">用户管理</el-button>
          </router-link>
        </div>
      </div>
    </header>

    <section class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <path d="M16 2v4M8 2v4M3 10h18"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">会议总数</span>
          <span class="stat-value">{{ totalMeetings }}</span>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon stat-icon--green">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">进行中</span>
          <span class="stat-value">{{ ongoingMeetings }}</span>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon stat-icon--amber">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <path d="M16 2v4M8 2v4M3 10h18"/>
            <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">计划中</span>
          <span class="stat-value">{{ plannedMeetings }}</span>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon stat-icon--purple">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <path d="M22 4L12 14.01l-3-3"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">已结束</span>
          <span class="stat-value">{{ doneMeetings }}</span>
        </div>
      </el-card>
    </section>

    <section class="dashboard-grid">
      <el-card class="base-card recent-meetings">
        <template #header>
          <div class="panel-header">
            <span>近期会议</span>
            <router-link to="/meetings">
              <el-button text type="primary" size="small">查看全部</el-button>
            </router-link>
          </div>
        </template>

        <el-skeleton v-if="store.loading" rows="3" animated />
        <el-empty v-else-if="store.meetings.length === 0" description="暂无会议数据" />
        <ul v-else class="meeting-list">
          <li v-for="item in recentMeetings" :key="item.id" class="meeting-item">
            <div class="meeting-info">
              <span class="meeting-title">{{ item.title }}</span>
              <el-tag :type="statusTagType(item.status)" size="small">{{ statusLabel(item.status) }}</el-tag>
            </div>
            <div class="meeting-meta">
              <span>{{ formatDate(item.scheduled_start_at) }}</span>
              <el-button size="small" @click="$router.push(`/meetings/${item.id}`)">查看</el-button>
            </div>
          </li>
        </ul>
      </el-card>

      <el-card class="base-card quick-actions">
        <template #header>
          <div class="panel-header">
            <span>快捷操作</span>
          </div>
        </template>
        <div class="action-grid">
          <router-link to="/meetings?status=planned" class="action-item">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <path d="M16 2v4M8 2v4M3 10h18"/>
              </svg>
            </div>
            <span>创建会议</span>
          </router-link>
          <router-link to="/tasks" class="action-item">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
            </div>
            <span>任务管理</span>
          </router-link>
          <router-link to="/users" class="action-item">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <span>用户管理</span>
          </router-link>
        </div>
      </el-card>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { MeetingStatus } from "../api/types";

const authStore = useAuthStore();
const store = useMeetingStore();

const greeting = computed(() => {
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? "早上好" : hour < 18 ? "下午好" : "晚上好";
  const name = authStore.currentUser?.full_name || "";
  return name ? `${timeGreeting}，${name}` : `${timeGreeting}！`;
});

const totalMeetings = computed(() => store.meetingsTotal || store.meetings.length);
const ongoingMeetings = computed(() => store.meetings.filter((m) => m.status === "ongoing").length);
const plannedMeetings = computed(() => store.meetings.filter((m) => m.status === "planned").length);
const doneMeetings = computed(() => store.meetings.filter((m) => m.status === "done").length);

const recentMeetings = computed(() =>
  [...store.meetings]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
);

function statusLabel(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    planned: "计划中",
    ongoing: "进行中",
    done: "已结束",
    cancelled: "已取消",
  };
  return map[status] ?? status;
}

function statusTagType(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    planned: "",
    ongoing: "success",
    done: "info",
    cancelled: "danger",
  };
  return map[status] ?? "";
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}

onMounted(async () => {
  await store.fetchMeetings({ limit: 100, offset: 0 });
});
</script>

<style scoped>
:root {
  --primary: #6366F1;
  --primary-light: #818CF8;
  --bg: #0F172A;
  --bg-light: #1E293B;
  --card: #1E293B;
  --card-hover: #334155;
  --border: #334155;
  --text: #F8FAFC;
  --text-muted: #94A3B8;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-header {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #6366F1 100%);
  border-radius: var(--radius-lg);
  padding: 32px;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.hero-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.hero-text p {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-actions :deep(.el-button) {
  border-radius: var(--radius-sm);
  font-weight: 600;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff;
}

.hero-actions :deep(.el-button--primary) {
  background: #fff;
  color: var(--primary);
  border-color: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--card);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.stat-icon--blue {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
}

.stat-icon--green {
  background: rgba(34, 197, 94, 0.1);
  color: #22C55E;
}

.stat-icon--amber {
  background: rgba(245, 158, 11, 0.1);
  color: #F59E0B;
}

.stat-icon--purple {
  background: rgba(139, 92, 246, 0.1);
  color: #8B5CF6;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.base-card {
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.base-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.base-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--text);
}

.meeting-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meeting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.meeting-item:hover {
  background: var(--border);
}

.meeting-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meeting-title {
  font-weight: 500;
  color: var(--text);
}

.meeting-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
}

.action-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--text);
  transition: all 0.2s;
}

.action-item:hover {
  background: var(--primary);
  color: #fff;
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: var(--card);
  display: grid;
  place-items: center;
}

.action-item:hover .action-icon {
  background: rgba(255, 255, 255, 0.2);
}

.action-item span {
  font-weight: 500;
}
</style>