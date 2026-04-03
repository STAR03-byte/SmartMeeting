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
            <span>{{ $t('transcript.title') }}</span>
            <el-button text @click="$emit('reload')">{{ $t('common.refresh') }}</el-button>
          </div>
        </template>

        <el-empty v-if="store.transcripts.length === 0" :description="$t('transcript.empty')" />
        
        <el-timeline v-else class="grouped-timeline">
          <el-timeline-item
            v-for="(group, gIdx) in groupedTranscripts"
            :key="gIdx"
            :timestamp="formatTimeRange(group.start_time_sec, group.end_time_sec)"
            placement="top"
          >
            <div class="speaker-header">
              <el-tag size="small" type="info">{{ group.speaker_name }}</el-tag>
            </div>
            
            <div 
              v-for="item in group.segments" 
              :key="item.id" 
              class="transcript-row"
              :class="{ playing: isPlaying(item) }"
            >
              <div class="transcript-meta">
                <strong>#{{ item.segment_index }}</strong>
                <span v-if="item.start_time_sec !== null" class="time-range">
                  [{{ formatTime(item.start_time_sec) }} - {{ formatTime(item.end_time_sec) }}]
                </span>
                <el-popconfirm :title="$t('transcript.deleteConfirm')" @confirm="removeTranscript(item.id)">
                  <template #reference>
                    <el-button size="small" type="danger" text>{{ $t('common.delete') }}</el-button>
                  </template>
                </el-popconfirm>
              </div>
              <div class="transcript-content">
                <p>{{ getDisplayText(item) }}</p>
                <el-button 
                  v-if="shouldCollapse(item.content)" 
                  type="primary" 
                  link 
                  size="small" 
                  @click="toggleExpand(item.id)"
                  class="toggle-btn"
                >
                  {{ isExpanded(item.id) ? $t('transcript.collapse') : $t('transcript.expand') }}
                </el-button>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useMeetingStore } from "../../stores/meetingStore";
import { useTranscription } from "../../composables/useTranscription";
import { useI18n } from "vue-i18n";
import type { Transcript } from "../../api/types";

const props = withDefaults(defineProps<{ 
  meetingId: number;
  currentTime?: number;
}>(), {
  currentTime: 0
});

defineEmits<{ (e: 'reload'): void }>();

const store = useMeetingStore();
const { removeTranscript } = useTranscription(props.meetingId);
const { t } = useI18n();

interface GroupedTranscript {
  speaker_name: string;
  start_time_sec: number | null;
  end_time_sec: number | null;
  segments: Transcript[];
}

const groupedTranscripts = computed(() => {
  const groups: GroupedTranscript[] = [];
  let currentGroup: GroupedTranscript | null = null;
  
  for (const transcript of store.transcripts) {
    const speakerName = transcript.speaker_name || transcript.source || t('common.unknown');
    if (!currentGroup || currentGroup.speaker_name !== speakerName) {
      currentGroup = {
        speaker_name: speakerName,
        start_time_sec: transcript.start_time_sec,
        end_time_sec: transcript.end_time_sec,
        segments: [transcript]
      };
      groups.push(currentGroup);
    } else {
      currentGroup.segments.push(transcript);
      if (transcript.end_time_sec !== null) {
        currentGroup.end_time_sec = transcript.end_time_sec;
      }
    }
  }
  return groups;
});

function formatTime(seconds: number | null): string {
  if (seconds === null || isNaN(seconds)) return '--:--';
  const s = Math.floor(seconds);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const mStr = (m % 60).toString().padStart(2, '0');
  const sStr = (s % 60).toString().padStart(2, '0');
  if (h > 0) {
    return `${h}:${mStr}:${sStr}`;
  }
  return `${mStr}:${sStr}`;
}

function formatTimeRange(start: number | null, end: number | null): string {
  return `${formatTime(start)} - ${formatTime(end)}`;
}

const expandedSegments = ref<Set<number>>(new Set());

function toggleExpand(id: number) {
  const newSet = new Set(expandedSegments.value);
  if (newSet.has(id)) {
    newSet.delete(id);
  } else {
    newSet.add(id);
  }
  expandedSegments.value = newSet;
}

function isExpanded(id: number): boolean {
  return expandedSegments.value.has(id);
}

function shouldCollapse(text: string) {
  return text && text.length > 150;
}

function getDisplayText(item: Transcript) {
  if (!shouldCollapse(item.content) || isExpanded(item.id)) {
    return item.content;
  }
  return item.content.slice(0, 150) + '...';
}

function isPlaying(item: Transcript): boolean {
  if (props.currentTime === undefined || props.currentTime === 0) return false;
  const start = item.start_time_sec ?? 0;
  const end = item.end_time_sec ?? Number.MAX_VALUE;
  return props.currentTime >= start && props.currentTime <= end;
}
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

.grouped-timeline {
  padding-left: 2px;
  margin-top: 8px;
}

.speaker-header {
  margin-bottom: 8px;
}

.transcript-row {
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  transition: all 0.2s ease;
  margin-bottom: 8px;
}

.transcript-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.transcript-row.playing {
  background: var(--el-color-primary-light-9);
  border-left: 4px solid var(--el-color-primary);
  border-radius: 4px;
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

.time-range {
  font-family: monospace;
  color: var(--el-text-color-secondary);
}

.transcript-content p {
  margin: 8px 0 4px;
  line-height: 1.7;
  color: var(--el-text-color-primary);
  font-size: 14px;
  white-space: pre-wrap;
}

.toggle-btn {
  margin-top: 4px;
  font-size: 13px;
}
</style>
