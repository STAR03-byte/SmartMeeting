<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { searchMeetings } from "../api/search";
import type { SearchResult } from "../api/search";

const router = useRouter();
const route = useRoute();
const query = ref("");
const loading = ref(false);
const results = ref<SearchResult[]>([]);
const searched = ref(false);
const sourceType = ref<string>("");
const error = ref("");
const searchInputRef = ref<HTMLInputElement | null>(null);
const showHistory = ref(false);

const HISTORY_KEY = "smartmeeting_search_history";
const MAX_HISTORY = 8;

const searchHistory = ref<string[]>(loadHistory());

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(q: string) {
  const trimmed = q.trim();
  if (!trimmed) return;
  const history = searchHistory.value.filter((h) => h !== trimmed);
  history.unshift(trimmed);
  searchHistory.value = history.slice(0, MAX_HISTORY);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value));
}

function removeFromHistory(item: string) {
  searchHistory.value = searchHistory.value.filter((h) => h !== item);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value));
}

function clearHistory() {
  searchHistory.value = [];
  localStorage.removeItem(HISTORY_KEY);
}

function selectHistory(item: string) {
  query.value = item;
  showHistory.value = false;
  doSearch();
}

function onSearchBlur() {
  setTimeout(() => showHistory.value = false, 200);
}

onMounted(() => {
  const q = route.query.q;
  if (typeof q === "string" && q.trim()) {
    query.value = q;
    doSearch();
  }
  document.addEventListener("keydown", handleGlobalKey);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalKey);
});

function handleGlobalKey(e: KeyboardEvent) {
  // Ctrl+K or / to focus search (when not in input)
  if ((e.key === "k" && (e.ctrlKey || e.metaKey)) || (e.key === "/" && !isInInput(e))) {
    e.preventDefault();
    searchInputRef.value?.focus();
    showHistory.value = true;
  }
  // Escape to clear and blur
  if (e.key === "Escape") {
    if (showHistory.value) {
      showHistory.value = false;
    } else {
      query.value = "";
      searchInputRef.value?.blur();
    }
  }
}

