<template>
  <div>
    <h1 class="text-h4 mb-4">Управление</h1>

    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        Резервные копии (последние 30)
        <v-spacer />
        <v-chip>Хранятся в папке backups/</v-chip>
      </v-card-title>
      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Размер</th>
              <th>Файл</th>
            </tr>
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
      <div class="text-body-2 mb-2">Для восстановления выполните в терминале:</div>
      <code>cd ~/observation_journal && bash restore.sh</code>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const backups = ref([]);

async function loadBackups() {
  try {
    const res = await axios.get("/admin/backups/");
    backups.value = res.data.backups || [];
  } catch (e) {}
}

onMounted(() => loadBackups());
</script>
