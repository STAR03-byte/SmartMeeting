<template>
  <div class="chat-window" ref="chatWindowRef">
    <div v-if="messages.length === 0" class="empty-state">
      <el-empty description="开始新的对话" />
    </div>
    
    <MessageBubble
      v-for="(msg, index) in messages"
      :key="msg.id"
      :message="msg"
      :is-last="index === messages.length - 1 && !isStreaming"
      :task-drafts="getTaskDrafts(msg)"
      @create-draft="$emit('create-draft', $event)"
    />
    
    <MessageBubble
      v-if="isStreaming && streamingMessage"
      :message="{ id: -1, role: 'assistant', content: streamingMessage, conversationId: 0, createdAt: '' }"
      :is-last="true"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'
import type { ConversationMessage, TaskDraft } from '../../api/types'

const props = defineProps<{
  messages: ConversationMessage[]
  isStreaming?: boolean
  streamingMessage?: string
}>()

defineEmits<{
  'create-draft': [draft: TaskDraft]
}>()

const chatWindowRef = ref<HTMLElement | null>(null)

// 解析消息中的任务提取标记
function getTaskDrafts(message: ConversationMessage): TaskDraft[] {
  const match = message.content.match(/<!-- TASK_EXTRACTION: (\[.*?\]) -->/)
  if (!match) return []
  
  try {
    return JSON.parse(match[1])
  } catch {
    return []
  }
}

// 自动滚动到底部
watch(
  () => [props.messages.length, props.streamingMessage],
  () => {
    nextTick(() => {
      if (chatWindowRef.value) {
        chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
      }
    })
  }
)
</script>

<style scoped>
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
