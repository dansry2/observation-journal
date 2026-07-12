import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("../views/LoginView.vue"),
    },
    {
      path: "/register",
      name: "register",
      component: () => import("../views/RegisterView.vue"),
    },
    {
      path: "/",
      name: "layout",
      component: () => import("../views/LayoutView.vue"),
      children: [
        {
          path: "",
          redirect: "/journal",
        },
        {
          path: "journal",
          name: "journal",
          component: () => import("../views/JournalView.vue"),
        },
        {
          path: "uv-plane",
          name: "uv-plane",
          component: () => import("../views/UVPlaneView.vue"),
        },
        {
          path: "errors",
          name: "errors",
          component: () => import("../views/ErrorsView.vue"),
        },
        {
          path: "movements",
          name: "movements",
          component: () => import("../views/MovementsView.vue"),
        },
        {
          path: "antenna-notes",
          name: "antenna-notes",
          component: () => import("../views/AntennaNotesView.vue"),
        },
        {
          path: "notes",
          name: "notes",
          component: () => import("../views/NotesView.vue"),
        },
        {
          path: "contacts",
          name: "contacts",
          component: () => import("../views/ContactsView.vue"),
        },
        {
          path: "admin/keys",
          name: "admin-keys",
          component: () => import("../views/AdminKeysView.vue"),
        },
      ],
    },
  ],
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  if (to.path !== "/login" && to.path !== "/register" && !token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
