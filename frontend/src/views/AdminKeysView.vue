<template>
  <div>
    <h1 class="text-h4 mb-4">Управление</h1>

    <v-tabs v-model="tab">
      <v-tab value="users">Пользователи</v-tab>
      <v-tab value="backups">Бэкапы</v-tab>
    </v-tabs>

    <v-tabs-window v-model="tab" class="mt-4">
      <!-- Пользователи -->
      <v-tabs-window-item value="users">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            Создать пользователя
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" sm="4">
                <v-text-field v-model="newUser.username" label="Логин" density="compact" variant="outlined" hide-details />
              </v-col>
              <v-col cols="12" sm="4">
                <v-text-field v-model="newUser.password" label="Пароль" density="compact" variant="outlined" hide-details type="password" />
              </v-col>
              <v-col cols="12" sm="4">
                <v-text-field v-model="newUser.full_name" label="ФИО" density="compact" variant="outlined" hide-details />
              </v-col>
            </v-row>
            <v-btn color="primary" class="mt-3" @click="createUser" :loading="creating">Создать</v-btn>
          </v-card-text>
        </v-card>

        <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
        <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

        <v-card>
          <v-card-title>Существующие пользователи</v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr><th>Логин</th><th>ФИО</th><th>Роль</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id">
                  <td>{{ u.username }}</td>
                  <td>{{ u.full_name }}</td>
                  <td>{{ u.role === 'admin' ? 'Админ' : 'Оператор' }}</td>
                <td><v-btn v-if="u.role !== 'admin'" icon="mdi-delete" variant="text" color="error" size="small" @click="deleteUser(u.id)" /></td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-tabs-window-item>

      <!-- Бэкапы -->
      <v-tabs-window-item value="backups">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            Резервные копии (последние 30)
            <v-spacer />
            <v-chip>Хранятся в папке backups/</v-chip>
          </v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr><th>Дата</th><th>Размер</th><th>Файл</th></tr>
              </thead>
              <tbody>
                <tr v-for="b in backups" :key="b.name">
                  <td>{{ b.date }}</td>
                  <td>{{ b.size_mb }} МБ</td>
                  <td><code>{{ b.name }}</code></td>
                </tr>
              </tbody>
            </v-table>
            <div v-if="backups.length === 0" class="text-center py-4 text-grey">Бэкапов пока нет</div>
          </v-card-text>
        </v-card>
        <v-card class="pa-4" variant="outlined">
          <div class="text-subtitle-2 mb-2">Восстановление из бэкапа</div>
          <code>cd ~/observation_journal && bash restore.sh</code>
        </v-card>
      </v-tabs-window-item>
    </v-tabs-window>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const tab = ref("users");
const users = ref([]);
const newUser = ref({ username: "", password: "", full_name: "" });
const error = ref("");
const success = ref("");
const creating = ref(false);
const backups = ref([]);

async function deleteUser(id) {
  try {
    await axios.delete(`admin/users/${id}`);
    await loadUsers();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка удаления";
  }
}

async function loadUsers() {
  try {
    const res = await axios.get("users/");
    users.value = res.data || [];
  } catch (e) {}
}

async function loadBackups() {
  try {
    const res = await axios.get("admin/backups/");
    backups.value = res.data.backups || [];
  } catch (e) {}
}

async function createUser() {
  creating.value = true;
  error.value = "";
  success.value = "";
  try {
    await axios.post("admin/users", {
      username: newUser.value.username,
      password: newUser.value.password,
      full_name: newUser.value.full_name
    });
    success.value = "Пользователь создан!";
    newUser.value = { username: "", password: "", full_name: "" };
    await loadUsers();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { creating.value = false; }
}

onMounted(() => {
  loadUsers();
  loadBackups();
});
</script>
