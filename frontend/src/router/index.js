import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
    {
      path: "/",
      name: "layout",
      component: () => import("../views/LayoutView.vue"),
      children: [
        { path: "", redirect: "/journal" },
        { path: "journal", name: "journal", component: () => import("../views/JournalView.vue") },
        { path: "errors", name: "errors", component: () => import("../views/ErrorsView.vue") },
        { path: "contacts", name: "contacts", component: () => import("../views/ContactsView.vue") },
        { path: "admin/keys", name: "admin", component: () => import("../views/AdminKeysView.vue") },
      ],
    },
  ],
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  // Все страницы кроме логина требуют авторизацию
  if (to.path !== "/login" && !token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
