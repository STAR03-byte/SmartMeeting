import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import MeetingDetailView from "../views/MeetingDetailView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/meetings/:id",
      name: "meeting-detail",
      component: MeetingDetailView,
      props: true,
    },
  ],
});

export default router;
