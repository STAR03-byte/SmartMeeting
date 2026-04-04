<template>
  <div class="invite-accept-view" v-loading="loading">
    <el-card>
      <template #header>
        <div class="header">{{ $t('invitation.title') }}</div>
      </template>
      <el-alert v-if="error" :title="error" type="error" show-icon />
      <el-alert v-else-if="success" :title="success" type="success" show-icon />
      <div v-else>{{ $t('common.refresh') }}...</div>
      <div class="actions">
        <el-button type="primary" @click="$router.push('/teams')">{{ $t('app.navTeams') }}</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { getApiErrorMessage } from '../api/client';
import { acceptInvitationByToken } from '../api/teamInvitations';

const route = useRoute();
const loading = ref(false);
const error = ref('');
const success = ref('');

onMounted(async () => {
  const token = String(route.params.token || '').trim();
  if (!token) {
    error.value = '邀请链接无效';
    return;
  }

  loading.value = true;
  try {
    await acceptInvitationByToken(token);
    success.value = '已成功加入团队';
    window.dispatchEvent(new Event('team-invitations-changed'));
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.invite-accept-view { max-width: 720px; margin: 24px auto; }
.header { font-weight: 600; }
.actions { margin-top: 16px; }
</style>
