import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/authStore";

const DashboardView = () => import("../views/DashboardView.vue");
const MeetingDetailView = () => import("../views/MeetingDetailView.vue");
const MeetingListView = () => import("../views/MeetingListView.vue");
const SharedMeetingView = () => import("../views/SharedMeetingView.vue");
const HotwordsView = () => import("../views/HotwordsView.vue");
const TasksView = () => import("../views/TasksView.vue");
const UsersView = () => import("../views/UsersView.vue");
const LoginView = () => import("../views/LoginView.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/meetings",
      name: "meetings",
      component: MeetingListView,
    },
    {
      path: "/meetings/:id",
      name: "meeting-detail",
      component: MeetingDetailView,
      props: true,
    },
    {
      path: "/shared/meetings/:token",
      name: "shared-meeting",
      component: SharedMeetingView,
      props: true,
    },
    {
      path: "/tasks",
      name: "tasks",
      component: TasksView,
    },
    {
      path: "/hotwords",
      name: "hotwords",
      component: HotwordsView,
    },
    {
      path: "/users",
      name: "users",
      component: UsersView,
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
    },
  ],
});

router.beforeEach((to) => {
  const authStore = useAuthStore();
  if (to.name !== "login" && !authStore.token) {
    return {
      name: "login",
      query: { redirect: `${to.fullPath}` },
    };
  }
  if (to.name === "login" && authStore.token) {
    return { name: "dashboard" };
  }
  return true;
});

export default router;
