import { createRouter, createWebHistory } from "vue-router";

const DashboardView = () => import("../views/DashboardView.vue");
const MeetingDetailView = () => import("../views/MeetingDetailView.vue");
const TasksView = () => import("../views/TasksView.vue");
const UsersView = () => import("../views/UsersView.vue");

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
    {
      path: "/tasks",
      name: "tasks",
      component: TasksView,
    },
    {
      path: "/users",
      name: "users",
      component: UsersView,
    },
  ],
});

export default router;
