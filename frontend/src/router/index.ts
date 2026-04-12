import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/authStore";

const DashboardView = () => import("../views/DashboardView.vue");
const MeetingDetailView = () => import("../views/MeetingDetailView.vue");
const MeetingListView = () => import("../views/MeetingListView.vue");
const SharedMeetingView = () => import("../views/SharedMeetingView.vue");
const AIAssistantView = () => import("../views/AIAssistantView.vue");
const HotwordsView = () => import("../views/HotwordsView.vue");
const TasksView = () => import("../views/TasksView.vue");
const LoginView = () => import("../views/LoginView.vue");
const TeamCreateView = () => import("../views/TeamCreateView.vue");
const TeamsView = () => import("../views/TeamsView.vue");
const TeamDetailView = () => import("../views/TeamDetailView.vue");
const InvitationsView = () => import("../views/InvitationsView.vue");
const InviteAcceptView = () => import("../views/InviteAcceptView.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: DashboardView,
    },
    {
      path: "/teams",
      name: "teams",
      component: TeamsView,
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
      path: "/ai-assistant",
      name: "ai-assistant",
      component: AIAssistantView,
      meta: { requiresAuth: true },
    },
    {
      path: "/hotwords",
      name: "hotwords",
      component: HotwordsView,
    },
    {
      path: "/teams/create",
      name: "team-create",
      component: TeamCreateView,
    },
    {
      path: "/teams/:id",
      name: "team-detail",
      component: TeamDetailView,
      props: true,
    },
    {
      path: "/invitations",
      name: "invitations",
      component: InvitationsView,
    },
    {
      path: "/invite/:token",
      name: "invite-accept",
      component: InviteAcceptView,
      props: true,
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
