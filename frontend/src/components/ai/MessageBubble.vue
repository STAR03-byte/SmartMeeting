<template>
  <div :class="['message-bubble', message.role]">
    <div class="message-content">
      <div v-if="message.role === 'user'" class="user-message">
        {{ message.content }}
      </div>
      <div v-else class="assistant-message">
        <vue-markdown :source="message.content" />
      </div>
    </div>
    <div v-if="showDraftButton && taskDrafts && taskDrafts.length > 0" class="task-actions">
      <el-button
        v-for="(draft, index) in taskDrafts"
        :key="index"
        size="small"
        type="primary"
        plain
        @click="$emit('create-draft', draft)"
      >
        创建任务: {{ draft.title }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VueMarkdown from 'vue-markdown-render'
import type { ConversationMessage, TaskDraft } from '../../api/types'

const props = defineProps<{
  message: ConversationMessage
  taskDrafts?: TaskDraft[]
  isLast?: boolean
}>()

defineEmits<{
  'create-draft': [draft: TaskDraft]
}>()

const showDraftButton = computed(() => props.isLast && props.message.role === 'assistant')
</script>

<style scoped>
.message-bubble {
  margin: 12px 0;
  max-width: 80%;
}

.message-bubble.user {
  margin-left: auto;
}

.message-bubble.assistant {
  margin-right: auto;
}

.user-message {
  background: var(--el-color-primary);
  color: white;
  padding: 12px 16px;
  border-radius: 12px;
}

.assistant-message {
  background: var(--el-fill-color-light);
  padding: 12px 16px;
  border-radius: 12px;
}

.task-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
