<template>
  <div class="team-detail-view" v-loading="loading">
    <div class="header-actions">
      <h2>团队详情</h2>
      <el-button @click="$router.back()">返回</el-button>
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
            <span>基本信息</span>
            <el-tag v-if="team.my_role" :type="getRoleTagType(team.my_role)">
              {{ getRoleLabel(team.my_role) }}
            </el-tag>
            <el-tag v-else-if="isOwner" type="danger">所有者</el-tag>
          </div>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="团队名称">{{ team.name }}</el-descriptions-item>
          <el-descriptions-item label="团队描述">{{ team.description || '暂无描述' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(team.created_at) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- Member List (Visible to all, but actions restricted) -->
      <el-card class="team-members-card">
        <template #header>
          <div class="card-header">
            <span>成员管理</span>
            <el-button
              v-if="canManageMembers"
              type="primary"
              size="small"
              @click="showAddMemberDialog = true"
            >
              添加成员
            </el-button>
          </div>
        </template>

        <el-table :data="members" style="width: 100%" v-loading="membersLoading">
          <el-table-column prop="user.full_name" label="姓名" min-width="120" />
          <el-table-column prop="user.email" label="邮箱" min-width="180" />
          <el-table-column label="角色" width="150">
            <template #default="{ row }">
              <el-select
                v-if="isOwner && row.user_id !== team.owner_id"
                v-model="row.role"
                size="small"
                @change="(val: string) => handleRoleChange(row, val)"
                :disabled="updatingRole === row.id"
              >
                <el-option label="管理员" value="admin" />
                <el-option label="成员" value="member" />
              </el-select>
              <el-tag v-else :type="getRoleTagType(row.role)">
                {{ getRoleLabel(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="加入时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.joined_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-popconfirm
                v-if="canManageMembers && row.user_id !== team.owner_id"
                title="确定要移除该成员吗？"
                @confirm="handleRemoveMember(row)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">移除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <!-- Add Member Dialog -->
    <el-dialog
      v-model="showAddMemberDialog"
      title="添加成员"
      width="500px"
      @open="fetchUsers"
    >
      <el-form :model="addMemberForm" ref="addMemberFormRef" label-width="80px">
        <el-form-item
          label="选择用户"
          prop="user_id"
          :rules="[{ required: true, message: '请选择用户', trigger: 'change' }]"
        >
          <el-select
            v-model="addMemberForm.user_id"
            placeholder="请选择要添加的用户"
            filterable
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
        <el-form-item
          label="角色"
          prop="role"
          :rules="[{ required: true, message: '请选择角色', trigger: 'change' }]"
        >
          <el-select v-model="addMemberForm.role" style="width: 100%">
            <el-option label="成员" value="member" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddMemberDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddMember" :loading="addingMember">
            确认添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';
import { getTeam, getTeamMembers, addTeamMember, removeTeamMember, updateMemberRole } from '../api/teams';
import type { Team, TeamMember } from '../api/teams';
import { getUsers } from '../api/users';
import type { UserItem } from '../api/types';
import { useAuthStore } from '../stores/authStore';
import { getApiErrorMessage } from '../api/client';

const route = useRoute();
const teamId = Number(route.params.id);
const authStore = useAuthStore();

const loading = ref(true);
const error = ref('');
const team = ref<Team | null>(null);

const members = ref<TeamMember[]>([]);
const membersLoading = ref(false);

const updatingRole = ref<number | null>(null);

// Add Member
const showAddMemberDialog = ref(false);
const users = ref<UserItem[]>([]);
const usersLoading = ref(false);
const addingMember = ref(false);
const addMemberFormRef = ref<FormInstance>();
const addMemberForm = ref({
  user_id: undefined as number | undefined,
  role: 'member'
});

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
    case 'owner': return '所有者';
    case 'admin': return '管理员';
    case 'member': return '成员';
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

const loadData = async () => {
  loading.value = true;
  error.value = '';
  try {
    team.value = await getTeam(teamId);
    await loadMembers();
  } catch (err: any) {
    error.value = getApiErrorMessage(err) || '加载团队信息失败';
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
    ElMessage.error(getApiErrorMessage(err) || '加载成员列表失败');
  } finally {
    membersLoading.value = false;
  }
};

const fetchUsers = async () => {
  if (users.value.length > 0) return;
  usersLoading.value = true;
  try {
    users.value = await getUsers();
  } catch (err: any) {
    ElMessage.error('加载用户列表失败');
  } finally {
    usersLoading.value = false;
  }
};

const handleAddMember = async () => {
  if (!addMemberFormRef.value) return;
  await addMemberFormRef.value.validate(async (valid) => {
    if (valid && addMemberForm.value.user_id) {
      addingMember.value = true;
      try {
        await addTeamMember(teamId, {
          user_id: addMemberForm.value.user_id,
          role: addMemberForm.value.role
        });
        ElMessage.success('添加成员成功');
        showAddMemberDialog.value = false;
        // reset form
        addMemberForm.value.user_id = undefined;
        addMemberForm.value.role = 'member';
        await loadMembers();
      } catch (err: any) {
        ElMessage.error(getApiErrorMessage(err) || '添加成员失败');
      } finally {
        addingMember.value = false;
      }
    }
  });
};

const handleRemoveMember = async (member: TeamMember) => {
  try {
    await removeTeamMember(teamId, member.user_id);
    ElMessage.success('成员已移除');
    await loadMembers();
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || '移除成员失败');
  }
};

const handleRoleChange = async (member: TeamMember, newRole: string) => {
  updatingRole.value = member.id;
  try {
    await updateMemberRole(teamId, member.user_id, newRole);
    ElMessage.success('角色更新成功');
    // Local state already updated via v-model
  } catch (err: any) {
    ElMessage.error(getApiErrorMessage(err) || '角色更新失败');
    // Revert changes on error
    await loadMembers();
  } finally {
    updatingRole.value = null;
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
.mb-4 {
  margin-bottom: 16px;
}
</style>
