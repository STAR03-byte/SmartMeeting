<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { listCommitments, updateCommitment, deleteCommitment } from "../api/commitments";
import type { Commitment } from "../api/commitments";

const router = useRouter();
const loading = ref(false);
const commitments = ref<Commitment[]>([]);
const total = ref(0);
const statusFilter = ref<string>("");
const page = ref(1);
const pageSize = 20;

const statusOptions = [
  { label: "全部", value: "" },
  { label: "待确认", value: "candidate" },
  { label: "已确认", value: "confirmed" },
  { label: "进行中", value: "in_progress" },
  { label: "已完成", value: "done" },
  { label: "已放弃", value: "abandoned" },
];

const statusLabel: Record<string, string> = {
  candidate: "待确认",
  confirmed: "已确认",
  in_progress: "进行中",
  done: "已完成",
  abandoned: "已放弃",
};

const nextStatus: Record<string, string> = {
  candidate: "confirmed",
  confirmed: "in_progress",
  in_progress: "done",
};

const nextStatusLabel: Record<string, string> = {
  candidate: "确认",
  confirmed: "开始",
  in_progress: "完成",
};

async function loadCommitments() {
  loading.value = true;
  try {
    const res = await listCommitments({
      status: statusFilter.value || undefined,
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
    });
    commitments.value = res.items;
    total.value = res.total;
  } finally {
    loading.value = false;
  }
}

async function advanceStatus(c: Commitment) {
  const next = nextStatus[c.status];
  if (next) {
    await updateCommitment(c.id, { status: next });
    await loadCommitments();
  }
}

async function abandonCommitment(c: Commitment) {
  await updateCommitment(c.id, { status: "abandoned" });
  await loadCommitments();
}

async function removeCommitment(c: Commitment) {
  await deleteCommitment(c.id);
  await loadCommitments();
}

function goToMeeting(meetingId: number) {
  router.push({ name: "meeting-detail", params: { id: meetingId } });
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-CN");
}

function exportMarkdown() {
  const lines: string[] = ["# 承诺导出\n", `> 导出时间：${new Date().toLocaleString("zh-CN")}\n`];
  const grouped = new Map<number, Commitment[]>();
  for (const c of commitments.value) {
    const arr = grouped.get(c.meeting_id) || [];
    arr.push(c);
    grouped.set(c.meeting_id, arr);
  }
  for (const [meetingId, items] of grouped) {
    lines.push(`## 会议 #${meetingId}\n`);
    for (const c of items) {
      const parts = [`- **[${statusLabel[c.status] || c.status}]** ${c.content}`];
      if (c.assignee_name) parts[0] += ` — ${c.assignee_name}`;
      if (c.due_hint) parts.push(`  - 截止：${c.due_hint}`);
      if (c.linked_task_id) parts.push(`  - 关联任务 #${c.linked_task_id}`);
      parts.push(`  - 时间：${formatDate(c.created_at)}`);
      lines.push(...parts);
    }
    lines.push("");
  }
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `commitments-${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

onMounted(loadCommitments);
</script>

<template>
  <div class="max-w-5xl mx-auto p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-xl sm:text-2xl font-bold">承诺追踪</h1>
      <div class="flex items-center gap-2">
        <button
          v-if="commitments.length > 0"
          class="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50"
          @click="exportMarkdown"
        >
          导出 Markdown
        </button>
        <select v-model="statusFilter" class="px-3 py-2 border rounded-lg text-sm" @change="loadCommitments">
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>

    <div v-else-if="commitments.length === 0" class="text-center py-12 text-gray-500">
      暂无承诺记录
    </div>

    <div v-else class="space-y-4">
      <div class="text-sm text-gray-500 mb-2">共 {{ total }} 条承诺</div>

      <div
        v-for="c in commitments"
        :key="c.id"
        class="border rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span
              class="px-2 py-0.5 text-xs rounded-full"
              :class="{
                'bg-yellow-100 text-yellow-700': c.status === 'candidate',
                'bg-blue-100 text-blue-700': c.status === 'confirmed',
                'bg-indigo-100 text-indigo-700': c.status === 'in_progress',
                'bg-green-100 text-green-700': c.status === 'done',
                'bg-gray-100 text-gray-600': c.status === 'abandoned',
              }"
            >
              {{ statusLabel[c.status] || c.status }}
            </span>
            <span v-if="c.assignee_name" class="text-xs text-gray-500">
              负责人：{{ c.assignee_name }}
            </span>
            <span v-if="c.due_hint" class="text-xs text-orange-600">
              截止：{{ c.due_hint }}
            </span>
          </div>
          <div class="flex gap-1 shrink-0">
            <button
              v-if="nextStatus[c.status]"
              class="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
              @click="advanceStatus(c)"
            >
              {{ nextStatusLabel[c.status] }}
            </button>
            <button
              v-if="c.status !== 'done' && c.status !== 'abandoned'"
              class="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
              @click="abandonCommitment(c)"
            >
              放弃
            </button>
            <button
              class="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
              @click="removeCommitment(c)"
            >
              删除
            </button>
          </div>
        </div>

        <p class="text-gray-800 mb-2">{{ c.content }}</p>

        <div class="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-gray-400">
          <span>会议 #{{ c.meeting_id }}</span>
          <button class="text-blue-500 hover:underline" @click="goToMeeting(c.meeting_id)">查看会议</button>
          <span v-if="c.linked_task_id">关联任务 #{{ c.linked_task_id }}</span>
          <span>{{ formatDate(c.created_at) }}</span>
          <span v-if="c.confirmed_at">确认于 {{ formatDate(c.confirmed_at) }}</span>
        </div>
      </div>

      <div v-if="total > pageSize" class="flex justify-center gap-2 mt-6">
        <button
          :disabled="page <= 1"
          class="px-3 py-1 border rounded disabled:opacity-50"
          @click="page--; loadCommitments()"
        >
          上一页
        </button>
        <span class="px-3 py-1 text-sm text-gray-500">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
        <button
          :disabled="page * pageSize >= total"
          class="px-3 py-1 border rounded disabled:opacity-50"
          @click="page++; loadCommitments()"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>
