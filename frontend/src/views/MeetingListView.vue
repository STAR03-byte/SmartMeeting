<template>
  <section class="meeting-list-page">
    <header class="page-header">
      <h1>{{ $t('app.navMeetings') }}</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        {{ $t('dashboard.newMeeting') }}
      </el-button>
    </header>

    <section class="filter-section">
      <el-form inline class="filter-bar" @submit.prevent="applyFilter">
        <el-form-item :label="$t('common.status')">
          <el-select v-model="filterStatus" clearable :placeholder="$t('common.all')" style="width: 140px">
            <el-option :label="$t('meeting.statusPlanned')" value="planned" />
            <el-option :label="$t('task.statusInProgress')" value="ongoing" />
            <el-option :label="$t('meeting.statusDone')" value="done" />
            <el-option :label="$t('meeting.statusCancelled')" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.keyword')">
          <el-input v-model="filterKeyword" :placeholder="$t('common.searchPlaceholder')" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilter">{{ $t('common.filter') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="meetings-section">
      <el-skeleton v-if="store.loading" rows="5" animated />

      <AppErrorAlert v-else-if="store.error" :error="store.error" @close="store.error = null" />

      <el-table v-else :data="store.meetings" stripe class="meetings-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" :label="$t('task.taskTitle')" min-width="180">
          <template #default="{ row }">
            <router-link :to="`/meetings/${row.id}`" class="meeting-link">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('common.status')" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_start_at" label="计划开始" width="150">
          <template #default="{ row }">
            {{ formatDate(row.scheduled_start_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" :label="$t('meeting.location')" width="120">
          <template #default="{ row }">
            {{ row.location || "-" }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operations')" width="120" fixed="right">
          <template #default="{ row }">
            <el-popconfirm :title="$t('meeting.deleteConfirm')" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger" plain>{{ $t('common.delete') }}</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="totalCount > pageSize"
        class="pagination"
        layout="prev, pager, next"
        :total="totalCount"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </section>

    <el-dialog v-model="showCreateDialog" :title="$t('dashboard.newMeeting')" width="90%" style="max-width: 520px" @closed="resetCreateForm">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item :label="$t('task.taskTitle')" prop="title">
          <el-input v-model="createForm.title" :placeholder="$t('meeting.titlePlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('task.taskDescription')">
          <el-input v-model="createForm.description" type="textarea" :rows="3" :placeholder="$t('meeting.descriptionPlaceholder')" />
        </el-form-item>
        <el-form-item :label="$t('meeting.team')" prop="team_id">
          <el-select v-model="createForm.team_id" :placeholder="$t('team.selectTeamOptional')" clearable style="width: 100%">
            <el-option 
              v-for="team in teams" 
              :key="team.id" 
              :label="team.name" 
              :value="team.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('meeting.organizer')" prop="organizer_id">
          <el-select
            v-model="createForm.organizer_id"
            filterable
            :placeholder="$t('meeting.organizerPlaceholder')"
            style="width: 100%"
            :disabled="!canChooseOrganizer"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name}（${user.username}）`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('meeting.startTimeLabel')">
          <el-date-picker v-model="createForm.scheduled_start_at" type="datetime" :placeholder="$t('meeting.selectStartTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('meeting.endTimeLabel')">
          <el-date-picker v-model="createForm.scheduled_end_at" type="datetime" :placeholder="$t('meeting.selectEndTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('meeting.location')">
          <el-input v-model="createForm.location" :placeholder="$t('meeting.locationOptional')" />
        </el-form-item>
        <el-form-item :label="$t('participant.title')">
          <el-select
            v-model="selectedParticipantIds"
            multiple
            filterable
            clearable
            :placeholder="$t('participant.selectParticipantOptional')"
            style="width: 100%"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.full_name}（${user.username}）`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
import { computed, onMounted, reactive, ref, watch } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";

import { useMeetingStore } from "../stores/meetingStore";
import AppErrorAlert from "../components/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import type { MeetingCreatePayload, MeetingListParams, MeetingStatus } from "../api/types";
import { getUsers, type UserItem } from "../api/users";
import { createMeetingParticipant } from "../api/participants";
import { getTeams, type Team } from "../api/teams";
import { useAuthStore } from "../stores/authStore";

const store = useMeetingStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const filterStatus = ref<MeetingStatus | "">("");
const filterKeyword = ref("");
const filterTeamId = computed(() => {
  const raw = route.query.team_id;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : undefined;
});
const currentPage = ref(1);
const pageSize = 20;
const totalCount = ref(0);

const showCreateDialog = ref(false);
const creating = ref(false);
const createFormRef = ref<FormInstance>();
const users = ref<UserItem[]>([]);
const teams = ref<Team[]>([]);
const selectedParticipantIds = ref<number[]>([]);

const createForm = reactive<MeetingCreatePayload>({
  title: "",
  description: null,
  organizer_id: 1,
  scheduled_start_at: null,
  scheduled_end_at: null,
  location: null,
  team_id: null,
});

const canChooseOrganizer = computed(() => authStore.currentUser?.role === "admin");

const createRules: FormRules = {
  title: [{ required: true, message: t('meeting.titlePlaceholder'), trigger: "blur" }],
  organizer_id: [{ required: true, message: t('meeting.organizerRequired'), trigger: "change" }],
};

watch(
  () => route.query.create,
  (value) => {
    if (value === "1") {
      showCreateDialog.value = true;
      const nextQuery = { ...route.query };
      delete nextQuery.create;
      router.replace({ query: nextQuery });
    }
  },
  { immediate: true }
);

async function loadMeetings() {
  totalCount.value = 0;
  const params: MeetingListParams = {
    limit: pageSize,
    offset: (currentPage.value - 1) * pageSize,
  };
  if (filterTeamId.value) params.team_id = filterTeamId.value;
  if (filterStatus.value) params.status = filterStatus.value;
  if (filterKeyword.value) params.keyword = filterKeyword.value;
  await store.fetchMeetings(params);
  totalCount.value = store.meetingsTotal;
}

async function loadUsers() {
  users.value = await getUsers({ team_id: createForm.team_id ?? undefined, scope: "selectable" });
  if (!createForm.organizer_id && users.value.length > 0) {
    createForm.organizer_id = users.value[0].id;
  }
}

async function loadTeams() {
  try {
    teams.value = await getTeams();
  } catch (e) {
    console.warn(t('team.loadFailed'), e);
  }
}

watch(
  () => createForm.team_id,
  async () => {
    await loadUsers();
    if (!users.value.some((u) => u.id === createForm.organizer_id)) {
      createForm.organizer_id = users.value[0]?.id ?? (authStore.currentUser?.id ?? 1);
    }
    selectedParticipantIds.value = selectedParticipantIds.value.filter((id) => users.value.some((u) => u.id === id));
  }
);

function applyFilter() {
  currentPage.value = 1;
  loadMeetings();
}

function resetFilter() {
  filterStatus.value = "";
  filterKeyword.value = "";
  currentPage.value = 1;
  loadMeetings();
}

function handlePageChange(page: number) {
  currentPage.value = page;
  loadMeetings();
}

async function handleCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false);
  if (!valid) return;

  if (users.value.length === 0) {
    ElMessage.error(t('meeting.noOrganizer'));
    return;
  }

  creating.value = true;
  try {
    const meeting = await store.createMeeting({
      ...createForm,
      scheduled_start_at: createForm.scheduled_start_at
        ? new Date(createForm.scheduled_start_at).toISOString()
        : null,
      scheduled_end_at: createForm.scheduled_end_at
        ? new Date(createForm.scheduled_end_at).toISOString()
        : null,
    });

    if (selectedParticipantIds.value.length > 0) {
      for (const userId of selectedParticipantIds.value) {
        try {
          await createMeetingParticipant({
            meeting_id: meeting.id,
            user_id: userId,
            participant_role: "optional",
          });
        } catch (err) {
          console.warn(t('meeting.addParticipantFailed'), userId, err);
        }
      }
      ElMessage.success(t('meeting.createSuccessWithParticipants', { count: selectedParticipantIds.value.length }));
    } else {
      ElMessage.success(t('meeting.createSuccess'));
    }

    showCreateDialog.value = false;
  } catch (err) {
    notifyApiError(err, { prefix: t('meeting.createFailed') });
  } finally {
    creating.value = false;
  }
}

async function handleDelete(meetingId: number) {
  try {
    await store.removeMeeting(meetingId);
    ElMessage.success(t('meeting.deleteSuccess'));
  } catch (err) {
    notifyApiError(err, { prefix: t('meeting.deleteFailed') });
  }
}

function resetCreateForm() {
  createForm.title = "";
  createForm.description = null;
  createForm.organizer_id = authStore.currentUser?.id ?? users.value[0]?.id ?? 1;
  createForm.scheduled_start_at = null;
  createForm.scheduled_end_at = null;
  createForm.location = null;
  createForm.team_id = null;
  selectedParticipantIds.value = [];
  createFormRef.value?.resetFields();
}

function statusLabel(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    planned: t('meeting.statusPlanned'),
    ongoing: t('task.statusInProgress'),
    done: t('meeting.statusDone'),
    cancelled: t('meeting.statusCancelled'),
  };
  return map[status] ?? status;
}

