<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Журнал ошибок антенн</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" class="mr-2" @change="loadData" />
      <v-select v-model="selectedGrid" :items="grids" item-title="name" item-value="id" label="Диапазон" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">Антенны <v-spacer /><v-checkbox v-model="isBroken" label="Диапазон сломан" density="compact" hide-details color="error" class="ml-4" /></v-card-title>
      <v-card-text>
        <div v-for="(entry, idx) in entries" :key="idx" class="d-flex align-center ga-2 mb-2">
          <v-combobox v-model="entry.antenna_code" :items="antennaList" :custom-filter="filterAntennas" label="Антенна" density="compact" variant="outlined" style="max-width: 150px" hide-details />
          <v-text-field v-model="entry.error_description" label="Описание ошибки" density="compact" variant="outlined" hide-details />
          <v-checkbox v-model="entry.is_broken" label="Сломана" density="compact" hide-details class="ml-2" />
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="entries.splice(idx, 1)" />
        </div>
        <v-btn variant="outlined" @click="entries.push({ antenna_code: '', error_description: '', is_broken: false })">
          <v-icon class="mr-2">mdi-plus</v-icon> Добавить антенну
        </v-btn>
      </v-card-text>
    </v-card>

    <v-text-field v-model="changeNote" label="Примечание к диапазону" variant="outlined" hide-details class="mb-4" hint="Общее примечание ко всем антеннам данного диапазона на эту дату" persistent-hint />

    <div v-if="info.created_by" class="mb-2 text-body-2">Создал: {{ info.created_by }} | Версия: {{ info.version }}</div>

    <div class="d-flex ga-2 mb-4">
      <v-btn color="primary" @click="save" :loading="saving"><v-icon class="mr-2">mdi-content-save</v-icon> Сохранить</v-btn>
      <v-btn variant="outlined" @click="showHistory = true" v-if="info.version">История</v-btn>
    </div>

    <v-dialog v-model="showHistory" max-width="800">
      <v-card>
        <v-card-title>История</v-card-title>
        <v-card-text>
          <v-timeline v-if="history.length" density="compact">
            <v-timeline-item v-for="h in history" :key="h.id" :dot-color="h.is_active ? 'success' : 'grey'" size="small">
              <div class="text-caption">{{ h.created_at }}</div>
              <div><strong>v{{ h.version }}</strong> — {{ h.created_by }}</div>
              <div v-if="h.change_note">{{ h.change_note }}</div>
            </v-timeline-item>
          </v-timeline>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="showHistory = false">Закрыть</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const selectedGrid = ref(5);
const entries = ref([{ antenna_code: "", error_description: "", is_broken: false }]);
const changeNote = ref("");
const isBroken = ref(false);
const error = ref("");
const success = ref("");
const saving = ref(false);
const showHistory = ref(false);
const info = ref({});
const history = ref([]);
const grids = ref([]);
const antennaList = ref([]);

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
  grids.value = res.data.equipment_ranges || [];
  antennaList.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  entries.value = [{ antenna_code: "", error_description: "", is_broken: false }];
  info.value = {};
  isBroken.value = false;
  error.value = "";
  success.value = "";
  try {
    const res = await axios.get(`/errors-grid/${selectedDate.value}/${selectedGrid.value}`);
    entries.value = res.data.entries.length > 0 ? res.data.entries.map(e => ({ ...e })) : [{ antenna_code: "", error_description: "", is_broken: false }];
    info.value = { created_by: res.data.created_by, version: res.data.version };
    isBroken.value = res.data.is_broken || false;
  } catch (e) {}
}

async function save() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    error.value = "Войдите в систему, чтобы вносить изменения";
    return;
  }

  const filtered = entries.value.filter(e => e.antenna_code);

  if (info.value.version) {
    const check = await axios.post("/errors-grid/check-conflicts", {
      date: selectedDate.value, grid_id: selectedGrid.value, entries: filtered
    });
    if (check.data.conflict) {
      confirmDialog.value = true;
      return;
    }
  }
  await doSave();
}

async function doSave() {
  saving.value = true;
  try {
    const filtered = entries.value.filter(e => e.antenna_code);
    await axios.post("/errors-grid/", {
      date: selectedDate.value, grid_id: selectedGrid.value,
      entries: filtered.map(e => ({ antenna_code: e.antenna_code, error_description: e.error_description, is_broken: e.is_broken })),
      change_note: changeNote.value || "Обновление", is_broken: isBroken.value
    });
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { saving.value = false; }
}

async function loadHistory() {
  try {
    const res = await axios.get(`/errors-grid/${selectedDate.value}/${selectedGrid.value}/history`);
    history.value = res.data.versions || [];
  } catch (e) { history.value = []; }
}

watch(showHistory, (val) => { if (val) loadHistory(); });
watch(selectedGrid, () => { loadData(); });

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
