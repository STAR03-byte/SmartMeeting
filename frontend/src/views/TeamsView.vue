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
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="My Teams" name="mine">
          <el-table :data="teams" v-loading="myTeamsLoading" stripe class="teams-table">
            <el-table-column prop="name" :label="$t('team.teamName')" min-width="150" />
            <el-table-column prop="description" :label="$t('task.taskDescription')" min-width="250">
              <template #default="{ row }">
                {{ row.description || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="is_public" label="Visibility" width="120">
              <template #default="{ row }">
                <el-tag :type="row.is_public ? 'success' : 'info'">
                  {{ row.is_public ? 'Public' : 'Private' }}
                </el-tag>
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
        </el-tab-pane>

        <el-tab-pane label="Discover" name="discover">
          <el-table :data="publicTeams" v-loading="discoverLoading" stripe class="teams-table">
            <el-table-column prop="name" :label="$t('team.teamName')" min-width="150" />
            <el-table-column prop="description" :label="$t('task.taskDescription')" min-width="250">
              <template #default="{ row }">
                {{ row.description || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="Visibility" width="120">
              <template #default>
                <el-tag type="success">Public</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.operations')" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="joinTeam(row)">Join</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Plus } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

import { getPublicTeams, getTeams, joinPublicTeam, type Team } from '../api/teams';
import { notifyApiError } from '../utils/notify';

const router = useRouter();

const teams = ref<Team[]>([]);
const publicTeams = ref<Team[]>([]);
const activeTab = ref('mine');
const myTeamsLoading = ref(false);
const discoverLoading = ref(false);

async function loadTeams() {
  myTeamsLoading.value = true;
  try {
    teams.value = await getTeams();
  } catch (error) {
    notifyApiError(error, { prefix: t('team.loadFailed') });
  } finally {
    myTeamsLoading.value = false;
  }
}

async function loadPublicTeams() {
  discoverLoading.value = true;
  try {
    publicTeams.value = await getPublicTeams();
  } catch (error) {
    notifyApiError(error, { prefix: t('team.loadFailed') });
  } finally {
    discoverLoading.value = false;
  }
}

function createTeam() {
  router.push('/teams/create');
}

function viewDetail(team: Team) {
  router.push(`/teams/${team.id}`);
}

async function joinTeam(team: Team) {
  try {
    await joinPublicTeam(team.id);
    ElMessage.success('已加入团队');
    await Promise.all([loadTeams(), loadPublicTeams()]);
  } catch (error) {
    notifyApiError(error, { prefix: '加入团队失败' });
  }
}

async function handleTabChange(name: string | number) {
  if (name === 'discover' && publicTeams.value.length === 0) {
    await loadPublicTeams();
  }
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
  void Promise.all([loadTeams(), loadPublicTeams()]);
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

/* Mobile Adjustments */
@media (max-width: 767px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .teams-section {
    padding: 16px;
  }
}
</style>
