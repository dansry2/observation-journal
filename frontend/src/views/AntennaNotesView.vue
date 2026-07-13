<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Примечания к антеннам</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-text>
        <v-text-field v-model="search" label="Поиск антенны" prepend-inner-icon="mdi-magnify" variant="outlined" density="compact" hide-details class="mb-4" />

        <v-row dense>
          <v-col v-for="a in filteredAntennas" :key="a.code" cols="6" sm="4" md="3" lg="2">
            <v-card variant="outlined" :color="a.note ? 'success' : ''" class="pa-2 text-center" @click="openNote(a)">
              <div class="text-caption">{{ a.code }}</div>
              <v-icon v-if="a.note" color="success" size="small">mdi-check-circle</v-icon>
              <v-icon v-else color="grey" size="small">mdi-circle-outline</v-icon>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <div class="d-flex ga-2 mb-4">
      <v-btn color="primary" size="large" @click="save" :loading="saving">Сохранить</v-btn>
    </div>

    <!-- Диалог для примечания -->
    <v-dialog v-model="dialog" max-width="400">
      <v-card>
        <v-card-title>{{ selectedAntenna?.code }}</v-card-title>
        <v-card-text>
          <v-textarea v-model="selectedAntenna.note" label="Примечание" variant="outlined" rows="3" hide-details autofocus />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false">Готово</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const search = ref("");
const notes = ref([]);
const error = ref("");
const success = ref("");
const saving = ref(false);
const dialog = ref(false);
const selectedAntenna = ref(null);

const antennas = ref([]);

function transliterate(text) {
  const map = {'Е':'E','е':'e','С':'C','с':'c','А':'A','а':'a','Т':'T','т':'t','Р':'P','р':'p','О':'O','о':'o','Н':'H','н':'h','М':'M','м':'m','К':'K','к':'k','Х':'X','х':'x','В':'B','в':'b'};
  return text.split('').map(ch => map[ch] || ch).join('');
}

const filteredAntennas = computed(() => {
  if (!search.value) return notes.value;
  const q = transliterate(search.value).toUpperCase();
  return notes.value.filter(a => transliterate(a.code).toUpperCase().includes(q));
});

async function loadRefs() {
  const res = await axios.get("/api/v1/references", { headers: { "X-API-Key": import.meta.env.VITE_API_KEY || "YOUR_API_KEY_HERE" } });
  antennas.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  notes.value = antennas.value.map(code => ({ code, note: '' }));
  try {
    const res = await axios.get(`/antenna-notes/${selectedDate.value}`);
    const existing = res.data.notes || [];
    for (const n of existing) {
      const found = notes.value.find(a => a.code === n.antenna_code);
      if (found) found.note = n.note || '';
    }
  } catch (e) {}
}

function openNote(antenna) {
  selectedAntenna.value = antenna;
  dialog.value = true;
}

async function save() {
  saving.value = true;
  error.value = "";
  success.value = "";
  try {
    const data = notes.value.filter(a => a.note).map(a => ({ antenna_code: a.code, note: a.note }));
    await axios.post("/antenna-notes", { date: selectedDate.value, notes: data });
    success.value = "Сохранено!";
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { saving.value = false; }
}

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
