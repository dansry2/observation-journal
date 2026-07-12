<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Управление ключами</h1>
      <v-spacer />
      <v-btn color="primary" @click="createKey" :loading="creating">
        <v-icon class="mr-2">mdi-plus</v-icon> Создать ключ
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card v-if="newKey" class="mb-4 pa-4" color="success" variant="outlined">
      <div class="text-h6">Новый ключ создан!</div>
      <div class="text-h4 my-2">{{ newKey }}</div>
      <div class="text-caption">Скопируйте и передайте наблюдателю. После закрытия страницы ключ не отобразится снова.</div>
    </v-card>

    <v-card>
      <v-card-title>Ключи приглашения</v-card-title>
      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>Ключ</th>
              <th>Создал</th>
              <th>Создан</th>
              <th>Использовал</th>
              <th>Использован</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in keys" :key="key.id">
              <td><code>{{ key.key_code }}</code></td>
              <td>{{ key.created_by }}</td>
              <td>{{ key.created_at?.substr(0, 10) }}</td>
              <td>{{ key.used_by || '-' }}</td>
              <td>{{ key.used_at?.substr(0, 10) || '-' }}</td>
              <td>
                <v-chip v-if="key.is_active && !key.used_by" color="success" size="small">Активен</v-chip>
                <v-chip v-else-if="key.used_by" color="info" size="small">Использован</v-chip>
                <v-chip v-else color="error" size="small">Отключён</v-chip>
              </td>
              <td>
                <v-btn v-if="key.is_active && !key.used_by" icon="mdi-cancel" variant="text" color="error" size="small" @click="deactivate(key.id)" />
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const keys = ref([]);
const newKey = ref("");
const error = ref("");
const success = ref("");
const creating = ref(false);

async function loadKeys() {
  try {
    const res = await axios.get("/admin/keys");
    keys.value = res.data;
  } catch (e) {
    error.value = "Ошибка загрузки ключей";
  }
}

async function createKey() {
  creating.value = true;
  error.value = "";
  try {
    const res = await axios.post("/admin/keys");
    newKey.value = res.data.key_code;
    success.value = "Ключ создан!";
    await loadKeys();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally {
    creating.value = false;
  }
}

async function deactivate(id) {
  try {
    await axios.put(`/admin/keys/${id}/deactivate`);
    await loadKeys();
  } catch (e) {
    error.value = "Ошибка деактивации";
  }
}

onMounted(() => loadKeys());
</script>
