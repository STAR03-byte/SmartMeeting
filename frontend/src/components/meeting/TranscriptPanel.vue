<template>
  <el-skeleton animated :loading="store.loading">
    <template #template>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <el-skeleton-item variant="text" style="width: 64px; height: 24px;" />
            <el-skeleton-item variant="text" style="width: 32px; height: 24px;" />
          </div>
        </template>
        <div class="plain-list">
          <div v-for="i in 3" :key="i" class="transcript-row" style="background: var(--el-fill-color-lighter); border-radius: var(--el-border-radius-small);">
            <div style="display: flex; gap: 12px; margin-bottom: 12px;">
              <el-skeleton-item variant="text" style="width: 24px;" />
              <el-skeleton-item variant="text" style="width: 64px;" />
            </div>
            <el-skeleton-item variant="text" style="width: 100%; margin-bottom: 8px;" />
            <el-skeleton-item variant="text" style="width: 80%;" />
          </div>
        </div>
      </el-card>
    </template>
    <template #default>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>转写片段</span>
            <el-button text @click="$emit('reload')">刷新</el-button>
          </div>
        </template>

        <el-empty v-if="store.transcripts.length === 0" description="暂无转写内容" />
        <ul v-else class="plain-list">
          <li v-for="item in store.transcripts" :key="item.id" class="transcript-row">
            <div class="transcript-meta">
              <strong>#{{ item.segment_index }}</strong>
              <span>{{ item.speaker_name || item.source }}</span>
              <el-popconfirm title="确认删除该转写片段？" @confirm="removeTranscript(item.id)">
                <template #reference>
                  <el-button size="small" type="danger" text>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
            <p>{{ item.content }}</p>
          </li>
        </ul>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { useMeetingStore } from "../../stores/meetingStore";
import { useTranscription } from "../../composables/useTranscription";

const props = defineProps<{ meetingId: number }>();
defineEmits<{ (e: 'reload'): void }>();

const store = useMeetingStore();
const { removeTranscript } = useTranscription(props.meetingId);
</script>

<style scoped>
.base-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0;
  flex: 1;
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
  background: var(--el-bg-color);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.base-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
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

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.transcript-row {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.transcript-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.transcript-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.transcript-meta strong {
  color: var(--el-color-primary);
}

.transcript-row p {
  margin: 12px 0 0;
  line-height: 1.7;
  color: var(--el-text-color-primary);
  font-size: 14px;
}
</style>