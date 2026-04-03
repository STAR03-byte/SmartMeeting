<template>
  <div class="audio-files-section">
    <h3 class="section-title">{{ $t('audio.title') }}</h3>
    
    <el-empty v-if="!audioFiles.length" :description="$t('audio.empty')" />
    
    <el-table v-else :data="audioFiles" style="width: 100%">
      <el-table-column prop="filename" :label="$t('audio.filename')" min-width="200" />
      <el-table-column prop="size_bytes" :label="$t('audio.size')" width="120">
        <template #default="{ row }">
          {{ formatFileSize(row.size_bytes) }}
        </template>
      </el-table-column>
      <el-table-column prop="uploaded_at" :label="$t('audio.uploadedAt')" width="180">
        <template #default="{ row }">
          {{ formatDate(row.uploaded_at) }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.operations')" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="playAudio(row)">
            {{ $t('audio.play') }}
          </el-button>
          <el-button type="success" size="small" @click="downloadAudio(row)">
            {{ $t('audio.download') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Audio Player Dialog -->
    <el-dialog
      v-model="playerVisible"
      :title="$t('audio.play')"
      width="500px"
      destroy-on-close
    >
      <audio controls style="width: 100%">
        <source :src="currentAudioUrl" type="audio/mpeg" />
        {{ $t('audio.loadAudioFailed') }}
      </audio>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import { listMeetingAudios, downloadAudio as downloadAudioApi } from '../../api/meetings';
import type { MeetingAudio } from '../../api/types';

const { t } = useI18n();

interface Props {
  meetingId: number;
}

const props = defineProps<Props>();

const audioFiles = ref<MeetingAudio[]>([]);
const playerVisible = ref(false);
const currentAudioUrl = ref('');
const loading = ref(false);

onMounted(async () => {
  await loadAudioFiles();
});

async function loadAudioFiles() {
  try {
    loading.value = true;
    audioFiles.value = await listMeetingAudios(props.meetingId);
  } catch (error) {
    ElMessage.error(t('audio.loadFailed'));
    console.error('Failed to load audio files:', error);
  } finally {
    loading.value = false;
  }
}

function playAudio(audio: MeetingAudio) {
  currentAudioUrl.value = `/api/v1/meetings/${props.meetingId}/audios/${audio.id}/stream`;
  playerVisible.value = true;
}

async function downloadAudio(audio: MeetingAudio) {
  try {
    const blob = await downloadAudioApi(audio.id, props.meetingId);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = audio.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    ElMessage.error(t('audio.loadAudioFailed'));
    console.error('Failed to download audio:', error);
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString();
}
</script>

<style scoped>
.audio-files-section {
  margin: 24px 0;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  border: 1px solid var(--el-border-color-lighter);
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>
