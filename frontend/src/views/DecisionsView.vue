<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { listDecisions, updateDecision, deleteDecision } from "../api/decisions";
import type { Decision } from "../api/decisions";

const router = useRouter();
const loading = ref(false);
const decisions = ref<Decision[]>([]);
const total = ref(0);
const statusFilter = ref<string>("");
const page = ref(1);
const pageSize = 20;

const statusOptions = [
  { label: "全部", value: "" },
  { label: "待确认", value: "candidate" },
  { label: "已确认", value: "confirmed" },
  { label: "已拒绝", value: "rejected" },
];

const statusLabel: Record<string, string> = {
  candidate: "待确认",
  confirmed: "已确认",
  rejected: "已拒绝",
};

const statusTag: Record<string, string> = {
  candidate: "warning",
  confirmed: "success",
  rejected: "danger",
};

async function loadDecisions() {
  loading.value = true;
  try {
    const res = await listDecisions({
      status: statusFilter.value || undefined,
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    });
    decisions.value = res.items;
    total.value = res.total;
  } finally {
    loading.value = false;
  }
}

async function confirmDecision(d: Decision) {
  await updateDecision(d.id, { status: "confirmed" });
  await loadDecisions();
}

async function rejectDecision(d: Decision) {
  await updateDecision(d.id, { status: "rejected" });
  await loadDecisions();
}

async function removeDecision(d: Decision) {
  await deleteDecision(d.id);
  await loadDecisions();
}

function goToMeeting(meetingId: number) {
  router.push({ name: "meeting-detail", params: { id: meetingId } });
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}

function confidenceColor(conf: number | null): string {
  if (conf === null) return "";
  if (conf >= 0.8) return "text-green-600";
  if (conf >= 0.5) return "text-yellow-600";
  return "text-red-600";
}

function exportMarkdown() {
  const lines: string[] = ["# 决策导出\n", `> 导出时间：${new Date().toLocaleString("zh-CN")}\n`];
  const grouped = new Map<number, Decision[]>();
  for (const d of decisions.value) {
    const arr = grouped.get(d.meeting_id) || [];
    arr.push(d);
    grouped.set(d.meeting_id, arr);
  }
  for (const [meetingId, items] of grouped) {
    lines.push(`## 会议 #${meetingId}\n`);
    for (const d of items) {
      const conf = d.confidence !== null ? ` (置信度 ${(d.confidence * 100).toFixed(0)}%)` : "";
      lines.push(`- **[${statusLabel[d.status] || d.status}]${conf}** ${d.content}`);
      if (d.proposer_name) lines.push(`  - 提出者：${d.proposer_name}`);
      if (d.context) lines.push(`  - 背景：${d.context}`);
      lines.push(`  - 时间：${formatDate(d.created_at)}`);
    }
    lines.push("");
  }
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `decisions-${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

onMounted(loadDecisions);
</script>

<template>
  <div class="max-w-5xl mx-auto p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-xl sm:text-2xl font-bold">决策管理</h1>
      <div class="flex items-center gap-2">
        <button
          v-if="decisions.length > 0"
          class="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50"
          @click="exportMarkdown"
        >
          导出 Markdown
        </button>
        <select v-model="statusFilter" class="px-3 py-2 border rounded-lg text-sm" @change="loadDecisions">
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>

    <div v-else-if="decisions.length === 0" class="text-center py-12 text-gray-500">
      暂无决策记录
    </div>

    <div v-else class="space-y-4">
      <div class="text-sm text-gray-500 mb-2">共 {{ total }} 条决策</div>

      <div
        v-for="d in decisions"
        :key="d.id"
        class="border rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span
              class="px-2 py-0.5 text-xs rounded-full"
              :class="{
                'bg-yellow-100 text-yellow-700': d.status === 'candidate',
                'bg-green-100 text-green-700': d.status === 'confirmed',
                'bg-red-100 text-red-700': d.status === 'rejected',
              }"
            >
              {{ statusLabel[d.status] || d.status }}
            </span>
            <span v-if="d.confidence !== null" :class="confidenceColor(d.confidence)" class="text-xs">
              置信度 {{ (d.confidence * 100).toFixed(0) }}%
            </span>
            <span
              v-if="d.confidence !== null && d.confidence < 0.6 && d.status === 'candidate'"
              class="text-xs text-orange-600"
            >
              (低置信度，请审核)
            </span>
          </div>
          <div class="flex gap-1 shrink-0">
            <button
              v-if="d.status === 'candidate'"
              class="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100"
              @click="confirmDecision(d)"
            >
              确认
            </button>
            <button
              v-if="d.status === 'candidate'"
              class="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100"
              @click="rejectDecision(d)"
            >
              拒绝
            </button>
            <button
              class="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
              @click="removeDecision(d)"
            >
              删除
            </button>
          </div>
        </div>

        <p class="text-gray-800 mb-2">{{ d.content }}</p>

        <div v-if="d.context" class="text-sm text-gray-500 mb-2">
          背景：{{ d.context }}
        </div>

        <div class="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-gray-400">
          <span v-if="d.proposer_name">提出者：{{ d.proposer_name }}</span>
          <span>会议 #{{ d.meeting_id }}</span>
          <button class="text-blue-500 hover:underline" @click="goToMeeting(d.meeting_id)">查看会议</button>
          <span>{{ formatDate(d.created_at) }}</span>
          <span v-if="d.confirmed_at">确认于 {{ formatDate(d.confirmed_at) }}</span>
        </div>
      </div>

      <div v-if="total > pageSize" class="flex justify-center gap-2 mt-6">
        <button
          :disabled="page <= 1"
          class="px-3 py-1 border rounded disabled:opacity-50"
          @click="page--; loadDecisions()"
        >
          上一页
        </button>
        <span class="px-3 py-1 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
        <button
          :disabled="page * pageSize >= total"
          class="px-3 py-1 border rounded disabled:opacity-50"
          @click="page++; loadDecisions()"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>
