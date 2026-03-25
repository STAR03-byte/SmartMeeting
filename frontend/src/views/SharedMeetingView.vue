<template>
  <section class="shared-page" v-loading="loading">
    <el-page-header @back="goHome" content="分享纪要" />

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <el-card v-if="data" class="base-card">
      <div class="header-row">
        <div>
          <h2>{{ data.meeting.title }}</h2>
          <p>{{ data.meeting.description || "暂无描述" }}</p>
          <p class="organizer-line">组织者：{{ data.meeting.organizer.full_name }} · 状态：{{ statusLabel(data.meeting.status) }}</p>
        </div>
      </div>

      <div class="summary-block">{{ data.meeting.summary || "暂无会议摘要" }}</div>
    </el-card>

    <div class="panel-grid">
      <el-card class="base-card">
        <template #header>转写片段</template>
        <el-empty v-if="!data || data.transcripts.length === 0" description="暂无转写内容" />
        <ul v-else class="plain-list">
          <li v-for="item in data.transcripts" :key="item.id" class="transcript-row">
            <strong>#{{ item.segment_index }}</strong>
            <p>{{ item.content }}</p>
          </li>
        </ul>
      </el-card>

      <el-card class="base-card">
        <template #header>任务列表</template>
        <el-empty v-if="!data || data.tasks.length === 0" description="暂无任务" />
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
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getApiErrorMessage } from "../api/client";
import { getSharedMeeting, type SharedMeetingDetail } from "../api/meetings";
import { useAuthStore } from "../stores/authStore";
import { resolveSafeRedirect } from "../utils/redirect";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const error = ref<string | null>(null);
const data = ref<SharedMeetingDetail | null>(null);

function goHome() {
  router.push("/");
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

async function loadSharedMeeting() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await getSharedMeeting(String(route.params.token));
  } catch (err) {
    const message = getApiErrorMessage(err);
    error.value = message;
    if (message === "Invalid token" || message === "User not found") {
      authStore.signOut();
      await router.push({ name: "login", query: { redirect: resolveSafeRedirect(route.fullPath) } });
    }
  } finally {
    loading.value = false;
  }
}

onMounted(loadSharedMeeting);
</script>

<style scoped>
.shared-page { display: flex; flex-direction: column; gap: 16px; }
.base-card { border-radius: 12px; }
.header-row { display: flex; justify-content: space-between; gap: 16px; }
.summary-block { padding: 12px; background: #f7fbff; border-radius: 8px; white-space: pre-wrap; }
.panel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.plain-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.transcript-row, .task-row { padding: 10px 12px; background: #f8fafc; border-radius: 8px; }
.organizer-line { color: #486078; }
@media (max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
</style>
