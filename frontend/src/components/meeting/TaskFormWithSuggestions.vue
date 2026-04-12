<template>
  <div class="task-form-with-suggestions">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="输入任务标题" @input="debouncedFetchSuggestions" />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="3" 
          placeholder="输入任务描述"
          @input="debouncedFetchSuggestions" 
        />
      </el-form-item>
      
      <el-form-item label="截止日期">
        <el-date-picker 
          v-model="form.due_at" 
          type="datetime" 
          placeholder="选择截止日期"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="优先级">
        <el-select v-model="form.priority" style="width: 100%">
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="负责人">
        <el-select v-model="form.assignee_id" filterable placeholder="选择负责人" style="width: 100%">
          <el-option
            v-for="p in participants"
            :key="p.user_id"
            :label="p.full_name"
            :value="p.user_id"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="props.isEdit" label="提醒时间">
        <el-date-picker
          v-model="form.reminder_at"
          type="datetime"
          placeholder="选择提醒时间"
          style="width: 100%"
        />
      </el-form-item>

      <!-- AI 建议按钮和区域 -->
      <el-form-item>
        <el-button 
          type="info" 
          :loading="loadingSuggestions"
          @click="fetchSuggestions"
        >
          <el-icon><MagicStick /></el-icon>
          获取 AI 建议
        </el-button>
      </el-form-item>
      
      <el-collapse v-if="suggestions && showSuggestions" v-model="activeCollapse">
        <el-collapse-item title="🤖 AI 建议" name="suggestions">
          <div v-if="suggestions.steps && suggestions.steps.length" class="suggestion-section">
            <h4>执行步骤</h4>
            <ol>
              <li v-for="(step, i) in suggestions.steps" :key="i" class="suggestion-item">
                {{ step }}
                <el-button size="small" text type="primary" @click="insertToDescription(step)">
                  插入
                </el-button>
              </li>
            </ol>
          </div>
          
          <div v-if="suggestions.risks && suggestions.risks.length" class="suggestion-section">
            <h4>潜在风险</h4>
            <ul>
              <li v-for="(risk, i) in suggestions.risks" :key="i" class="suggestion-item">
                {{ risk }}
              </li>
            </ul>
          </div>
          
          <div v-if="suggestions.suggestedRoles && suggestions.suggestedRoles.length" class="suggestion-section">
            <h4>建议角色</h4>
            <el-tag v-for="role in suggestions.suggestedRoles" :key="role" class="mr-1" type="success">
              {{ role }}
            </el-tag>
          </div>
          
          <div v-if="suggestions.relatedTasks && suggestions.relatedTasks.length" class="suggestion-section">
            <h4>相关任务</h4>
            <el-tag
              v-for="task in suggestions.relatedTasks"
              :key="task.id"
              type="info"
              class="mr-1"
            >
              #{{ task.id }} {{ task.title }}
            </el-tag>
          </div>
        </el-collapse-item>
      </el-collapse>
      
      <el-form-item class="form-actions">
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ submitting ? (props.isEdit ? '保存中...' : '创建中...') : (props.isEdit ? '保存任务' : '创建任务') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { getTaskSuggestions } from '../../api/ai'
import type { TaskSuggestions, MeetingParticipantOut } from '../../api/types'

type TaskFormSubmitPayload = {
  title: string
  description: string
  due_at: Date | null
  priority: 'high' | 'medium' | 'low'
  assignee_id: number | null
  meeting_id: number
  reminder_at?: Date | null
}

interface TaskFormData {
  title: string
  description: string
  due_at: Date | null
  priority: 'high' | 'medium' | 'low'
  assignee_id: number | null
  reminder_at?: Date | null
}

const props = defineProps<{
  meetingId: number
  participants: MeetingParticipantOut[]
  initialData?: TaskFormData
  isEdit?: boolean
}>()

const emit = defineEmits<{
  submit: [form: TaskFormSubmitPayload]
  cancel: []
}>()

const formRef = ref<FormInstance>()
const form = ref<TaskFormData & { reminder_at?: Date | null }>({
  title: props.initialData?.title ?? '',
  description: props.initialData?.description ?? '',
  due_at: props.initialData?.due_at ?? null,
  priority: props.initialData?.priority ?? 'medium',
  assignee_id: props.initialData?.assignee_id ?? null,
  reminder_at: (props.initialData as any)?.reminder_at ?? null
})

const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }]
}

const suggestions = ref<TaskSuggestions | null>(null)
const loadingSuggestions = ref(false)
const showSuggestions = ref(false)
const submitting = ref(false)
const activeCollapse = ref(['suggestions'])

// 防抖函数
let debounceTimer: ReturnType<typeof setTimeout> | null = null
function debouncedFetchSuggestions() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    if (form.value.title.trim().length > 3) {
      fetchSuggestions()
    }
  }, 1000)
}

async function fetchSuggestions() {
  if (!form.value.title.trim()) {
    return
  }
  
  loadingSuggestions.value = true
  try {
    suggestions.value = await getTaskSuggestions(
      form.value.title,
      form.value.description || undefined,
      props.meetingId
    )
    showSuggestions.value = true
  } catch (err) {
    ElMessage.error('获取 AI 建议失败，请稍后重试')
  } finally {
    loadingSuggestions.value = false
  }
}

function insertToDescription(text: string) {
  form.value.description = (form.value.description ? form.value.description + '\n' : '') + text
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    const payload: TaskFormSubmitPayload & { reminder_at?: Date | null; meeting_id: number } = {
      ...form.value,
      meeting_id: props.meetingId
    }
    // 如果不是编辑模式，删除reminder_at字段
    if (!props.isEdit) {
      delete payload.reminder_at
    }
    emit('submit', payload)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.task-form-with-suggestions {
  padding: 8px;
}

.suggestion-section {
  margin: 12px 0;
}

.suggestion-section h4 {
  margin: 8px 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.suggestion-item {
  margin: 4px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mr-1 {
  margin-right: 4px;
  margin-bottom: 4px;
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>