function statusTagType(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    planned: "",
    ongoing: "success",
    done: "info",
    cancelled: "danger",
  };
  return map[status] ?? "";
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}

loadMeetings();
onMounted(async () => {
  await Promise.all([loadTeams()]);
  await loadUsers();
  if (!canChooseOrganizer.value && authStore.currentUser) {
    createForm.organizer_id = authStore.currentUser.id;
  }
});
</script>

<style scoped>
.meeting-list-page {
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

.filter-section {
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  padding: 24px;
  box-shadow: var(--el-box-shadow-light);
}

.filter-bar {
  margin: 0;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-bar :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.meetings-section {
  background: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  padding: 24px;
  box-shadow: var(--el-box-shadow-light);
}

.meetings-table {
  border-radius: var(--el-border-radius-small);
  overflow: hidden;
}

.meetings-table :deep(.el-table__header-wrapper th) {
  background: var(--el-fill-color-light);
  font-weight: 600;
  color: var(--el-text-color-regular);
  height: 56px;
  border-bottom: none;
}

.meetings-table :deep(.el-table__body-wrapper td) {
  padding: 16px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.meetings-table :deep(.el-table__row:hover > td) {
  background-color: var(--el-color-primary-light-9) !important;
}

.meeting-link {
  color: var(--el-text-color-primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
  transition: color 0.2s ease;
}

.meeting-link:hover {
  color: var(--el-color-primary);
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* Mobile Adjustments */
@media (max-width: 767px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filter-section {
    padding: 16px;
  }
  
  .filter-bar {
    flex-direction: column;
    width: 100%;
    gap: 12px;
  }
  
  .filter-bar :deep(.el-form-item) {
    width: 100%;
  }
  
  .filter-bar :deep(.el-select),
  .filter-bar :deep(.el-input) {
    width: 100% !important;
  }
  
  .meetings-section {
    padding: 16px;
  }
  
  .pagination {
    justify-content: center;
  }
}
</style>
