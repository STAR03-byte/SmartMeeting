<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      :placeholder="placeholder"
      :disabled="disabled"
      @keydown.enter.exact.prevent="handleSend"
      @keydown.enter.shift.exact="() => {}"
    />
    <div class="input-toolbar">
      <div class="toolbar-left">
        <el-button size="small" text @click="$emit('select-context')">
          <el-icon><Link /></el-icon>
          选择上下文
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button
          type="primary"
          :disabled="!inputText.trim() || disabled"
          :loading="isStreaming"
          @click="handleSend"
        >
          {{ isStreaming ? '发送中...' : '发送' }}
        </el-button>
      </div>
    </div>
    <div v-if="contextHint" class="context-hint">
      <el-tag size="small" type="info">
        📎 {{ contextHint }}
      </el-tag>
      <el-button size="small" text @click="$emit('clear-context')">
        清除
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Link } from '@element-plus/icons-vue'

const props = defineProps<{
  disabled?: boolean
  placeholder?: string
  isStreaming?: boolean
  contextHint?: string
}>()

const emit = defineEmits<{
  send: [message: string]
  'clear-context': []
  'select-context': []
}>()

const inputText = ref('')

function handleSend() {
  const trimmed = inputText.value.trim()
  if (trimmed && !props.disabled) {
    emit('send', trimmed)
    inputText.value = ''
  }
}
</script>

<style scoped>
.chat-input {
  padding: 16px;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
}

.input-toolbar {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.toolbar-right {
  display: flex;
}

.context-hint {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
