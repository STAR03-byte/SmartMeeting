<template>
  <section class="users-page">
    <header class="hero-header">
      <div>
        <h1>用户管理</h1>
        <p>维护会议参与成员，为任务分配提供基础数据。</p>
      </div>
    </header>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

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
          <el-form-item label="角色">
            <el-select v-model="form.role">
              <el-option label="管理员" value="admin" />
              <el-option label="成员" value="member" />
            </el-select>
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password_hash" type="password" show-password placeholder="请输入密码" />
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

import { getApiErrorMessage } from "../api/client";
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
  password_hash: "hashed_password_123",
  role: "member",
});

async function refreshUsers() {
  loading.value = true;
  error.value = null;
  try {
    users.value = await getUsers();
  } catch (err) {
    error.value = getApiErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

async function submitUser() {
  submitting.value = true;
  try {
    await createUser({ ...form });
    ElMessage.success("用户创建成功");
    form.username = "";
    form.email = "";
    form.full_name = "";
    form.password_hash = "hashed_password_123";
    form.role = "member";
    await refreshUsers();
  } catch (err) {
    ElMessage.error(getApiErrorMessage(err));
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
    ElMessage.error(getApiErrorMessage(err));
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
  gap: 20px;
}

.hero-header {
  background: linear-gradient(120deg, #f3f9ff 0%, #fff6ea 100%);
  border: 1px solid #dce8f4;
  border-radius: 18px;
  padding: 24px;
}

.hero-header h1 {
  margin: 0;
  font-size: 30px;
  color: #1d2f45;
}

.hero-header p {
  margin: 8px 0 0;
  color: #4b6077;
}

.user-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
}

.base-card {
  border-radius: 12px;
}

@media (max-width: 980px) {
  .user-grid {
    grid-template-columns: 1fr;
  }
}
</style>
