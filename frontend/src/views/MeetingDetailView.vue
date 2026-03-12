<template>
  <section class="detail-page" v-loading="store.loading">
    <el-page-header @back="goBack" content="会议详情" />

    <el-card v-if="store.currentMeeting" class="base-card">
      <h2>{{ store.currentMeeting.title }}</h2>
      <p>{{ store.currentMeeting.description || "暂无描述" }}</p>
      <div class="action-row">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept="audio/*"
          :on-change="onFilePicked"
        >
          <el-button type="primary">上传音频并转写</el-button>
        </el-upload>
        <el-button type="success" @click="runPostprocess">生成纪要与任务</el-button>
      </div>
      <p class="summary-block">{{ store.currentMeeting.summary || "暂无会议摘要" }}</p>
    </el-card>

    <div class="panel-grid">
      <el-card class="base-card">
        <template #header>转写片段</template>
        <ul class="plain-list">
          <li v-for="item in store.transcripts" :key="item.id">
            #{{ item.segment_index }} {{ item.content }}
          </li>
        </ul>
      </el-card>

      <el-card class="base-card">
        <template #header>任务列表</template>
        <ul class="plain-list">
          <li v-for="task in store.tasks" :key="task.id">
            {{ task.title }} | {{ task.status }} | {{ task.priority }}
          </li>
        </ul>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useMeetingStore } from "../stores/meetingStore";

const store = useMeetingStore();
const route = useRoute();
const router = useRouter();
const meetingId = Number(route.params.id);

onMounted(async () => {
  if (!Number.isFinite(meetingId)) {
    ElMessage.error("会议ID无效");
    router.push("/");
    return;
  }
  await store.fetchMeetingDetail(meetingId);
});

function goBack() {
  router.push("/");
}

async function onFilePicked(file: { raw?: File }) {
  if (!file.raw) {
    return;
  }
  await store.uploadAudioAndTranscribe(meetingId, file.raw);
  ElMessage.success("音频上传并转写完成");
}

async function runPostprocess() {
  await store.runPostprocess(meetingId);
  ElMessage.success("已生成会议纪要与任务");
}
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.base-card {
  border-radius: 12px;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.action-row {
  display: flex;
  gap: 10px;
  margin: 14px 0;
}

.summary-block {
  margin: 0;
  padding: 10px;
  background: #f7fbff;
  border-radius: 8px;
  border: 1px solid #d7e6f5;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 900px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}
</style>
