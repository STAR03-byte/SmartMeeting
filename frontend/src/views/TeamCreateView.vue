<template>
  <div class="team-create">
    <h1>{{ $t('team.createTeam') }}</h1>
    <el-card>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" @submit.prevent>
        <el-form-item :label="$t('team.teamName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('team.teamNameRequired')" />
        </el-form-item>
        <el-form-item :label="$t('task.taskDescription')" prop="description">
          <el-input v-model="form.description" type="textarea" :placeholder="$t('team.teamDescriptionPlaceholder')" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">{{ $t('common.create') }}</el-button>
          <el-button @click="cancel">{{ $t('common.cancel') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
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
    { required: true, message: t('team.teamNameRequired'), trigger: 'blur' },
    { min: 2, max: 50, message: t('team.teamNameLength'), trigger: 'blur' },
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
        ElMessage.success(t('team.createSuccess'));
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
