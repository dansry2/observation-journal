<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Журнал ошибок антенн</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" class="mr-2" @change="loadData" />
      <v-select v-model="selectedGrid" :items="grids" item-title="name" item-value="id" label="Решётка" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-title>Ошибки</v-card-title>
      <v-card-text>
        <div v-for="(entry, idx) in entries" :key="idx" class="d-flex align-center ga-2 mb-2">
          <v-combobox v-model="entry.antenna_code" :items="antennaList" label="Антенна" density="compact" variant="outlined" style="max-width: 150px" hide-details />
          <v-text-field v-model="entry.error_description" label="Описание ошибки" density="compact" variant="outlined" hide-details />
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="entries.splice(idx, 1)" />
        </div>
        <v-btn variant="outlined" @click="entries.push({ antenna_code: '', error_description: '' })">
          <v-icon class="mr-2">mdi-plus</v-icon> Добавить
        </v-btn>
      </v-card-text>
    </v-card>

    <v-text-field v-model="changeNote" label="Примечание к изменению" variant="outlined" hide-details class="mb-4" />

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
const entries = ref([{ antenna_code: "", error_description: "" }]);
const changeNote = ref("");
const error = ref("");
const success = ref("");
const saving = ref(false);
const showHistory = ref(false);
const info = ref({});
const history = ref([]);
const grids = ref([]);
const antennaList = ref([]);

async function loadRefs() {
  const res = await axios.get("/api/v1/references", { headers: { "X-API-Key": "ak_5e013c70196a73ec479597dc68fa8b2b" } });
  grids.value = res.data.equipment_ranges || [];
  antennaList.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  try {
    const res = await axios.get(`/errors/${selectedDate.value}/${selectedGrid.value}`);
    entries.value = res.data.entries.length > 0 ? res.data.entries.map(e => ({ ...e })) : [{ antenna_code: "", error_description: "" }];
    info.value = { created_by: res.data.created_by, version: res.data.version };
  } catch (e) {
    entries.value = [{ antenna_code: "", error_description: "" }];
    info.value = {};
  }
}

async function save() {
  saving.value = true;
  try {
    await axios.post("/errors/", {
      date: selectedDate.value, grid_id: selectedGrid.value,
      entries: entries.value.filter(e => e.antenna_code),
      change_note: changeNote.value || "Обновление"
    });
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка";
  } finally { saving.value = false; }
}

async function loadHistory() {
  try {
    const res = await axios.get(`/errors/${selectedDate.value}/${selectedGrid.value}/history`);
    history.value = res.data.versions || [];
  } catch (e) { history.value = []; }
}

watch(showHistory, (val) => { if (val) loadHistory(); });

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
