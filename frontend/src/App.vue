<template>
  <v-app>
    <router-view />
    <v-snackbar
      v-model="notifications.visible"
      :color="notifications.type"
      :timeout="5000"
      location="top"
    >
      {{ notifications.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="notifications.hide()">Закрыть</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";

const auth = useAuthStore();
const notifications = useNotificationsStore();

onMounted(() => {
  auth.initAuth();
});
</script>
