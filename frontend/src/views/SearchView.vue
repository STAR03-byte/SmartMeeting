<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
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

onMounted(() => {
  const q = route.query.q;
  if (typeof q === "string" && q.trim()) {
    query.value = q;
    doSearch();
  }
});

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
  if (!query.value.trim()) return;
  loading.value = true;
  error.value = "";
  searched.value = true;
  try {
    const res = await searchMeetings({
      q: query.value,
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
</script>

<template>
  <div class="max-w-4xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-6">跨会议搜索</h1>

    <form class="flex gap-3 mb-4" @submit.prevent="doSearch">
      <input
        v-model="query"
        type="text"
        placeholder="输入关键词搜索会议内容、决策、承诺..."
        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        v-model="sourceType"
        class="px-3 py-2 border border-gray-300 rounded-lg bg-white"
      >
        <option v-for="opt in sourceTypeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <button
        type="submit"
        :disabled="loading || !query.trim()"
        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? "搜索中..." : "搜索" }}
      </button>
    </form>

    <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg">
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
          <h2 class="font-semibold text-blue-700 hover:underline">{{ group.meetingTitle || `会议 #${group.meetingId}` }}</h2>
          <span class="text-sm text-gray-500">{{ group.items.length }} 条结果</span>
        </div>
        <ul class="divide-y">
          <li v-for="(item, idx) in group.items" :key="idx" class="px-4 py-3">
            <div class="flex items-start gap-2 mb-1">
              <span
                class="inline-block px-2 py-0.5 text-xs rounded-full"
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
              class="text-sm text-gray-700 line-clamp-3"
              v-html="highlightContent(item.content)"
            />
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
