<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Перемещение компонентов</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-title>Перемещения</v-card-title>
      <v-card-text>
        <div v-for="(m, idx) in movements" :key="idx" class="mb-3 pa-3 border rounded">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="m.component_name" label="Компонент" density="compact" variant="outlined" hide-details />
            </v-col>
            <v-col cols="6" sm="3">
              <v-combobox v-model="m.from_antenna" :items="antennaList" :custom-filter="filterAntennas" label="С антенны" density="compact" variant="outlined" hide-details clearable />
            </v-col>
            <v-col cols="6" sm="3">
              <v-combobox v-model="m.to_antenna" :items="antennaList" :custom-filter="filterAntennas" label="На антенну" density="compact" variant="outlined" hide-details clearable />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="m.note" label="Примечание" density="compact" variant="outlined" hide-details />
            </v-col>
          </v-row>
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="movements.splice(idx, 1)" class="mt-1" />
        </div>
        <v-btn variant="outlined" @click="movements.push({ component_name: '', from_antenna: '', to_antenna: '', note: '' })">
          <v-icon class="mr-2">mdi-plus</v-icon> Добавить перемещение
        </v-btn>
      </v-card-text>
    </v-card>

    <v-text-field v-model="changeNote" label="Примечание к изменению" variant="outlined" hide-details class="mb-4" />

    <div class="d-flex ga-2 mb-4">
      <v-btn color="primary" size="large" @click="save" :loading="saving">Сохранить</v-btn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const movements = ref([{ component_name: '', from_antenna: '', to_antenna: '', note: '' }]);
const antennaList = ref([]);
const error = ref("");
const success = ref("");
const saving = ref(false);
const changeNote = ref('');

function transliterate(text) {
  const map = {'Е':'E','е':'e','С':'C','с':'c','А':'A','а':'a','Т':'T','т':'t','Р':'P','р':'p','О':'O','о':'o','Н':'H','н':'h','М':'M','м':'m','К':'K','к':'k','Х':'X','х':'x','В':'B','в':'b'};
  return text.split('').map(ch => map[ch] || ch).join('');
}

function filterAntennas(item, queryText) {
  if (!queryText) return true;
  const q = transliterate(queryText).toUpperCase();
  const code = transliterate(typeof item === 'object' ? (item.title || item || '') : (item || '')).toUpperCase();
  return code.includes(q);
}

async function loadRefs() {
  const res = await axios.get("/api/v1/references", { headers: { "X-API-Key": import.meta.env.VITE_API_KEY || "YOUR_API_KEY_HERE" } });
  antennaList.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  try {
    const res = await axios.get(`/movements/${selectedDate.value}`);
    movements.value = res.data.movements.length > 0 ? res.data.movements.map(m => ({ ...m })) : [{ component_name: '', from_antenna: '', to_antenna: '', note: '' }];
  } catch (e) {
    movements.value = [{ component_name: '', from_antenna: '', to_antenna: '', note: '' }];
  }
}

async function save() {
  saving.value = true;
  error.value = "";
  success.value = "";
  try {
    await axios.put(`/movements/${selectedDate.value}`, {
      date: selectedDate.value,
      movements: movements.value.filter(m => m.component_name || m.from_antenna || m.to_antenna)
    });
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { saving.value = false; }
}

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
