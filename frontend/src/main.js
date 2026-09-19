import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "vuetify/styles";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import "@mdi/font/css/materialdesignicons.css";
import axios from "axios";

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "dark",
    themes: {
      dark: {
        dark: true,
        colors: {
          primary: "#1976D2",
          secondary: "#424242",
          accent: "#82B1FF",
          error: "#FF5252",
          info: "#2196F3",
          success: "#4CAF50",
          warning: "#FFC107",
        },
      },
    },
  },
});

const BASE_URL = document.querySelector("base")?.getAttribute("href") || "/";
axios.defaults.baseURL = BASE_URL;

import { useNotificationsStore } from "@/stores/notifications";

function extractErrorMessage(error) {
  if (!error.response) {
    return "Нет соединения с сервером";
  }
  const data = error.response.data;
  if (!data) {
    return `Ошибка ${error.response.status}`;
  }
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map(e => e.msg || JSON.stringify(e)).join("; ");
  }
  if (typeof data === "string") {
    return data;
  }
  return JSON.stringify(data);
}

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("access_token");
      const base = document.querySelector("base")?.getAttribute("href") || "/";
      const loginPath = (base.endsWith("/") ? base : base + "/") + "login";
      if (!window.location.pathname.startsWith(loginPath)) {
        window.location.href = loginPath;
      }
      return Promise.reject(error);
    }

    const url = error.config?.url || "";
    const isNotFound = error.response && error.response.status === 404;
    const isExpected404 = url.includes("errors-grid") || url.includes("observations");

    if (!(isNotFound && isExpected404)) {
      try {
        const notifications = useNotificationsStore();
        notifications.show(extractErrorMessage(error), "error");
      } catch (e) {
        console.error("Не удалось показать ошибку:", e);
      }
    }

    return Promise.reject(error);
  }
);

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(vuetify);
app.mount("#app");
