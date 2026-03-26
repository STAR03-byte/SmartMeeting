<template>
  <section class="shared-page" v-loading="loading">
    <el-page-header @back="goHome" content="分享纪要" />

    <el-card v-if="loading && !errorState && !data" class="base-card loading-card">
      <el-skeleton animated :rows="8" />
    </el-card>

    <el-card v-if="errorState" class="base-card state-card" :class="errorState.kind">
      <div class="state-title">{{ errorState.title }}</div>
      <div class="state-message">{{ errorState.message }}</div>
      <div class="error-actions">
        <el-button v-if="errorState.showRetry" size="small" @click="reload">重试</el-button>
        <el-button v-if="errorState.redirectToLogin" size="small" type="primary" @click="goLogin">去登录</el-button>
        <el-button v-if="errorState.showHome" size="small" @click="goHome">返回首页</el-button>
      </div>
    </el-card>

    <el-card v-if="data" class="base-card summary-card">
      <div class="header-row">
        <div>
          <div class="eyebrow">只读分享内容</div>
          <h2 class="summary-title">{{ data.meeting.title }}</h2>
          <p class="summary-desc">{{ data.meeting.description || "暂无描述" }}</p>
          <div class="summary-meta">
            <el-tag size="small" :type="statusType(data.meeting.status)">{{ statusLabel(data.meeting.status) }}</el-tag>
            <span class="organizer-line">组织者：{{ data.meeting.organizer.full_name }}</span>
            <span class="summary-dot">·</span>
            <span>转写 {{ transcriptCount }} 段</span>
            <span class="summary-dot">·</span>
            <span>任务 {{ taskCount }} 条</span>
          </div>
        </div>
      </div>

      <div class="summary-block">
        <div class="summary-block-label">会议摘要</div>
        <div class="summary-block-text">{{ data.meeting.summary || "暂无会议摘要" }}</div>
      </div>
    </el-card>

    <div class="panel-grid">
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>转写片段</span>
            <el-tag size="small" type="info">{{ transcriptCount }} 段</el-tag>
          </div>
        </template>
        <el-empty v-if="!data || data.transcripts.length === 0" description="暂无转写内容，会议录音或上传音频后会在这里显示。" />
        <ul v-else class="plain-list">
          <li v-for="item in data.transcripts" :key="item.id" class="transcript-row">
            <strong>#{{ item.segment_index }}</strong>
            <p>{{ item.content }}</p>
          </li>
        </ul>
      </el-card>

      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>任务列表</span>
            <el-tag size="small" type="info">{{ taskCount }} 条</el-tag>
          </div>
        </template>
        <el-empty v-if="!data || data.tasks.length === 0" description="暂无任务，纪要抽取后会自动显示在这里。" />
        <ul v-else class="plain-list">
          <li v-for="task in data.tasks" :key="task.id" class="task-row">
            <span>{{ task.title }}</span>
            <el-tag size="small" :type="task.status === 'done' ? 'success' : 'warning'">{{ task.status }}</el-tag>
          </li>
        </ul>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getSharedMeeting, type SharedMeetingDetail } from "../api/meetings";
import { useAuthStore } from "../stores/authStore";
import { resolveSafeRedirect } from "../utils/redirect";
import { getSharedMeetingErrorState, type SharedMeetingErrorState } from "../utils/shared-meeting-error";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const errorState = ref<SharedMeetingErrorState | null>(null);
const data = ref<SharedMeetingDetail | null>(null);

const transcriptCount = computed(() => data.value?.transcripts.length ?? 0);
const taskCount = computed(() => data.value?.tasks.length ?? 0);

function goHome() {
  router.push("/");
}

function goLogin() {
  router.push({ name: "login", query: { redirect: resolveSafeRedirect(route.fullPath) } });
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    planned: "计划中",
    ongoing: "进行中",
    done: "已结束",
    cancelled: "已取消",
  };
  return map[status] ?? status;
}

function statusType(status: string): "info" | "success" | "warning" | "danger" {
  if (status === "done") return "success";
  if (status === "ongoing") return "warning";
  if (status === "cancelled") return "danger";
  return "info";
}

async function loadSharedMeeting() {
  loading.value = true;
  errorState.value = null;
  try {
    data.value = await getSharedMeeting(String(route.params.token));
  } catch (err) {
    const state = getSharedMeetingErrorState(err);
    errorState.value = state;
    if (state.redirectToLogin) {
      authStore.signOut();
      await goLogin();
    }
  } finally {
    loading.value = false;
  }
}

async function reload() {
  await loadSharedMeeting();
}

onMounted(loadSharedMeeting);
</script>

<style scoped>
.shared-page { display: flex; flex-direction: column; gap: 16px; }
.base-card { border-radius: 12px; }
.loading-card { min-height: 260px; }
.state-card { padding: 20px; }
.summary-card { border: 1px solid #dbeafe; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); }
.header-row { display: flex; justify-content: space-between; gap: 16px; }
.eyebrow { color: #2563eb; font-size: 12px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }
.summary-title { margin: 4px 0 8px; font-size: 26px; line-height: 1.3; }
.summary-desc { margin: 0 0 12px; color: #475569; }
.summary-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; color: #64748b; }
.summary-dot { color: #cbd5e1; }
.summary-block { margin-top: 16px; padding: 16px; background: #eff6ff; border-radius: 12px; border: 1px solid #dbeafe; }
.summary-block-label { font-size: 12px; font-weight: 600; color: #2563eb; margin-bottom: 8px; }
.summary-block-text { white-space: pre-wrap; line-height: 1.7; color: #0f172a; }
.panel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; }
.plain-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.transcript-row, .task-row { padding: 10px 12px; background: #f8fafc; border-radius: 8px; }
.transcript-row p { margin: 4px 0 0; line-height: 1.65; }
.organizer-line { color: #486078; }
.state-title { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
.state-message { color: #475569; margin-bottom: 12px; }
.error-actions { display: flex; gap: 8px; margin-top: 12px; }
.state-card.auth { border-left: 4px solid #409eff; }
.state-card.not_found { border-left: 4px solid #f59e0b; }
.state-card.unknown { border-left: 4px solid #ef4444; }
@media (max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
</style>
