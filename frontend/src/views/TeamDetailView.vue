<template>
  <div class="team-detail-view" v-loading="loading">
    <div class="header-actions">
      <h2>{{ $t('team.detailTitle') }}</h2>
      <el-button @click="$router.back()">{{ $t('common.back') }}</el-button>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      class="mb-4"
    />

    <template v-if="team">
      <el-card class="team-info-card mb-4">
        <template #header>
          <div class="card-header">
            <span>{{ $t('team.basicInfo') }}</span>
            <div class="header-tags">
              <el-tag v-if="team.my_role" :type="getRoleTagType(team.my_role)">
                {{ getRoleLabel(team.my_role) }}
              </el-tag>
              <el-tag v-else-if="isOwner" type="danger">{{ $t('team.roleOwner') }}</el-tag>
              <el-popconfirm
                v-if="isOwner"
                title="确定要删除该团队吗？此操作不可恢复"
                @confirm="handleDeleteTeam"
              >
                <template #reference>
                  <el-button type="danger" size="small" :loading="deletingTeam">删除团队</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="$t('team.teamName')">{{ team.name }}</el-descriptions-item>
          <el-descriptions-item label="团队描述">{{ team.description || $t('team.noDescription') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('team.createdAt')">{{ formatDate(team.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="canManageMembers" class="invite-link-block">
          <el-button type="primary" plain :loading="creatingInviteLink" @click="handleCreateInviteLink">
            生成邀请链接
          </el-button>
          <el-input v-if="inviteLink" :model-value="inviteLink" readonly class="mt-2" />
        </div>
      </el-card>

      <!-- Member List (Visible to all, but actions restricted) -->
      <el-card class="team-members-card">
        <template #header>
          <div class="card-header">
            <span>{{ $t('team.memberManagement') }}</span>
            <el-button
              v-if="canManageMembers"
              type="primary"
              size="small"
              @click="showInviteMemberDialog = true"
            >
              {{ $t('team.inviteMember') }}
            </el-button>
          </div>
        </template>

        <el-table :data="members" style="width: 100%" v-loading="membersLoading">
          <el-table-column :label="$t('team.memberName')" min-width="120">
            <template #default="{ row }">
              {{ row.full_name }} ({{ row.user_name }})
            </template>
          </el-table-column>
          <el-table-column prop="email" :label="$t('team.email')" min-width="180" />
          <el-table-column :label="$t('team.role')" width="150">
            <template #default="{ row }">
              <el-select
                v-if="isOwner && row.user_id !== team.owner_id"
                v-model="row.role"
                size="small"
                @change="(val: string) => handleRoleChange(row, val)"
                :disabled="updatingRole === row.id"
              >
                <el-option :label="$t('team.roleAdmin')" value="admin" />
                <el-option :label="$t('team.roleMember')" value="member" />
              </el-select>
              <el-tag v-else :type="getRoleTagType(row.role)">
                {{ getRoleLabel(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invitation.pending')" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.invitation_status" :type="getInvitationTagType(row.invitation_status)">
                {{ getInvitationStatusLabel(row.invitation_status) }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('team.joinedAt')" width="180">
            <template #default="{ row }">
              {{ formatDate(row.joined_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operations')" width="120" fixed="right">
            <template #default="{ row }">
              <el-popconfirm
                v-if="canManageMembers && row.user_id !== team.owner_id"
                :title="$t('team.removeConfirm')"
                @confirm="handleRemoveMember(row)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">{{ $t('team.remove') }}</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <!-- Add Member Dialog -->
    <el-dialog
      v-model="showInviteMemberDialog"
      :title="$t('team.inviteMember')"
      width="500px"
    >
      <el-form :model="inviteMemberForm" ref="inviteMemberFormRef" label-width="80px">
        <el-form-item
          :label="$t('participant.selectUser')"
          prop="user_id"
          :rules="[{ required: true, message: $t('team.selectUserRequired'), trigger: 'change' }]"
        >
          <el-select
            v-model="inviteMemberForm.user_id"
            :placeholder="$t('team.selectUserPlaceholder')"
            filterable
            remote
            :remote-method="handleUserSearch"
            style="width: 100%"
            :loading="usersLoading"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.full_name} (${user.email})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showInviteMemberDialog = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="handleInviteMember" :loading="invitingMember">
            {{ $t('team.confirmInvite') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';
import { getTeam, getTeamMembers, removeTeamMember, updateMemberRole, deleteTeam } from '../api/teams';
import type { Team, TeamMember } from '../api/teams';
import { searchInvitableUsers } from '../api/users';
import type { UserItem } from '../api/types';
import { useAuthStore } from '../stores/authStore';
import { getApiErrorMessage } from '../api/client';
import { sendInvitation } from '../api/teamInvitations';
import { createTeamInviteLink } from '../api/teamInvitations';

const route = useRoute();
const teamId = Number(route.params.id);
const authStore = useAuthStore();

const loading = ref(true);
const error = ref('');
const team = ref<Team | null>(null);

const members = ref<TeamMember[]>([]);
const membersLoading = ref(false);

const updatingRole = ref<number | null>(null);
const deletingTeam = ref(false);

// Add Member
const showInviteMemberDialog = ref(false);
const users = ref<UserItem[]>([]);
const usersLoading = ref(false);
const invitingMember = ref(false);
const inviteMemberFormRef = ref<FormInstance>();
const inviteMemberForm = ref({
  user_id: undefined as number | undefined,
});
const userSearchKeyword = ref('');
const creatingInviteLink = ref(false);
const inviteLink = ref('');

const isOwner = computed(() => {
  if (!team.value || !authStore.currentUser) return false;
  return team.value.owner_id === authStore.currentUser.id || team.value.my_role === 'owner';
});

const canManageMembers = computed(() => {
  if (isOwner.value) return true;
  return team.value?.my_role === 'admin';
});

const availableUsers = computed(() => {
  // Filter out users who are already in the team
  const currentMemberIds = new Set(members.value.map(m => m.user_id));
  return users.value.filter(u => !currentMemberIds.has(u.id));
});

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getRoleLabel = (role: string) => {
  switch (role) {
    case 'owner': return t('team.roleOwner');
    case 'admin': return t('team.roleAdmin');
    case 'member': return t('team.roleMember');
    default: return role;
  }
};

const getRoleTagType = (role: string) => {
  switch (role) {
    case 'owner': return 'danger';
    case 'admin': return 'warning';
    case 'member': return 'info';
    default: return '';
  }
};

const getInvitationStatusLabel = (status: string) => {
  switch (status) {
    case 'pending': return t('invitation.pending');
    case 'accepted': return t('participant.statusAccepted');
    case 'rejected': return t('participant.statusDeclined');
    default: return status;
  }
};

const getInvitationTagType = (status: string) => {
  switch (status) {
    case 'pending': return 'warning';
    case 'accepted': return 'success';
    case 'rejected': return 'info';
    default: return '';
  }
};

const loadData = async () => {
  loading.value = true;
  error.value = '';
  try {
    team.value = await getTeam(teamId);
    await loadMembers();
  } catch (err: any) {
    error.value = getApiErrorMessage(err) || t('team.loadTeamFailed');
  } finally {
    loading.value = false;
  }
};

const loadMembers = async () => {
  membersLoading.value = true;
  try {
    members.value = await getTeamMembers(teamId);
    
    // Update my_role based on members if not provided by getTeam API
    if (team.value && authStore.currentUser && !team.value.my_role) {
      const myMember = members.value.find(m => m.user_id === authStore.currentUser?.id);
      if (myMember) {
        team.value.my_role = myMember.role;
      }
    }
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || t('team.loadMemberFailed'));
  } finally {
    membersLoading.value = false;
  }
};

const fetchUsers = async (keyword = '') => {
  usersLoading.value = true;
  try {
    const normalized = keyword.trim();
    if (normalized.length < 2) {
      users.value = [];
      return;
    }
    users.value = await searchInvitableUsers(teamId, normalized, 20);
  } catch (err: any) {
    ElMessage.error(t('team.loadUserFailed'));
  } finally {
    usersLoading.value = false;
  }
};

const handleUserSearch = async (keyword: string) => {
  userSearchKeyword.value = keyword;
  await fetchUsers(keyword);
};

const handleCreateInviteLink = async () => {
  creatingInviteLink.value = true;
  try {
    const data = await createTeamInviteLink(teamId, 72);
    const fullLink = `${window.location.origin}${data.invite_path}`;
    inviteLink.value = fullLink;
    await navigator.clipboard.writeText(fullLink);
    ElMessage.success('邀请链接已生成并复制');
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || t('team.inviteMemberFailed'));
  } finally {
    creatingInviteLink.value = false;
  }
};

const handleInviteMember = async () => {
  if (!inviteMemberFormRef.value) return;
  await inviteMemberFormRef.value.validate(async (valid) => {
    if (valid && inviteMemberForm.value.user_id) {
      invitingMember.value = true;
      try {
        await sendInvitation(teamId, inviteMemberForm.value.user_id);
        ElMessage.success(t('team.inviteMemberSuccess'));
        showInviteMemberDialog.value = false;
        inviteMemberForm.value.user_id = undefined;
        userSearchKeyword.value = '';
        users.value = [];
        await loadMembers();
        window.dispatchEvent(new Event('team-invitations-changed'));
      } catch (err: any) {
        ElMessage.error(getApiErrorMessage(err) || t('team.inviteMemberFailed'));
      } finally {
        invitingMember.value = false;
      }
    }
  });
};

const handleRemoveMember = async (member: TeamMember) => {
  try {
    await removeTeamMember(teamId, member.user_id);
    ElMessage.success(t('team.memberRemoved'));
    await loadMembers();
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || t('team.removeMemberFailed'));
  }
};

const handleRoleChange = async (member: TeamMember, newRole: string) => {
  updatingRole.value = member.user_id;
  try {
    await updateMemberRole(teamId, member.user_id, newRole);
    ElMessage.success(t('team.roleUpdateSuccess'));
    // Local state already updated via v-model
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || t('team.roleUpdateFailed'));
    // Revert changes on error
    await loadMembers();
  } finally {
    updatingRole.value = null;
  }
};

const handleDeleteTeam = async () => {
  if (!isOwner.value) return;
  deletingTeam.value = true;
  try {
    await deleteTeam(teamId);
    ElMessage.success('团队已删除');
    // 跳转到团队列表页
    window.location.href = '/teams';
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || '删除团队失败');
  } finally {
    deletingTeam.value = false;
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.team-detail-view {
  max-width: 1000px;
  margin: 0 auto;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-actions h2 {
  margin: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}
.mb-4 {
  margin-bottom: 16px;
}

.invite-link-block {
  margin-top: 12px;
}

/* Mobile Adjustments */
@media (max-width: 767px) {
  .header-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
