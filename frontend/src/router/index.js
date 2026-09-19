import { createRouter, createWebHistory } from "vue-router";

const BASE_URL = document.querySelector('base')?.getAttribute('href') || '/';

const router = createRouter({
  history: createWebHistory(BASE_URL),
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

function isTokenExpired(token) {
  if (!token) return true;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    if (!payload.exp) return false;
    return payload.exp * 1000 < Date.now();
  } catch (e) {
    return true;
  }
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  const expired = isTokenExpired(token);

  if (expired && token) {
    localStorage.removeItem("access_token");
  }

  if (to.path !== "/login" && (expired || !token)) {
    next("/login");
  } else if (to.path === "/login" && token && !expired) {
    next("/journal");
  } else {
    next();
  }
});

export default router;
