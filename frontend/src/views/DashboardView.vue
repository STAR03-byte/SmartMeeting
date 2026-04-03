<template>
  <section class="dashboard-page">
    <header class="hero-header">
      <div class="hero-content">
        <div class="hero-text">
          <h1>{{ greeting }}</h1>
          <p>{{ $t('dashboard.slogan') }}</p>
        </div>
        <div class="hero-actions">
          <router-link to="/meetings?create=1">
            <el-button type="primary" size="large">{{ $t('dashboard.newMeeting') }}</el-button>
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
          <span class="stat-label">{{ $t('dashboard.totalMeetings') }}</span>
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
          <span class="stat-label">{{ $t('meeting.statusOngoing') }}</span>
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
          <span class="stat-label">{{ $t('meeting.statusPlanned') }}</span>
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
          <span class="stat-label">{{ $t('meeting.statusDone') }}</span>
          <span class="stat-value">{{ doneMeetings }}</span>
        </div>
      </el-card>
    </section>

    <section class="dashboard-grid">
      <el-card class="base-card recent-meetings">
        <template #header>
          <div class="panel-header">
            <span>{{ $t('dashboard.recentMeetings') }}</span>
            <router-link to="/meetings">
              <el-button text type="primary" size="small">{{ $t('dashboard.viewAll') }}</el-button>
            </router-link>
          </div>
        </template>

        <el-skeleton v-if="store.loading" rows="3" animated />
        <el-empty v-else-if="store.meetings.length === 0" :description="$t('dashboard.noMeetingData')" />
        <ul v-else class="meeting-list">
          <li v-for="item in recentMeetings" :key="item.id" class="meeting-item">
            <div class="meeting-info">
              <span class="meeting-title">{{ item.title }}</span>
              <el-tag :type="statusTagType(item.status)" size="small">{{ statusLabel(item.status) }}</el-tag>
            </div>
            <div class="meeting-meta">
              <span>{{ formatDate(item.scheduled_start_at) }}</span>
              <el-button size="small" @click="$router.push(`/meetings/${item.id}`)">{{ $t('common.view') }}</el-button>
            </div>
          </li>
        </ul>
      </el-card>

      <el-card class="base-card quick-actions">
        <template #header>
          <div class="panel-header">
            <span>{{ $t('dashboard.quickActions') }}</span>
          </div>
        </template>
        <div class="action-grid">
          <router-link to="/tasks" class="action-item">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
            </div>
            <span>{{ $t('dashboard.taskManagement') }}</span>
          </router-link>
          <router-link to="/users" class="action-item">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <span>{{ $t('dashboard.userManagement') }}</span>
          </router-link>
        </div>
      </el-card>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";

import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { MeetingStatus } from "../api/types";

const { t } = useI18n();
const authStore = useAuthStore();
const store = useMeetingStore();

const greeting = computed(() => {
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? t('dashboard.morning') : hour < 18 ? t('dashboard.afternoon') : t('dashboard.evening');
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
    planned: t('meeting.statusPlanned'),
    ongoing: t('meeting.statusOngoing'),
    done: t('meeting.statusDone'),
    cancelled: t('meeting.statusCancelled'),
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
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.hero-header {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  border-radius: var(--el-border-radius-base);
  padding: 40px;
  box-shadow: var(--el-box-shadow-light);
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.hero-text h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.5px;
}

.hero-text p {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-actions :deep(.el-button) {
  border-radius: var(--el-border-radius-small);
  font-weight: 600;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  transition: all 0.3s ease;
}

.hero-actions :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
}

.hero-actions :deep(.el-button--primary) {
  background: #fff;
  color: var(--el-color-primary);
  border-color: #fff;
}

.hero-actions :deep(.el-button--primary:hover) {
  background: var(--el-color-primary-light-9);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
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
  border-radius: var(--el-border-radius-base);
  border: none;
  background: var(--el-bg-color);
  box-shadow: var(--el-box-shadow-light) !important;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--el-border-radius-small);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.stat-icon--blue {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.stat-icon--green {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-icon--amber {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-icon--purple {
  background: #f4f4f5;
  color: #909399;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
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
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.base-card :deep(.el-card__body) {
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.meeting-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meeting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.meeting-item:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.meeting-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.meeting-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 15px;
}

.meeting-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.action-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  text-decoration: none;
  color: var(--el-text-color-primary);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.action-item:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--el-border-radius-small);
  background: var(--el-bg-color);
  display: grid;
  place-items: center;
  color: var(--el-color-primary);
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.action-item span {
  font-weight: 600;
  font-size: 15px;
}

/* Mobile Adjustments */
@media (max-width: 767px) {
  .hero-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .hero-header {
    padding: 24px;
  }
  
  .meeting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .meeting-meta {
    width: 100%;
    justify-content: space-between;
  }
  
  .base-card :deep(.el-card__header),
  .base-card :deep(.el-card__body) {
    padding: 16px;
  }
}
</style>
