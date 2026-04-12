<template>
  <div class="conversation-list">
    <div class="list-header">
      <el-button type="primary" @click="$emit('create')">
        <el-icon><Plus /></el-icon>
        新对话
      </el-button>
    </div>
    
    <el-scrollbar>
      <div
        v-for="conv in conversations"
        :key="conv.id"
        :class="['conversation-item', { active: conv.id === currentId }]"
        @click="$emit('select', conv.id)"
      >
        <div class="conv-title">{{ conv.title }}</div>
        <div class="conv-time">{{ formatTime(conv.updatedAt || conv.updated_at || '') }}</div>
        <el-button
          v-if="conv.id === currentId"
          type="danger"
          size="small"
          text
          @click.stop="$emit('delete', conv.id)"
        >
          删除
        </el-button>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import type { Conversation } from '../../api/types'

defineProps<{
  conversations: Conversation[]
  currentId: number | null
}>()

defineEmits<{
  create: []
  select: [id: number]
  delete: [id: number]
}>()

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}
</script>

<style scoped>
.conversation-list {
  width: 280px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
}

.list-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.conversation-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background 0.2s;
}

.conversation-item:hover {
  background: var(--el-fill-color-light);
}

.conversation-item.active {
  background: var(--el-color-primary-light-9);
}

.conv-title {
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
