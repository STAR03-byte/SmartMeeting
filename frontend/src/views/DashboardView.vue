<template>
  <section class="dashboard-page">
    <header class="hero-header">
      <div>
        <h1>SmartMeeting Control Deck</h1>
        <p>{{ greeting }}</p>
      </div>
      <div class="hero-actions">
        <router-link to="/meetings">
          <el-button type="primary">会议管理</el-button>
        </router-link>
        <router-link to="/tasks">
          <el-button>任务中心</el-button>
        </router-link>
        <router-link to="/users">
          <el-button>用户管理</el-button>
        </router-link>
      </div>
    </header>

    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="会议总数" :value="totalMeetings" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="进行中" :value="ongoingMeetings" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="计划中" :value="plannedMeetings" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="已结束" :value="doneMeetings" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="base-card">
      <template #header>
        <div class="panel-header">
          <span>近期会议</span>
          <router-link to="/meetings">
            <el-button text type="primary">查看全部</el-button>
          </router-link>
        </div>
      </template>

      <el-skeleton v-if="store.loading" rows="3" animated />
      <el-empty v-else-if="store.meetings.length === 0" description="暂无会议数据" />
      <el-table v-else :data="recentMeetings" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/meetings/${row.id}`" class="meeting-link">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="计划开始" width="170">
          <template #default="{ row }">
            {{ formatDate(row.scheduled_start_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/meetings/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-skeleton v-if="store.loading" rows="4" animated />
    <div v-else class="meeting-grid">
      <MeetingCard v-for="item in store.meetings" :key="item.id" :meeting="item" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

import MeetingCard from "../components/MeetingCard.vue";
import { useAuthStore } from "../stores/authStore";
import { useMeetingStore } from "../stores/meetingStore";
import type { MeetingStatus } from "../api/types";

const authStore = useAuthStore();
const store = useMeetingStore();

const greeting = computed(() => {
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? "早上好" : hour < 18 ? "下午好" : "晚上好";
  const name = authStore.currentUser?.full_name || "";
  return name ? `${timeGreeting}，${name}！欢迎使用 SmartMeeting` : `${timeGreeting}！欢迎使用 SmartMeeting`;
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
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px;
}

.hero-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 24px;
  padding: 32px 36px;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.hero-header::before {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -100px;
  right: -50px;
}

.hero-header h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.hero-header p {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.hero-actions :deep(.el-button) {
  border-radius: 10px;
  font-weight: 500;
}

.hero-actions :deep(.el-button--primary) {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
}

.hero-actions :deep(.el-button--primary:hover) {
  background: rgba(255, 255, 255, 0.3);
}

.hero-actions :deep(.el-button) {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.stats-row {
  margin-top: 0;
}

.stats-row :deep(.el-col) {
  padding: 0 12px;
}

.stat-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-card :deep(.el-statistic__head) {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.stat-card :deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.base-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.base-card :deep(.el-card__body) {
  padding: 20px 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
}

.meeting-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.meeting-link:hover {
  color: #764ba2;
  text-decoration: none;
}

.meeting-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.meeting-grid :deep(.el-card) {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.meeting-grid :deep(.el-card:hover) {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}
</style>
