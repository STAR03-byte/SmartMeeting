<template>
  <section class="users-page">
    <header class="hero-header">
      <div>
        <h1>用户管理</h1>
        <p>维护会议参与成员，为任务分配提供基础数据。</p>
      </div>
    </header>

    <AppErrorAlert :error="error" :closable="false" />

    <div class="user-grid">
      <el-card class="base-card">
        <template #header>新增用户</template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="form.full_name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="角色" placeholder="请选择用户角色">
            <el-select v-model="form.role" placeholder="请选择用户角色">
              <el-option label="管理员（可管理所有会议和用户）" value="admin" />
              <el-option label="成员（可参与会议和任务）" value="member" />
            </el-select>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password_hash" type="password" show-password placeholder="请设置登录密码（至少8位）" />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="confirmPassword" type="password" show-password placeholder="请再次输入密码" />
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitUser">创建用户</el-button>
        </el-form>
      </el-card>

      <el-card class="base-card" v-loading="loading">
        <template #header>现有用户</template>
        <el-table :data="users" stripe>
          <el-table-column prop="full_name" label="姓名" min-width="140" />
          <el-table-column prop="username" label="用户名" min-width="140" />
          <el-table-column prop="email" label="邮箱" min-width="220" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
                {{ row.role === "admin" ? "管理员" : "成员" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-popconfirm title="确认删除此用户？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" plain>删除</el-button>
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
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import AppErrorAlert from "../components/AppErrorAlert.vue";
import { notifyApiError } from "../utils/notify";
import { createUser, deleteUser, getUsers, type UserItem, type UserRole } from "../api/users";

const users = ref<UserItem[]>([]);
const loading = ref(false);
const submitting = ref(false);
const error = ref<string | null>(null);

const form = reactive<{
  username: string;
  email: string;
  full_name: string;
  password_hash: string;
  role: UserRole;
}>({
  username: "",
  email: "",
  full_name: "",
  password_hash: "",
  role: "member",
});

const confirmPassword = ref("");

async function refreshUsers() {
  loading.value = true;
  error.value = null;
  try {
    users.value = await getUsers();
  } catch (err) {
    error.value = notifyApiError(err, { prefix: "加载用户失败" });
  } finally {
    loading.value = false;
  }
}

async function submitUser() {
  if (!form.username || form.username.length < 3) {
    ElMessage.warning("用户名至少需要3个字符");
    return;
  }
  if (!form.email) {
    ElMessage.warning("请输入邮箱地址");
    return;
  }
  if (!form.full_name) {
    ElMessage.warning("请输入姓名");
    return;
  }
  if (!form.password_hash || form.password_hash.length < 8) {
    ElMessage.warning("密码至少需要8个字符");
    return;
  }
  if (form.password_hash !== confirmPassword.value) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }

  submitting.value = true;
  try {
    await createUser({ ...form });
    ElMessage.success("用户创建成功");
    form.username = "";
    form.email = "";
    form.full_name = "";
    form.password_hash = "";
    confirmPassword.value = "";
    form.role = "member";
    await refreshUsers();
  } catch (err) {
    notifyApiError(err);
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(userId: number) {
  try {
    await deleteUser(userId);
    ElMessage.success("已删除");
    await refreshUsers();
  } catch (err) {
    notifyApiError(err);
  }
}

onMounted(async () => {
  await refreshUsers();
});
</script>

<style scoped>
.users-page {
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
  letter-spacing: -0.5px;
}

.hero-header p {
  margin: 12px 0 0;
  color: var(--el-color-primary);
  font-size: 16px;
}

.user-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
}

.base-card {
  border-radius: var(--el-border-radius-base);
  border: none;
  box-shadow: var(--el-box-shadow-light) !important;
  background: var(--el-bg-color);
}

.base-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.base-card :deep(.el-card__body) {
  padding: 24px;
}

/* Custom Table Styles */
:deep(.el-table) {
  --el-table-border-color: var(--el-border-color-lighter);
  --el-table-header-bg-color: var(--el-fill-color-light);
  --el-table-row-hover-bg-color: var(--el-color-primary-light-9);
}

:deep(.el-table__header-wrapper th) {
  height: 56px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  border-bottom: none;
}

:deep(.el-table__body-wrapper td) {
  padding: 16px 0;
}

@media (max-width: 980px) {
  .user-grid {
    grid-template-columns: 1fr;
  }
}
</style>
