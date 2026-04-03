<template>
  <section class="teams-page">
    <header class="page-header">
      <h1>{{ $t('team.title') }}</h1>
      <el-button type="primary" @click="createTeam">
        <el-icon><Plus /></el-icon>
        {{ $t('team.createTeam') }}
      </el-button>
    </header>

    <section class="teams-section">
      <el-table :data="teams" v-loading="loading" stripe class="teams-table">
        <el-table-column prop="name" :label="$t('team.teamName')" min-width="150" />
        <el-table-column prop="description" :label="$t('task.taskDescription')" min-width="250">
          <template #default="{ row }">
            {{ row.description || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="my_role" :label="$t('team.myRole')" width="120">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.my_role)">
              {{ roleLabel(row.my_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operations')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">{{ $t('common.view') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Plus } from '@element-plus/icons-vue';

import { getTeams, type Team } from '../api/teams';
import { notifyApiError } from '../utils/notify';

const router = useRouter();

const teams = ref<Team[]>([]);
const loading = ref(false);

async function loadTeams() {
  loading.value = true;
  try {
    teams.value = await getTeams();
  } catch (error) {
    notifyApiError(error, { prefix: t('team.loadFailed') });
  } finally {
    loading.value = false;
  }
}

function createTeam() {
  router.push('/teams/create');
}

function viewDetail(team: Team) {
  router.push(`/teams/${team.id}`);
}

function roleLabel(role?: string): string {
  if (role === 'owner') return t('team.roleOwner');
  if (role === 'admin') return t('team.roleAdmin');
  if (role === 'member') return t('team.roleMember');
  return role || t('common.unknown');
}

function roleTagType(role?: string): string {
  if (role === 'owner') return 'danger';
  if (role === 'admin') return 'warning';
  if (role === 'member') return 'info';
  return '';
}

onMounted(() => {
  loadTeams();
});
</script>

<style scoped>
.teams-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: -0.5px;
}

.teams-section {
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  padding: 24px;
  box-shadow: var(--el-box-shadow-light);
}

.teams-table {
  border-radius: var(--el-border-radius-small);
  overflow: hidden;
}

.teams-table :deep(.el-table__header-wrapper th) {
  background: var(--el-fill-color-light);
  font-weight: 600;
  color: var(--el-text-color-regular);
  height: 56px;
  border-bottom: none;
}

.teams-table :deep(.el-table__body-wrapper td) {
  padding: 16px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.teams-table :deep(.el-table__row:hover > td) {
  background-color: var(--el-color-primary-light-9) !important;
}
</style>
