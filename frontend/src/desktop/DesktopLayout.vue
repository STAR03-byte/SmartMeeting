<script setup lang="ts">
import { ref } from "vue";
import RecordingControls from "./RecordingControls.vue";
import SettingsView from "./SettingsView.vue";
import MeetingHistory from "./MeetingHistory.vue";

const activeTab = ref<"record" | "history" | "settings">("record");
</script>

<template>
  <div class="desktop-layout">
    <nav class="sidebar">
      <div class="logo">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
        </svg>
        <span>SmartMeeting</span>
      </div>

      <div class="nav-items">
        <button
          :class="['nav-item', { active: activeTab === 'record' }]"
          @click="activeTab = 'record'"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="4" fill="currentColor" />
          </svg>
          <span>录制</span>
        </button>

        <button
          :class="['nav-item', { active: activeTab === 'history' }]"
          @click="activeTab = 'history'"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>历史</span>
        </button>

        <button
          :class="['nav-item', { active: activeTab === 'settings' }]"
          @click="activeTab = 'settings'"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>设置</span>
        </button>
      </div>
    </nav>

    <main class="content">
      <RecordingControls v-if="activeTab === 'record'" />
      <MeetingHistory v-else-if="activeTab === 'history'" />
      <SettingsView v-else-if="activeTab === 'settings'" />
    </main>
  </div>
</template>

<style scoped>
.desktop-layout {
  display: flex;
  height: 100vh;
  background: var(--el-bg-color-page);
}

.sidebar {
  width: 200px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  margin-bottom: 32px;
  color: var(--el-color-primary);
}

.logo span {
  font-size: 18px;
  font-weight: 700;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--el-text-color-regular);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
}

.nav-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
