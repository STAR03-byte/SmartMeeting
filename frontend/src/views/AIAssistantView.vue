<template>
  <section class="ai-assistant-page">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">AI 助理</span>
      </template>
    </el-page-header>

    <el-card class="main-card">
      <div class="chat-container">
        <ConversationList
          :conversations="store.sortedConversations"
          :current-id="currentConversationId"
          @create="handleCreateConversation"
          @select="handleSelectConversation"
          @delete="handleDeleteConversation"
        />
        
        <div class="chat-main">
          <div class="knowledge-panel">
            <div class="knowledge-header">
              <span>会议知识问答</span>
              <el-tag size="small" type="success">带来源</el-tag>
            </div>
            <div class="knowledge-query">
              <el-input
                v-model="knowledgeQuestion"
                placeholder="查询历史会议中的决策、风险、任务或参会人"
                clearable
                @keyup.enter="handleKnowledgeQuery"
              />
              <el-button type="primary" :loading="knowledgeLoading" @click="handleKnowledgeQuery">查询</el-button>
            </div>
            <div v-if="knowledgeAnswer" class="knowledge-answer">
              <p>{{ knowledgeAnswer }}</p>
              <div v-if="knowledgeSources.length > 0" class="knowledge-sources">
                <div v-for="source in knowledgeSources" :key="`${source.meeting_id}-${source.source_type}-${source.snippet}`" class="knowledge-source">
                  <div class="source-title">{{ source.meeting_title }}</div>
                  <el-tag size="small" type="info">{{ sourceTypeLabel(source.source_type) }}</el-tag>
                  <span class="source-snippet">{{ source.snippet }}</span>
                </div>
              </div>
            </div>
          </div>

          <ChatWindow
            :messages="store.messages"
            :is-streaming="store.isStreaming"
            :streaming-message="streamingContent"
            @create-draft="handleCreateDraft"
          />
          
          <ChatInput
            :disabled="store.isLoading"
            :is-streaming="store.isStreaming"
            :context-hint="contextHint"
            placeholder="输入消息，按 Enter 发送，Shift+Enter 换行..."
            @send="handleSendMessage"
            @clear-context="clearContext"
            @select-context="openContextSelector"
          />
        </div>
      </div>
    </el-card>

    <!-- 上下文选择对话框 -->
    <el-dialog
      v-model="contextDialogVisible"
      title="选择对话上下文"
      width="500px"
    >
      <el-tabs v-model="contextType" @tab-change="onContextTabChange">
        <el-tab-pane label="会议" name="meeting">
          <el-scrollbar max-height="300px">
            <div
              v-for="meeting in meetingList"
              :key="meeting.id"
              class="context-item"
              @click="selectMeetingContext(meeting.id, meeting.title)"
            >
              <span class="context-title">{{ meeting.title }}</span>
              <el-button size="small" type="primary" text>选择</el-button>
            </div>
            <el-empty v-if="meetingList.length === 0" description="暂无会议" />
          </el-scrollbar>
        </el-tab-pane>
        <el-tab-pane label="任务" name="task">
          <el-scrollbar max-height="300px">
            <div
              v-for="task in taskList"
              :key="task.id"
              class="context-item"
              @click="selectTaskContext(task.id, task.title)"
            >
              <span class="context-title">#{{ task.id }} {{ task.title }}</span>
              <el-button size="small" type="primary" text>选择</el-button>
            </div>
            <el-empty v-if="taskList.length === 0" description="暂无任务" />
          </el-scrollbar>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 任务草稿确认对话框 -->
    <el-dialog
      v-model="draftDialogVisible"
      title="创建任务草稿"
      width="500px"
    >
      <el-form :model="draftForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="draftForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="draftForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="draftForm.priority">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="draftDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDraft">确认创建</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationList from '../components/ai/ConversationList.vue'
import ChatWindow from '../components/ai/ChatWindow.vue'
import ChatInput from '../components/ai/ChatInput.vue'
import { useAiAssistantStore } from '../stores/aiAssistantStore'
import type { KnowledgeSource, TaskDraft, CreateTaskDraftPayload, ChatContext } from '../api/types'
import { getMeetings } from '../api/meetings'
import { getTasks } from '../api/tasks'
import { queryMeetingKnowledge } from '../api/ai'

const router = useRouter()
const store = useAiAssistantStore()

const currentConversationId = ref<number | null>(null)
const knowledgeQuestion = ref('')
const knowledgeAnswer = ref('')
const knowledgeSources = ref<KnowledgeSource[]>([])
const knowledgeLoading = ref(false)
const draftDialogVisible = ref(false)
const draftForm = ref<Partial<TaskDraft>>({
  title: '',
  description: '',
  priority: 'medium'
})

// 流式内容（从 store 的当前助手消息中提取）
const streamingContent = computed(() => {
  if (!store.isStreaming) return ''
  const lastMessage = store.messages[store.messages.length - 1]
  if (lastMessage?.role === 'assistant') {
    return lastMessage.content
  }
  return ''
})

// 上下文提示
const contextMeetingId = ref<number | null>(null)
const contextTaskIds = ref<number[]>([])

// 上下文选择相关
const contextDialogVisible = ref(false)
const contextType = ref<'meeting' | 'task'>('meeting')
const meetingList = ref<Array<{ id: number; title: string }>>([])
const taskList = ref<Array<{ id: number; title: string }>>([])

const contextHint = computed(() => {
  if (contextMeetingId.value) {
    return `会议 #${contextMeetingId.value}`
  }
  if (contextTaskIds.value.length > 0) {
    return `任务 #${contextTaskIds.value.join(', #')}`
  }
  return undefined
})

