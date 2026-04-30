<template>
  <div v-if="visible" class="processing-progress">
    <div class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-elapsed">{{ formattedElapsed }}</span>
    </div>
    <el-progress
      :percentage="Math.round(progress * 100)"
      :status="progressStatus"
      :stroke-width="10"
    />
    <div class="progress-footer">
      <span class="progress-message">{{ message }}</span>
      <el-button
        v-if="showCancel"
        type="danger"
        text
        size="small"
        @click="$emit('cancel')"
      >
        取消
      </el-button>
    </div>
    <div v-if="error" class="progress-error">
      <el-text type="danger">{{ error }}</el-text>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ProcessingJobStatus } from "../../api/types";

interface Props {
  visible: boolean;
  status?: ProcessingJobStatus | null;
  progress?: number;
  message?: string;
  error?: string | null;
  formattedElapsed?: string;
  label?: string;
}

const props = withDefaults(defineProps<Props>(), {
  status: null,
  progress: 0,
  message: "",
  error: null,
  formattedElapsed: "",
  label: "处理中",
});

defineEmits<{
  cancel: [];
}>();

const showCancel = computed(() =>
  props.status != null &&
  !["completed", "failed", "interrupted"].includes(props.status),
);

const progressStatus = computed(() => {
  if (props.status === "completed") return "success" as const;
  if (props.status === "failed" || props.status === "interrupted") return "exception" as const;
  return undefined;
});
</script>

<style scoped>
.processing-progress {
  padding: 12px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-weight: 500;
  font-size: 14px;
}

.progress-elapsed {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.progress-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.progress-message {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.progress-error {
  margin-top: 8px;
}
</style>
