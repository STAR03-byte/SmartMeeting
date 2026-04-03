<template>
  <div class="summary-container">
    <div v-if="hasStructuredSummary" class="structured-summary">
      <div class="summary-section" v-if="structuredSummary.agenda.length > 0">
        <div class="section-header">
          <el-icon><Document /></el-icon>
          <span class="section-title">议程</span>
        </div>
        <div class="section-content">
          <div
            v-for="(item, index) in structuredSummary.agenda"
            :key="'agenda-' + index"
            class="agenda-item"
          >
            <div class="item-topic">{{ item.topic }}</div>
            <div v-if="item.speaker" class="item-speaker">
              <el-tag size="small" type="info">{{ item.speaker }}</el-tag>
            </div>
            <ul v-if="item.key_points.length > 0" class="item-points">
              <li v-for="(point, pIndex) in item.key_points" :key="'point-' + pIndex">
                {{ point }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="summary-section" v-if="structuredSummary.resolutions.length > 0">
        <div class="section-header">
          <el-icon><CircleCheck /></el-icon>
          <span class="section-title">决议</span>
        </div>
        <div class="section-content">
          <div
            v-for="(item, index) in structuredSummary.resolutions"
            :key="'resolution-' + index"
            class="resolution-item"
          >
            <div class="item-decision">{{ item.decision }}</div>
            <div v-if="item.proposer" class="item-meta">
              <span class="meta-label">提议人:</span>
              <span class="meta-value">{{ item.proposer }}</span>
            </div>
            <div v-if="item.context" class="item-context">{{ item.context }}</div>
          </div>
        </div>
      </div>

      <div class="summary-section" v-if="structuredSummary.todos.length > 0">
        <div class="section-header">
          <el-icon><List /></el-icon>
          <span class="section-title">待办事项</span>
        </div>
        <div class="section-content">
          <div
            v-for="(item, index) in structuredSummary.todos"
            :key="'todo-' + index"
            class="todo-item"
          >
            <div class="todo-header">
              <span class="todo-title">{{ item.title }}</span>
              <el-tag
                :type="getPriorityType(item.priority)"
                size="small"
              >
                {{ getPriorityLabel(item.priority) }}
              </el-tag>
            </div>
            <div v-if="item.description" class="todo-description">{{ item.description }}</div>
            <div class="todo-meta">
              <span v-if="item.assignee" class="meta-item">
                <el-icon><User /></el-icon>
                {{ item.assignee }}
              </span>
              <span v-if="item.due_date" class="meta-item">
                <el-icon><Clock /></el-icon>
                {{ item.due_date }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="structuredSummary.raw_summary"
        class="raw-summary-section"
      >
        <el-collapse>
          <el-collapse-item title="原始摘要" name="raw">
            <div class="raw-summary-content">{{ structuredSummary.raw_summary }}</div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <div v-else ref="summaryBlockRef">
      <div
        class="summary-block"
        :class="{ empty: summaryDisplayText === '暂无会议摘要', 'is-clamped': showExpandBtn && !isExpanded }"
      >
        {{ summaryDisplayText }}
      </div>
      <transition name="expand-btn">
        <div class="expand-action" v-if="showExpandBtn">
          <el-button text type="primary" @click="isExpanded = !isExpanded">
            {{ isExpanded ? "折叠摘要" : "展开全文" }}
            <span class="expand-arrow" :class="{ 'is-rotated': isExpanded }">▼</span>
          </el-button>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { Document, CircleCheck, List, User, Clock } from "@element-plus/icons-vue";
import { useSummary } from "../../composables/useSummary";
import { useMeetingStore } from "../../stores/meetingStore";
import type { StructuredSummary } from "../../api/types";

const props = defineProps<{ meetingId: number }>();

const store = useMeetingStore();

const {
  summaryBlockRef,
  summaryDisplayText,
  showExpandBtn,
  isExpanded,
  maxClampLines,
  totalLineCount,
  initResizeObserver
} = useSummary(props.meetingId);

const structuredSummary = computed<StructuredSummary>(() => {
  const meeting = store.currentMeeting;
  if (meeting && "structured_summary" in meeting && meeting.structured_summary) {
    return meeting.structured_summary as StructuredSummary;
  }
  return {
    agenda: [],
    resolutions: [],
    todos: [],
    raw_summary: null
  };
});

const hasStructuredSummary = computed(() => {
  const summary = structuredSummary.value;
  return (
    summary.agenda.length > 0 ||
    summary.resolutions.length > 0 ||
    summary.todos.length > 0
  );
});

function getPriorityType(priority: string): "danger" | "warning" | "info" {
  switch (priority) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    default:
      return "info";
  }
}

function getPriorityLabel(priority: string): string {
  switch (priority) {
    case "high":
      return "高";
    case "medium":
      return "中";
    case "low":
      return "低";
    default:
      return priority;
  }
}

onMounted(() => {
  initResizeObserver();
});
</script>

<style scoped>
.summary-container {
  margin-top: 24px;
}

.structured-summary {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-section {
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.section-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.section-content {
  padding: 16px;
}

.agenda-item,
.resolution-item,
.todo-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.agenda-item:last-child,
.resolution-item:last-child,
.todo-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.agenda-item:first-child,
.resolution-item:first-child,
.todo-item:first-child {
  padding-top: 0;
}

.item-topic {
  font-weight: 500;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.item-speaker {
  margin-bottom: 8px;
}

.item-points {
  margin: 8px 0 0 20px;
  padding: 0;
  color: var(--el-text-color-regular);
  font-size: 13px;
}

.item-points li {
  margin: 4px 0;
}

.item-decision {
  font-weight: 500;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.meta-label {
  color: var(--el-text-color-placeholder);
}

.meta-value {
  color: var(--el-text-color-regular);
}

.item-context {
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding-left: 12px;
  border-left: 2px solid var(--el-border-color);
}

.todo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.todo-title {
  font-weight: 500;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.todo-description {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.todo-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.raw-summary-section {
  margin-top: 16px;
}

.raw-summary-content {
  white-space: pre-wrap;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.summary-block {
  margin: 0;
  padding: 24px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid var(--el-border-color-lighter);
  white-space: pre-wrap;
  line-height: 27px;
  font-size: 15px;
  color: var(--el-text-color-primary);
  
  transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), padding 0.4s ease;
  max-height: calc(v-bind('totalLineCount') * 27px + 48px);
  overflow: hidden;
}

.summary-block.empty {
  color: var(--el-text-color-placeholder);
  font-style: italic;
  text-align: center;
  padding: 40px;
  max-height: unset;
}

.summary-block.is-clamped {
  max-height: calc(v-bind('maxClampLines') * 27px + 48px);
  display: -webkit-box;
  -webkit-line-clamp: v-bind('maxClampLines');
  -webkit-box-orient: vertical;
}

.expand-action {
  text-align: center;
  margin-top: 8px;
}

.expand-btn-enter-active,
.expand-btn-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.expand-btn-enter-from,
.expand-btn-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.expand-arrow {
  display: inline-block;
  margin-left: 4px;
  transition: transform 0.3s ease;
  font-size: 12px;
}

.expand-arrow.is-rotated {
  transform: rotate(180deg);
}
</style>
