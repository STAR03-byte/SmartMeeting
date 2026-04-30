<template>
  <el-card class="meeting-card" shadow="hover" @click="goDetail">
    <div class="meeting-card-title">{{ meeting.title }}</div>
    <div class="meeting-card-meta">
      <span class="meta-chip">状态: {{ meeting.status }}</span>
      <span class="meta-chip">ID: {{ meeting.id }}</span>
    </div>
    <p class="meeting-card-desc">{{ meeting.description || $t('team.noDescription') }}</p>
  </el-card>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { useRouter } from "vue-router";
import type { Meeting } from "../../api/meetings";

const props = defineProps<{
  meeting: Meeting;
}>();

const router = useRouter();

function goDetail() {
  router.push(`/meetings/${props.meeting.id}`);
}
</script>

<style scoped>
.meeting-card {
  cursor: pointer;
  border-radius: 12px;
  border: 1px solid rgba(18, 56, 96, 0.2);
}

.meeting-card-title {
  font-size: 18px;
  font-weight: 700;
  color: #113355;
}

.meeting-card-meta {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.meta-chip {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e8f4ff;
  color: #0c4a84;
}

.meeting-card-desc {
  margin: 10px 0 0;
  color: #2c4965;
}
</style>
