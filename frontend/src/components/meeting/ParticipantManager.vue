<template>
  <el-skeleton animated :loading="loading">
    <template #template>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <el-skeleton-item variant="text" style="width: 48px; height: 24px;" />
          </div>
        </template>
        <div style="height: 100px;"></div>
      </el-card>
    </template>
    <template #default>
      <el-card class="base-card">
        <template #header>
          <div class="panel-header">
            <span>{{ $t('participant.title') }}</span>
            <el-button text @click="refreshParticipants">{{ $t('common.refresh') }}</el-button>
          </div>
        </template>

        <div class="participant-create-row">
          <el-select
            v-model="participantForm.user_id"
            filterable
            clearable
            :placeholder="$t('participant.selectUser')"
            style="min-width: 220px"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
          <el-select v-model="participantForm.participant_role" style="width: 140px">
            <el-option :label="$t('participant.roleRequired')" value="required" />
            <el-option :label="$t('participant.roleOptional')" value="optional" />
            <el-option :label="$t('participant.roleObserver')" value="observer" />
          </el-select>
          <el-button type="primary" :loading="creatingParticipant" @click="addParticipant">{{ $t('common.add') }}</el-button>
        </div>

        <el-empty v-if="participants.length === 0" :description="$t('participant.empty')" />
        <ul v-else class="plain-list">
          <li v-for="participant in participants" :key="participant.id" class="participant-row">
            <div class="participant-main">
              <strong>{{ participant.username }}</strong>
              <el-tag size="small" :type="attendanceTag(participant.attendance_status)">
                {{ attendanceLabel(participant.attendance_status) }}
              </el-tag>
            </div>
            <div class="participant-actions">
              <el-select
                :model-value="participant.participant_role"
                size="small"
                style="width: 120px"
                @change="(role: string) => changeParticipantRole(participant.id, role)"
              >
                <el-option :label="$t('participant.roleRequired')" value="required" />
                <el-option :label="$t('participant.roleOptional')" value="optional" />
                <el-option :label="$t('participant.roleObserver')" value="observer" />
              </el-select>
              <el-popconfirm :title="$t('participant.removeConfirm')" @confirm="removeParticipant(participant.id)">
                <template #reference>
                  <el-button size="small" type="danger" plain>{{ $t('team.remove') }}</el-button>
                </template>
              </el-popconfirm>
            </div>
          </li>
        </ul>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  createMeetingParticipant,
  deleteMeetingParticipant,
  getMeetingParticipants,
  updateMeetingParticipant,
} from "../../api/participants";
import { getUsers, type UserItem } from "../../api/users";
import type { MeetingParticipantOut } from "../../api/types";
import { notifyApiError } from "../../utils/notify";

const props = defineProps<{ meetingId: number }>();

const loading = ref(false);
const creatingParticipant = ref(false);
const participants = ref<MeetingParticipantOut[]>([]);
const users = ref<UserItem[]>([]);

const participantForm = reactive<{ user_id: number | null; participant_role: string }>({
  user_id: null,
  participant_role: "required",
});

const availableUsers = computed(() => {
  const existingUserIds = new Set(participants.value.map((item) => item.user_id));
  return users.value.filter((user) => !existingUserIds.has(user.id));
});

onMounted(async () => {
  await Promise.all([refreshParticipants(), refreshUsers()]);
});

async function refreshParticipants() {
  loading.value = true;
  try {
    participants.value = await getMeetingParticipants(props.meetingId);
  } catch (err) {
    notifyApiError(err);
  } finally {
    loading.value = false;
  }
}

async function refreshUsers() {
  try {
    users.value = await getUsers({ scope: "selectable", meeting_id: props.meetingId });
  } catch (err) {
    notifyApiError(err);
  }
}

async function addParticipant() {
  if (!participantForm.user_id) {
    ElMessage.warning(t('participant.selectUserFirst'));
    return;
  }
  creatingParticipant.value = true;
  try {
    await createMeetingParticipant({
      meeting_id: props.meetingId,
      user_id: participantForm.user_id,
      participant_role: participantForm.participant_role,
    });
    participantForm.user_id = null;
    participantForm.participant_role = "required";
    ElMessage.success(t('participant.addSuccess'));
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  } finally {
    creatingParticipant.value = false;
  }
}

async function changeParticipantRole(participantId: number, role: string) {
  try {
    await updateMeetingParticipant(participantId, { participant_role: role });
    ElMessage.success(t('participant.roleUpdateSuccess'));
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  }
}

async function removeParticipant(participantId: number) {
  try {
    await deleteMeetingParticipant(participantId);
    ElMessage.success(t('participant.removeSuccess'));
    await refreshParticipants();
  } catch (err) {
    notifyApiError(err);
  }
}

function attendanceLabel(status: string): string {
  const map: Record<string, string> = {
    invited: t('participant.statusInvited'),
    accepted: t('participant.statusAccepted'),
    declined: t('participant.statusDeclined'),
    attended: t('participant.statusAttended'),
  };
  return map[status] ?? status;
}

function attendanceTag(status: string): string {
  const map: Record<string, string> = {
    invited: "info",
    accepted: "success",
    declined: "danger",
    attended: "warning",
  };
  return map[status] ?? "info";
}

defineExpose({
  reload: refreshParticipants
});
</script>

<style scoped>
.base-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0;
  flex: 1;
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
  background: var(--el-bg-color);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.base-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.plain-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.participant-create-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-small);
}

.participant-row {
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-small);
  border: 1px solid transparent;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  transition: all 0.2s ease;
}

.participant-row:hover {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.participant-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex-wrap: wrap;
}

.participant-main strong {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.participant-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
