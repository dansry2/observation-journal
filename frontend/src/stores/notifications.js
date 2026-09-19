import { defineStore } from "pinia";

export const useNotificationsStore = defineStore("notifications", {
  state: () => ({
    message: "",
    type: "error",
    visible: false,
  }),
  actions: {
    show(message, type = "error") {
      this.message = message;
      this.type = type;
      this.visible = true;
    },
    hide() {
      this.visible = false;
    },
  },
});
