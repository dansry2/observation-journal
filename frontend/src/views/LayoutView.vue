<template>
  <v-navigation-drawer permanent rail expand-on-hover>
    <v-list density="compact" nav>
      <v-list-item prepend-icon="mdi-notebook-edit" title="Журнал" value="journal" to="/journal" />
      <v-list-item prepend-icon="mdi-alert-circle" title="Ошибки" value="errors" to="/errors" />
      <v-list-item prepend-icon="mdi-swap-horizontal" title="Перемещения" value="movements" to="/movements" />
      <v-list-item prepend-icon="mdi-contacts" title="Контакты" value="contacts" to="/contacts" />
      <v-divider class="my-2" />
      <v-list-item v-if="auth.token && isAdmin" prepend-icon="mdi-backup-restore" title="Бэкапы" value="admin" to="/admin/keys" />
      <v-divider class="my-2" />
      <v-list-item v-if="!auth.token" prepend-icon="mdi-login" title="Войти" to="/login" />
      <v-list-item v-if="auth.token" prepend-icon="mdi-logout" title="Выход" @click="logout" />
    </v-list>
  </v-navigation-drawer>
  <v-main>
    <v-container fluid>
      <router-view />
    </v-container>
  </v-main>
</template>

<script setup>
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();
const isAdmin = auth.token ? JSON.parse(atob(auth.token.split(".")[1])).role === "admin" : false;

function logout() {
  auth.logout();
  window.location.reload();
}
</script>
