<template>
  <el-row :gutter="12" class="stats-row">
    <el-col :span="8">
      <el-statistic :title="$t('stats.transcriptCount')" :value="store.transcripts.length" />
    </el-col>
    <el-col :span="8">
      <el-statistic :title="$t('stats.taskCount')" :value="store.tasks.length" />
    </el-col>
    <el-col :span="8">
      <el-statistic :title="$t('stats.doneTaskCount')" :value="doneTaskCount" />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
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