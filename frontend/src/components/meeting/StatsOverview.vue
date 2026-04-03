<template>
  <el-row :gutter="12" class="stats-row">
    <el-col :span="8">
      <el-statistic title="转写片段" :value="store.transcripts.length" />
    </el-col>
    <el-col :span="8">
      <el-statistic title="任务数" :value="store.tasks.length" />
    </el-col>
    <el-col :span="8">
      <el-statistic title="已完成任务" :value="doneTaskCount" />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useMeetingStore } from "../../stores/meetingStore";

const store = useMeetingStore();
const doneTaskCount = computed(() => store.tasks.filter((task) => task.status === "done").length);
</script>

<style scoped>
.stats-row {
  margin-top: 24px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-small);
}

.stats-row :deep(.el-col) {
  text-align: center;
}
</style>