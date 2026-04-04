<template>
  <div class="invitations-view" v-loading="loading">
    <div class="header-actions">
      <h2>{{ $t('invitation.title') }}</h2>
      <el-button @click="loadInvitations" :loading="loading">{{ $t('common.refresh') }}</el-button>
    </div>

    <el-empty v-if="!loading && invitations.length === 0" :description="$t('invitation.noInvitations')" />

    <el-space v-else direction="vertical" fill :size="12" class="w-full">
      <el-card v-for="invitation in invitations" :key="invitation.id">
        <div class="invitation-row">
          <div>
            <div class="title">{{ invitation.team?.name || invitation.team_name || $t('common.unknown') }}</div>
            <div class="meta">
              {{ $t('invitation.sentBy') }}: {{ invitation.inviter?.full_name || invitation.inviter_name || $t('common.unknown') }}
            </div>
            <div class="meta">
              {{ $t('invitation.toTeam') }}: {{ invitation.team?.name || invitation.team_name || $t('common.unknown') }}
            </div>
          </div>
          <div class="actions">
            <el-tag type="warning">{{ $t('invitation.pending') }}</el-tag>
            <el-button size="small" type="primary" :loading="actingId === invitation.id" @click="handleAccept(invitation.id)">
              {{ $t('invitation.accept') }}
            </el-button>
            <el-button size="small" :loading="actingId === invitation.id" @click="handleReject(invitation.id)">
              {{ $t('invitation.reject') }}
            </el-button>
          </div>
        </div>
      </el-card>
    </el-space>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { acceptInvitation, getMyInvitations, rejectInvitation, type Invitation } from '../api/teamInvitations';
import { getApiErrorMessage } from '../api/client';

const loading = ref(false);
const invitations = ref<Invitation[]>([]);
const actingId = ref<number | null>(null);

const loadInvitations = async () => {
  loading.value = true;
  try {
    invitations.value = (await getMyInvitations()).filter((item) => item.status === 'pending');
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error));
  } finally {
    loading.value = false;
  }
};

const handleAccept = async (id: number) => {
  actingId.value = id;
  try {
    await acceptInvitation(id);
    ElMessage.success('OK');
    window.dispatchEvent(new Event('team-invitations-changed'));
    await loadInvitations();
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error));
  } finally {
    actingId.value = null;
  }
};

const handleReject = async (id: number) => {
  actingId.value = id;
  try {
    await rejectInvitation(id);
    ElMessage.success('OK');
    window.dispatchEvent(new Event('team-invitations-changed'));
    await loadInvitations();
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error));
  } finally {
    actingId.value = null;
  }
};

onMounted(loadInvitations);
</script>

<style scoped>
.invitations-view { max-width: 960px; margin: 0 auto; }
.header-actions { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.invitation-row { display:flex; justify-content:space-between; gap:16px; align-items:center; }
.title { font-weight:600; margin-bottom:6px; }
.meta { color: var(--el-text-color-secondary); font-size: 13px; }
.actions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
@media (max-width: 767px) { .invitation-row { flex-direction:column; align-items:flex-start; } }
</style>
