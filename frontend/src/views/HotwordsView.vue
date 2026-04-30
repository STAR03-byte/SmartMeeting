<template>
  <section class="hotwords-page">
    <header class="hero-header">
      <div>
        <h1>{{ $t('hotword.title') }}</h1>
        <p>{{ $t('hotword.description') }}</p>
      </div>
    </header>

    <AppErrorAlert :error="error" :closable="false" />

    <div class="layout">
      <el-card class="base-card">
        <template #header>{{ $t('hotword.addHotword') }}</template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item :label="$t('hotword.hotword')">
            <el-input v-model="word" :placeholder="$t('hotword.hotwordPlaceholder')" maxlength="100" />
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleCreate">{{ $t('hotword.add') }}</el-button>
        </el-form>
      </el-card>

      <el-card class="base-card" v-loading="loading">
        <template #header>{{ $t('hotword.list') }}</template>
        <el-table :data="hotwords" stripe>
          <el-table-column prop="word" :label="$t('hotword.hotword')" min-width="180" />
          <el-table-column prop="created_at" :label="$t('team.createdAt')" min-width="180" />
          <el-table-column :label="$t('common.operations')" width="120">
            <template #default="{ row }">
              <el-popconfirm :title="$t('hotword.deleteConfirm')" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" plain>{{ $t('common.delete') }}</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import AppErrorAlert from "../components/common/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import { createHotword, deleteHotword, getHotwords, type HotwordItem } from "../api/hotwords";

const hotwords = ref<HotwordItem[]>([]);
const loading = ref(false);
const submitting = ref(false);
const error = ref<string | null>(null);
const word = ref("");

async function refreshHotwords() {
  loading.value = true;
  error.value = null;
  try {
    hotwords.value = await getHotwords();
  } catch (err) {
    error.value = notifyApiError(err, { prefix: t('hotword.loadFailed') });
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  const value = word.value.trim();
  if (!value) {
    ElMessage.warning(t('hotword.inputRequired'));
    return;
  }

  submitting.value = true;
  try {
    await createHotword({ word: value });
    ElMessage.success(t('hotword.addSuccess'));
    word.value = "";
    await refreshHotwords();
  } catch (err) {
    notifyApiError(err);
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(hotwordId: number) {
  try {
    await deleteHotword(hotwordId);
    ElMessage.success(t('hotword.deleteSuccess'));
    await refreshHotwords();
  } catch (err) {
    notifyApiError(err);
  }
}

onMounted(async () => {
  await refreshHotwords();
});
</script>

<style scoped>
.hotwords-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-header {
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
  border-radius: var(--el-border-radius-base);
  padding: 32px 40px;
  box-shadow: var(--el-box-shadow-light);
}

.hero-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary-dark-2);
}

.hero-header p {
  margin: 12px 0 0;
  color: var(--el-color-primary);
}

.layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
}

.base-card {
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  font-weight: 600;
}

.base-card :deep(.el-card__body) {
  padding: 24px;
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
