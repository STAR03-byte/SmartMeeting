<template>
  <div class="team-create">
    <h1>创建团队</h1>
    <el-card>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" @submit.prevent>
        <el-form-item label="团队名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入团队名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入团队描述（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">创建</el-button>
          <el-button @click="cancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { createTeam } from '../api/teams';
import { getApiErrorMessage } from '../api/client';

const router = useRouter();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({
  name: '',
  description: '',
});

const rules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入团队名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
});

const submit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await createTeam({
          name: form.name,
          description: form.description || undefined,
        });
        ElMessage.success('团队创建成功');
        router.push('/teams'); // Redirect to teams list or details
      } catch (error: any) {
        ElMessage.error(getApiErrorMessage(error));
      } finally {
        loading.value = false;
      }
    }
  });
};

const cancel = () => {
  router.back();
};
</script>

<style scoped>
.team-create {
  max-width: 600px;
  margin: 2rem auto;
}
.team-create h1 {
  margin-bottom: 2rem;
}
</style>
