<template>
  <v-navigation-drawer permanent rail expand-on-hover>
    <v-list density="compact" nav>
      <v-list-item
        prepend-icon="mdi-notebook-edit"
        title="Журнал"
        value="journal"
        to="/journal"
      />
      <v-list-item
        prepend-icon="mdi-waves"
        title="UV plane"
        value="uv-plane"
        to="/uv-plane"
      />
      <v-list-item
        prepend-icon="mdi-alert-circle"
        title="Ошибки"
        value="errors"
        to="/errors"
      />
      <v-list-item
        prepend-icon="mdi-swap-horizontal"
        title="Перемещения"
        value="movements"
        to="/movements"
      />
      <v-list-item
        prepend-icon="mdi-antenna"
        title="Антенны"
        value="antenna-notes"
        to="/antenna-notes"
      />
      <v-list-item
        prepend-icon="mdi-note-text"
        title="Заметки"
        value="notes"
        to="/notes"
      />
      <v-list-item
        prepend-icon="mdi-contacts"
        title="Контакты"
        value="contacts"
        to="/contacts"
      />
      <v-divider class="my-2" />
      <v-list-item
        prepend-icon="mdi-key-variant"
        title="Ключи"
        value="admin-keys"
        to="/admin/keys"
      />
      <v-divider class="my-2" />
      <v-list-item
        prepend-icon="mdi-logout"
        title="Выход"
        @click="logout"
      />
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

function logout() {
  auth.logout();
  router.push("/login");
}
</script>
