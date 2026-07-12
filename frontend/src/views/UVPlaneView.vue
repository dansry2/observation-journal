<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">UV plane</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" class="mr-2" @change="loadData" />
      <v-select v-model="selectedTime" :items="slots" item-title="title" item-value="value" label="Время" variant="outlined" density="compact" style="max-width: 120px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card class="mb-4">
      <v-card-title>Антенны</v-card-title>
      <v-card-text>
        <div v-for="(entry, idx) in entries" :key="idx" class="d-flex align-center ga-2 mb-2">
          <v-combobox
            v-model="entry.antenna_code"
            :items="antennaList"
            :custom-filter="filterAntennas"
            label="Антенна"
            density="compact"
            variant="outlined"
            style="max-width: 150px"
            hide-details
          />
          <v-combobox v-model="entry.status" :items="statusList" label="Статус" density="compact" variant="outlined" style="max-width: 200px" hide-details />
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="entries.splice(idx, 1)" />
        </div>
        <v-btn variant="outlined" @click="entries.push({ antenna_code: '', status: '' })" class="mb-2">
          <v-icon class="mr-2">mdi-plus</v-icon> Добавить антенну
        </v-btn>
      </v-card-text>
    </v-card>

    <v-text-field v-model="changeNote" label="Примечание к изменению" variant="outlined" hide-details class="mb-4" />

    <div v-if="info.created_by" class="mb-2 text-body-2">Создал: {{ info.created_by }} | Версия: {{ info.version }}</div>

    <div class="d-flex ga-2 mb-4">
      <v-btn color="primary" @click="save" :loading="saving"><v-icon class="mr-2">mdi-content-save</v-icon> Сохранить</v-btn>
      <v-btn variant="outlined" @click="showHistory = true" v-if="info.version"><v-icon class="mr-2">mdi-history</v-icon> История</v-btn>
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
const selectedTime = ref(1);
const entries = ref([{ antenna_code: "", status: "" }]);
const changeNote = ref("");
const error = ref("");
const success = ref("");
const saving = ref(false);
const showHistory = ref(false);
const info = ref({});
const history = ref([]);
const slots = ref([]);
const statusList = ref([]);
const antennaList = ref([]);

function transliterate(text) {
  const map = {'Е':'E','е':'e','С':'C','с':'c','А':'A','а':'a','Т':'T','т':'t','Р':'P','р':'p','О':'O','о':'o','Н':'H','н':'h','М':'M','м':'m','К':'K','к':'k','Х':'X','х':'x','В':'B','в':'b'};
  return text.split('').map(ch => map[ch] || ch).join('');
}

function filterAntennas(item, queryText) {
  if (!queryText) return true;
  const q = transliterate(queryText).toUpperCase();
  const code = transliterate(typeof item === 'object' ? (item.title || item.antenna_code || '') : (item || '')).toUpperCase();
  return code.includes(q);
}

async function loadRefs() {
  const res = await axios.get("/api/v1/references", { headers: { "X-API-Key": "ak_5e013c70196a73ec479597dc68fa8b2b" } });
  slots.value = (res.data.uv_slots || []).map(s => ({ title: s.time || s.slot_time, value: s.id }));
  statusList.value = (res.data.uv_statuses || []).map(s => s.text);
  antennaList.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  try {
    const res = await axios.get(`/uv-plane/${selectedDate.value}/${selectedTime.value}`);
    const data = res.data;
    entries.value = data.entries.length > 0 ? data.entries.map(e => ({ ...e })) : [{ antenna_code: "", status: "" }];
    info.value = { created_by: data.created_by, version: data.version };
  } catch (e) {
    entries.value = [{ antenna_code: "", status: "" }];
    info.value = {};
  }
}

async function save() {
  saving.value = true;
  error.value = "";
  success.value = "";
  try {
    await axios.post("/uv-plane/", {
      date: selectedDate.value,
      slot_id: selectedTime.value,
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
    const res = await axios.get(`/uv-plane/${selectedDate.value}/${selectedTime.value}/history`);
    history.value = res.data.versions || [];
  } catch (e) { history.value = []; }
}

watch(showHistory, (val) => { if (val) loadHistory(); });

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
