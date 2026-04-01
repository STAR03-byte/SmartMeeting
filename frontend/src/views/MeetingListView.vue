<template>
  <section class="meeting-list-page">
    <header class="page-header">
      <h1>会议管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建会议
      </el-button>
    </header>

    <section class="filter-section">
      <el-form inline class="filter-bar" @submit.prevent="applyFilter">
        <el-form-item label="状态">
          <el-select v-model="filterStatus" clearable placeholder="全部" style="width: 140px">
            <el-option label="计划中" value="planned" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="done" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filterKeyword" placeholder="搜索标题/描述" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilter">筛选</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="meetings-section">
      <el-skeleton v-if="store.loading" rows="5" animated />

      <AppErrorAlert v-else-if="store.error" :error="store.error" @close="store.error = null" />

      <el-table v-else :data="store.meetings" stripe class="meetings-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="180">
          <template #default="{ row }">
            <router-link :to="`/meetings/${row.id}`" class="meeting-link">{{ row.title }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_start_at" label="计划开始" width="150">
          <template #default="{ row }">
            {{ formatDate(row.scheduled_start_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="120">
          <template #default="{ row }">
            {{ row.location || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/meetings/${row.id}`)">详情</el-button>
            <el-popconfirm title="确认删除此会议？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger" plain>删除</el-button>
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

    <el-dialog v-model="showCreateDialog" title="新建会议" width="520px" @closed="resetCreateForm">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入会议标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入会议描述（可选）" />
        </el-form-item>
        <el-form-item label="组织者" prop="organizer_id">
          <el-select
            v-model="createForm.organizer_id"
            filterable
            placeholder="请选择组织者"
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
        <el-form-item label="计划开始">
          <el-date-picker v-model="createForm.scheduled_start_at" type="datetime" placeholder="选择开始时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="计划结束">
          <el-date-picker v-model="createForm.scheduled_end_at" type="datetime" placeholder="选择结束时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="createForm.location" placeholder="会议地点（可选）" />
        </el-form-item>
        <el-form-item label="参与者">
          <el-select
            v-model="selectedParticipantIds"
            multiple
            filterable
            clearable
            placeholder="选择参与人员（可选）"
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
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { Plus } from "@element-plus/icons-vue";

import { useMeetingStore } from "../stores/meetingStore";
import AppErrorAlert from "../components/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import type { MeetingCreatePayload, MeetingListParams, MeetingStatus } from "../api/types";
import { getUsers, type UserItem } from "../api/users";
import { createMeetingParticipant } from "../api/participants";

const store = useMeetingStore();

const filterStatus = ref<MeetingStatus | "">("");
const filterKeyword = ref("");
const currentPage = ref(1);
const pageSize = 20;
const totalCount = ref(0);

const showCreateDialog = ref(false);
const creating = ref(false);
const createFormRef = ref<FormInstance>();
const users = ref<UserItem[]>([]);
const selectedParticipantIds = ref<number[]>([]);

const createForm = reactive<MeetingCreatePayload>({
  title: "",
  description: null,
  organizer_id: 1,
  scheduled_start_at: null,
  scheduled_end_at: null,
  location: null,
});

const createRules: FormRules = {
  title: [{ required: true, message: "请输入会议标题", trigger: "blur" }],
  organizer_id: [{ required: true, message: "请选择组织者", trigger: "change" }],
};

async function loadMeetings() {
  totalCount.value = 0;
  const params: MeetingListParams = {
    limit: pageSize,
    offset: (currentPage.value - 1) * pageSize,
  };
  if (filterStatus.value) params.status = filterStatus.value;
  if (filterKeyword.value) params.keyword = filterKeyword.value;
  await store.fetchMeetings(params);
  totalCount.value = store.meetingsTotal;
}

async function loadUsers() {
  users.value = await getUsers();
  if (!createForm.organizer_id && users.value.length > 0) {
    createForm.organizer_id = users.value[0].id;
  }
}

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
    ElMessage.error("暂无可选组织者，请先创建用户");
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
          console.warn("添加参与者失败:", userId, err);
        }
      }
      ElMessage.success(`会议创建成功，已添加 ${selectedParticipantIds.value.length} 位参与者`);
    } else {
      ElMessage.success("会议创建成功");
    }

    showCreateDialog.value = false;
  } catch (err) {
    notifyApiError(err, { prefix: "创建失败" });
  } finally {
    creating.value = false;
  }
}

async function handleDelete(meetingId: number) {
  try {
    await store.removeMeeting(meetingId);
    ElMessage.success("会议已删除");
  } catch (err) {
    notifyApiError(err, { prefix: "删除失败" });
  }
}

function resetCreateForm() {
  createForm.title = "";
  createForm.description = null;
  createForm.organizer_id = users.value[0]?.id ?? 1;
  createForm.scheduled_start_at = null;
  createForm.scheduled_end_at = null;
  createForm.location = null;
  selectedParticipantIds.value = [];
  createFormRef.value?.resetFields();
}

function statusLabel(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    planned: "计划中",
    ongoing: "进行中",
    done: "已结束",
    cancelled: "已取消",
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
  await loadUsers();
});
</script>

<style scoped>
:root {
  --primary: #6366F1;
  --primary-light: #818CF8;
  --bg: #0F172A;
  --bg-light: #1E293B;
  --card: #1E293B;
  --card-hover: #334155;
  --border: #334155;
  --text: #F8FAFC;
  --text-muted: #94A3B8;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

.meeting-list-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100vh;
  background: var(--bg);
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
}

.page-header :deep(.el-button--primary) {
  background: var(--primary);
  border-color: var(--primary);
}

.filter-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
}

.filter-bar {
  margin: 0;
}

.filter-bar :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-bar :deep(.el-select .el-input__wrapper) {
  border-radius: var(--radius-sm);
}

.filter-bar :deep(.el-button--primary) {
  background: var(--primary);
  border-color: var(--primary);
}

.meetings-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 20px;
}

.meetings-table {
  border-radius: var(--radius-sm);
}

.meetings-table :deep(.el-table th) {
  background: var(--bg);
  font-weight: 600;
  color: var(--text-muted);
}

.meetings-table :deep(.el-table td) {
  padding: 14px 0;
}

.meeting-link {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

.meeting-link:hover {
  color: var(--primary-light);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.pagination :deep(.el-pager li.is-active) {
  background: var(--primary);
}
</style>