function clearContext() {
  contextMeetingId.value = null
  contextTaskIds.value = []
}

async function handleKnowledgeQuery() {
  const question = knowledgeQuestion.value.trim()
  if (!question) {
    ElMessage.warning('请输入要查询的问题')
    return
  }

  knowledgeLoading.value = true
  try {
    const result = await queryMeetingKnowledge({ question, limit: 6 })
    knowledgeAnswer.value = result.answer
    knowledgeSources.value = result.sources
    if (result.sources.length === 0) {
      ElMessage.info('没有找到可访问的会议来源')
    }
  } catch (err) {
    ElMessage.error('知识问答查询失败')
  } finally {
    knowledgeLoading.value = false
  }
}

function sourceTypeLabel(type: KnowledgeSource['source_type']): string {
  const map: Record<KnowledgeSource['source_type'], string> = {
    meeting: '会议',
    summary: '纪要',
    transcript: '转写',
    task: '任务',
    participant: '参会人'
  }
  return map[type]
}

async function openContextSelector() {
  contextDialogVisible.value = true
  contextType.value = 'meeting'
  await loadMeetingList()
}

async function loadMeetingList() {
  try {
    const result = await getMeetings({ limit: 50 })
    meetingList.value = result.items.map(m => ({ id: m.id, title: m.title }))
  } catch {
    meetingList.value = []
  }
}

async function loadTaskList() {
  try {
    const result = await getTasks({ limit: 50 })
    taskList.value = result.items.map(t => ({ id: t.id, title: t.title }))
  } catch {
    taskList.value = []
  }
}

function selectMeetingContext(meetingId: number, title: string) {
  contextMeetingId.value = meetingId
  contextTaskIds.value = []
  contextDialogVisible.value = false
  ElMessage.success(`已关联会议：${title}`)
}

function selectTaskContext(taskId: number, title: string) {
  contextMeetingId.value = null
  contextTaskIds.value = [taskId]
  contextDialogVisible.value = false
  ElMessage.success(`已关联任务：${title}`)
}

async function onContextTabChange(tabName: string | number) {
  if (tabName === 'meeting') {
    await loadMeetingList()
  } else if (tabName === 'task') {
    await loadTaskList()
  }
}

onMounted(async () => {
  await store.fetchConversations()
  if (store.sortedConversations.length > 0) {
    await handleSelectConversation(store.sortedConversations[0].id)
  }
})

function goBack() {
  router.push('/')
}

async function handleNewConversation() {
  try {
    const conv = await store.createConversation()
    currentConversationId.value = conv.id
    ElMessage.success('新对话已创建')
  } catch (err) {
    ElMessage.error('创建对话失败')
  }
}

async function handleSelectConversation(id: number) {
  try {
    currentConversationId.value = id
    await store.selectConversation(id)
  } catch (err) {
    ElMessage.error('加载对话失败')
  }
}

async function handleDeleteConversation(id: number) {
  try {
    await ElMessageBox.confirm('确定删除此对话？', '删除确认', { type: 'warning' })
    await store.deleteConversation(id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
    }
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

async function handleCreateConversation() {
  try {
    const title = await ElMessageBox.prompt('对话标题', '新建对话', {
      inputValue: '新对话',
      confirmButtonText: '创建',
      cancelButtonText: '取消'
    }).then(r => r.value).catch(() => null)
    
    if (title) {
      const conv = await store.createConversation(title)
      currentConversationId.value = conv.id
    }
  } catch {
    // 用户取消
  }
}

async function handleSendMessage(message: string) {
  const context: ChatContext | undefined = contextMeetingId.value || contextTaskIds.value.length > 0
    ? {
        meetingId: contextMeetingId.value || undefined,
        taskIds: contextTaskIds.value.length > 0 ? contextTaskIds.value : undefined
      }
    : undefined
  
  try {
    await store.sendMessage(message, context)
  } catch (err) {
    ElMessage.error(store.error || '发送消息失败')
  }
}

function handleCreateDraft(draft: TaskDraft) {
  draftForm.value = { 
    title: draft.title,
    description: draft.description || '',
    priority: draft.priority || 'medium',
    meetingId: draft.meetingId || draft.meeting_id
  }
  draftDialogVisible.value = true
}

async function confirmDraft() {
  if (!draftForm.value.title) {
    ElMessage.warning('请输入任务标题')
    return
  }
  
  try {
    const payload: CreateTaskDraftPayload = {
      meeting_id: draftForm.value.meetingId || draftForm.value.meeting_id || 0,
      title: draftForm.value.title,
      description: draftForm.value.description || '',
      due_date: new Date().toISOString(),
      priority: draftForm.value.priority as 'high' | 'medium' | 'low',
      assignee_id: 0
    }
    await store.createTaskDraft(payload)
    ElMessage.success('任务草稿已创建')
    draftDialogVisible.value = false
  } catch (err) {
    ElMessage.error('创建任务草稿失败')
  }
}
</script>

<style scoped>
.ai-assistant-page {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.main-card {
  flex: 1;
  overflow: hidden;
}

.main-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.chat-container {
  display: flex;
  height: 100%;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.knowledge-panel {
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}

.knowledge-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.knowledge-query {
  display: flex;
  gap: 8px;
}

.knowledge-answer {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-small);
}

.knowledge-answer p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.knowledge-sources {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.knowledge-source {
  display: grid;
  grid-template-columns: minmax(120px, 180px) auto 1fr;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.source-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-snippet {
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background 0.2s;
}

.context-item:hover {
  background: var(--el-fill-color-light);
}

.context-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

@media (max-width: 767px) {
  .knowledge-query {
    flex-direction: column;
  }

  .knowledge-source {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }
}
</style>
