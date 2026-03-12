<template>
  <section class="dashboard-page">
    <header class="hero-header">
      <h1>SmartMeeting Control Deck</h1>
      <p>会议、转写、任务闭环的一站式驾驶舱</p>
    </header>

    <el-skeleton v-if="store.loading" rows="4" animated />

    <div v-else class="meeting-grid">
      <MeetingCard v-for="item in store.meetings" :key="item.id" :meeting="item" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import MeetingCard from "../components/MeetingCard.vue";
import { useMeetingStore } from "../stores/meetingStore";

const store = useMeetingStore();

onMounted(async () => {
  await store.fetchMeetings();
});
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-header {
  background: linear-gradient(120deg, #f3f9ff 0%, #fff6ea 100%);
  border: 1px solid #dce8f4;
  border-radius: 18px;
  padding: 24px;
}

.hero-header h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0.3px;
  color: #1d2f45;
}

.hero-header p {
  margin: 10px 0 0;
  color: #4b6077;
}

.meeting-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}
</style>
