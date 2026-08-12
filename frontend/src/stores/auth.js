import { defineStore } from "pinia";
import axios from "axios";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("access_token") || null,
    user: null,
  }),
  actions: {
    async login(username, password) {
      const res = await axios.post("auth/login", { username, password });
      this.token = res.data.access_token;
      localStorage.setItem("access_token", this.token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`;
    },
    async register(username, password, full_name, ) {
      const res = await axios.post("auth/register", {
        username,
        password,
        full_name,
        
      });
      this.token = res.data.access_token;
      localStorage.setItem("access_token", this.token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`;
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("access_token");
      delete axios.defaults.headers.common["Authorization"];
    },
    initAuth() {
      if (this.token) {
        axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`;
      }
    },
  },
});
