<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Заметки</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-text>
        <div v-for="(note, idx) in notes" :key="note.id || idx" class="mb-3 pa-3 border rounded">
          <div class="d-flex align-center mb-2">
            <v-text-field v-model="note.title" label="Заголовок" density="compact" variant="outlined" hide-details class="mr-2" />
            <v-btn v-if="note.id" icon="mdi-delete" variant="text" color="error" size="small" @click="deleteNote(note.id)" />
          </div>
          <v-textarea v-model="note.description" label="Описание" density="compact" variant="outlined" rows="2" hide-details />
          <div v-if="note.created_by" class="text-caption mt-1">Добавил: {{ note.created_by }} | {{ note.created_at?.substr(0, 16) }}</div>
        </div>
      </v-card-text>
    </v-card>

    <div class="d-flex ga-2 mb-4">
      <v-btn variant="outlined" @click="notes.push({ title: '', description: '' })">
        <v-icon class="mr-2">mdi-plus</v-icon> Добавить заметку
      </v-btn>
      <v-btn color="primary" @click="saveAll" :loading="saving">Сохранить все</v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const notes = ref([]);
const error = ref("");
const success = ref("");
const saving = ref(false);

async function loadData() {
  try {
    const res = await axios.get(`/notes/${selectedDate.value}`);
    notes.value = res.data.length > 0 ? res.data : [];
  } catch (e) {
    notes.value = [];
  }
}

async function saveAll() {
  saving.value = true;
  error.value = "";
  success.value = "";
  try {
    for (const note of notes.value) {
      if (!note.id && (note.title || note.description)) {
        await axios.post("/notes", { date: selectedDate.value, title: note.title, description: note.description });
      }
    }
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { saving.value = false; }
}

async function deleteNote(id) {
  try {
    await axios.delete(`/notes/${id}`);
    await loadData();
  } catch (e) {
    error.value = "Ошибка удаления";
  }
}

onMounted(() => loadData());
</script>