function isInInput(e: KeyboardEvent): boolean {
  const tag = (e.target as HTMLElement).tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

const sourceTypeOptions = [
  { label: "全部", value: "" },
  { label: "转写", value: "transcript" },
  { label: "摘要", value: "summary" },
  { label: "标题", value: "title" },
  { label: "决策", value: "decision" },
  { label: "承诺", value: "commitment" },
];

const sourceTypeLabel: Record<string, string> = {
  transcript: "转写",
  summary: "摘要",
  title: "标题",
  decision: "决策",
  commitment: "承诺",
};

interface MeetingGroup {
  meetingId: number;
  meetingTitle: string;
  items: SearchResult[];
}

const groupedResults = computed<MeetingGroup[]>(() => {
  const groups = new Map<number, MeetingGroup>();
  for (const item of results.value) {
    let group = groups.get(item.meeting_id);
    if (!group) {
      group = { meetingId: item.meeting_id, meetingTitle: item.meeting_title, items: [] };
      groups.set(item.meeting_id, group);
    }
    group.items.push(item);
  }
  return Array.from(groups.values());
});

async function doSearch() {
  const q = query.value.trim();
  if (!q) return;
  loading.value = true;
  error.value = "";
  searched.value = true;
  showHistory.value = false;
  saveHistory(q);
  try {
    const res = await searchMeetings({
      q,
      source_type: sourceType.value || undefined,
    });
    results.value = res.items;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "搜索失败，请稍后重试";
    results.value = [];
  } finally {
    loading.value = false;
  }
}

function goToMeeting(meetingId: number) {
  router.push({ name: "meeting-detail", params: { id: meetingId } });
}

function highlightContent(content: string): string {
  if (!query.value.trim()) return content;
  const escaped = query.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${escaped})`, "gi");
  return content.replace(regex, '<mark class="bg-yellow-200 px-0.5 rounded">$1</mark>');
}

function snippetAround(content: string, maxLen = 200): string {
  const q = query.value.trim().toLowerCase();
  if (!q) return content.slice(0, maxLen);
  const idx = content.toLowerCase().indexOf(q);
  if (idx < 0) return content.slice(0, maxLen);
  const start = Math.max(0, idx - 60);
  const end = Math.min(content.length, idx + q.length + 140);
  let snippet = content.slice(start, end);
  if (start > 0) snippet = "..." + snippet;
  if (end < content.length) snippet = snippet + "...";
  return snippet;
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-4 sm:p-6">
    <h1 class="text-2xl font-bold mb-6">跨会议搜索</h1>

    <div class="relative mb-4">
      <form class="flex gap-2 sm:gap-3" @submit.prevent="doSearch">
        <div class="relative flex-1">
          <input
            ref="searchInputRef"
            v-model="query"
            type="text"
            placeholder="搜索会议内容、决策、承诺... (Ctrl+K)"
            class="w-full px-4 py-2.5 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            @focus="showHistory = searchHistory.length > 0"
            @blur="onSearchBlur"
          />
          <span v-if="!query" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 pointer-events-none border border-gray-300 rounded px-1.5 py-0.5">/</span>
        </div>
        <select
          v-model="sourceType"
          class="px-2 sm:px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
        >
          <option v-for="opt in sourceTypeOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <button
          type="submit"
          :disabled="loading || !query.trim()"
          class="px-4 sm:px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          {{ loading ? "搜索中..." : "搜索" }}
        </button>
      </form>

      <!-- 搜索历史下拉 -->
      <div
        v-if="showHistory && searchHistory.length > 0"
        class="absolute z-10 top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg max-h-64 overflow-y-auto"
      >
        <div class="flex items-center justify-between px-3 py-2 border-b text-xs text-gray-500">
          <span>搜索历史</span>
          <button class="text-red-400 hover:text-red-600" @mousedown.prevent="clearHistory()">清空</button>
        </div>
        <div
          v-for="item in searchHistory"
          :key="item"
          class="flex items-center justify-between px-3 py-2 hover:bg-gray-50 cursor-pointer group"
          @mousedown.prevent="selectHistory(item)"
        >
          <span class="text-sm text-gray-700">{{ item }}</span>
          <button
            class="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 text-xs"
            @mousedown.prevent.stop="removeFromHistory(item)"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>

    <div v-if="searched && !loading && groupedResults.length === 0 && !error" class="text-gray-500 text-center py-12">
      未找到相关结果
    </div>

    <div v-if="groupedResults.length > 0" class="space-y-6">
      <div class="text-sm text-gray-500 mb-2">共找到 {{ results.length }} 条结果，来自 {{ groupedResults.length }} 个会议</div>

      <div v-for="group in groupedResults" :key="group.meetingId" class="border rounded-lg overflow-hidden">
        <div
          class="bg-gray-50 px-4 py-3 flex justify-between items-center cursor-pointer hover:bg-gray-100"
          @click="goToMeeting(group.meetingId)"
        >
          <h2 class="font-semibold text-blue-700 hover:underline text-sm sm:text-base">{{ group.meetingTitle || `会议 #${group.meetingId}` }}</h2>
          <span class="text-xs sm:text-sm text-gray-500 shrink-0 ml-2">{{ group.items.length }} 条结果</span>
        </div>
        <ul class="divide-y">
          <li v-for="(item, idx) in group.items" :key="idx" class="px-4 py-3">
            <div class="flex items-start gap-2 mb-1">
              <span
                class="inline-block px-2 py-0.5 text-xs rounded-full shrink-0"
                :class="{
                  'bg-blue-100 text-blue-700': item.source_type === 'transcript',
                  'bg-green-100 text-green-700': item.source_type === 'summary',
                  'bg-purple-100 text-purple-700': item.source_type === 'title',
                  'bg-orange-100 text-orange-700': item.source_type === 'decision',
                  'bg-pink-100 text-pink-700': item.source_type === 'commitment',
                }"
              >
                {{ sourceTypeLabel[item.source_type] || item.source_type }}
              </span>
              <span class="text-xs text-gray-400">相关度 {{ (item.score * 100).toFixed(0) }}%</span>
            </div>
            <p
              class="text-sm text-gray-700"
              v-html="highlightContent(snippetAround(item.content))"
            />
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
