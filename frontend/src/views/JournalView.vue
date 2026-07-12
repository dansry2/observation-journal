<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Журнал наблюдений</h1>
      <v-spacer />
      <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4">{{ success }}</v-alert>

    <v-card v-if="loading" class="pa-6"><v-progress-circular indeterminate color="primary" /><span class="ml-3">Загрузка...</span></v-card>

    <template v-if="!loading && ready">
      <v-card class="mb-4" variant="outlined">
        <v-card-title class="d-flex align-center">Погода и температура <v-spacer /><v-chip v-if="weatherFilled" color="success" size="small" variant="tonal">Заполнено</v-chip><v-chip v-else color="warning" size="small" variant="tonal">Не заполнено</v-chip></v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col v-for="h in 11" :key="h" cols="12" sm="6" md="4" lg="3">
              <v-card variant="outlined" :border="hourFilled(h-1) ? 'success' : 'warning'" class="pa-2">
                <div class="text-caption mb-1">{{ (h-1).toString().padStart(2, '0') }}:00</div>
                <v-text-field v-model="weather[h-1].temperature" label="°C" type="number" density="compact" variant="outlined" hide-details class="mb-1" />
                <v-select v-model="weather[h-1].weather_type_id" :items="weatherTypes" item-title="name" item-value="id" label="Погода" density="compact" variant="outlined" hide-details clearable />
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card class="mb-4" variant="outlined">
        <v-card-title class="d-flex align-center">Оборудование (пуск/стоп) <v-spacer /><v-chip v-if="equipFilled" color="success" size="small" variant="tonal">Заполнено</v-chip><v-chip v-else color="warning" size="small" variant="tonal">Не заполнено</v-chip></v-card-title>
        <v-card-text>
          <div v-for="eq in equipmentRanges" :key="eq.id" class="mb-3">
            <div class="text-subtitle-2 mb-1">{{ eq.name }}</div>
            <v-row dense>
              <v-col cols="6" sm="3"><v-text-field v-model="equipment[eq.id].time_start" label="Начало" type="time" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="6" sm="3"><v-text-field v-model="equipment[eq.id].time_stop" label="Конец" type="time" density="compact" variant="outlined" hide-details /></v-col>
              <v-col cols="12" sm="6"><v-text-field v-model="equipment[eq.id].note" label="Примечание" density="compact" variant="outlined" hide-details /></v-col>
            </v-row>
          </div>
        </v-card-text>
      </v-card>

      <v-card class="mb-4" variant="outlined">
        <v-card-title class="d-flex align-center">Дежурные <v-spacer /><v-chip v-if="dutyUserIds.length > 0 || dutyCustom" color="success" size="small" variant="tonal">Заполнено</v-chip><v-chip v-else color="warning" size="small" variant="tonal">Не заполнено</v-chip></v-card-title>
        <v-card-text>
          <v-select v-model="dutyUserIds" :items="users" item-title="full_name" item-value="id" label="Дежурные (из зарегистрированных)" multiple chips variant="outlined" />
          <v-text-field v-model="dutyCustom" label="Дополнительные дежурные (через запятую)" variant="outlined" hide-details class="mt-2" placeholder="Например: Иванов, Петров" />
        </v-card-text>
      </v-card>

      <v-text-field v-model="changeNote" label="Примечание к изменению" variant="outlined" hide-details class="mb-4" />

      <div v-if="info.created_by" class="mb-2 text-body-2">Создал: {{ info.created_by }} | Версия: {{ info.version }}</div>

      <div class="d-flex ga-2 mb-4">
        <v-btn color="primary" size="large" @click="save" :loading="saving">Сохранить</v-btn>
        <v-btn variant="outlined" @click="showHistory = true" v-if="info.version">История (v{{ info.version }})</v-btn>
      </div>
    </template>

    <v-dialog v-model="showHistory" max-width="800">
      <v-card>
        <v-card-title>История — {{ selectedDate }}</v-card-title>
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
import { ref, computed, onMounted, watch } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const loading = ref(true);
const saving = ref(false);
const ready = ref(false);
const error = ref("");
const success = ref("");
const showHistory = ref(false);
const weather = ref({});
const equipment = ref({});
const dutyUserIds = ref([]);
const dutyCustom = ref("");
const changeNote = ref("");
const info = ref({});
const history = ref([]);
const weatherTypes = ref([]);
const equipmentRanges = ref([]);
const users = ref([]);

function initEmpty() {
  const w = {};
  for (let h = 0; h < 11; h++) w[h] = { hour: h, temperature: null, weather_type_id: null };
  weather.value = w;
  const e = {};
  for (const eq of equipmentRanges.value) e[eq.id] = { equipment_range_id: eq.id, time_start: null, time_stop: null, note: null };
  equipment.value = e;
  dutyUserIds.value = [];
  dutyCustom.value = "";
  changeNote.value = "";
  info.value = {};
}

async function loadRefs() {
  const res = await axios.get("/api/v1/references", { headers: { "X-API-Key": "ak_5e013c70196a73ec479597dc68fa8b2b" } });
  weatherTypes.value = res.data.weather_types || [];
  equipmentRanges.value = res.data.equipment_ranges || [];
}

async function loadUsers() {
  try {
    const res = await axios.get("/users");
    users.value = res.data || [];
  } catch (e) {}
}

async function loadData() {
  loading.value = true;
  error.value = "";
  initEmpty();
  try {
    const res = await axios.get(`/observations/${selectedDate.value}`);
    const data = res.data;
    info.value = { created_by: data.created_by, updated_by: data.updated_by, version: data.version };
    for (const w of data.weather || []) weather.value[w.hour] = { hour: w.hour, temperature: w.temperature, weather_type_id: w.weather_type_id };
    for (const e of data.equipment || []) equipment.value[e.equipment_range_id] = { equipment_range_id: e.equipment_range_id, time_start: e.time_start, time_stop: e.time_stop, note: e.note };
    dutyUserIds.value = data.duty_user_ids || [];
    dutyCustom.value = data.duty_custom || "";
  } catch (e) {
    if (e.response?.status !== 404) error.value = "Ошибка загрузки";
  } finally { loading.value = false; }
}

async function save() {
  saving.value = true;
  error.value = "";
  success.value = "";
  const wl = Object.values(weather.value).filter(w => w.temperature !== null || w.weather_type_id !== null);
  const el = Object.values(equipment.value).filter(e => e.time_start || e.time_stop || e.note);
  try {
    await axios.post("/observations/", {
      date: selectedDate.value,
      weather: wl,
      equipment: el,
      duty_user_ids: dutyUserIds.value,
      duty_custom: dutyCustom.value,
      change_note: changeNote.value || "Обновление"
    });
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка сохранения";
  } finally { saving.value = false; }
}

async function loadHistory() {
  try {
    const res = await axios.get(`/observations/${selectedDate.value}/history`);
    history.value = res.data.versions || [];
  } catch (e) { history.value = []; }
}

const weatherFilled = computed(() => Object.values(weather.value).some(w => w.temperature !== null || w.weather_type_id !== null));
const equipFilled = computed(() => Object.values(equipment.value).some(e => e.time_start || e.time_stop || e.note));
function hourFilled(h) { const w = weather.value[h]; return w && (w.temperature !== null || w.weather_type_id !== null); }

watch(showHistory, (val) => { if (val) loadHistory(); });

onMounted(async () => {
  await loadRefs();
  await loadUsers();
  initEmpty();
  await loadData();
  ready.value = true;
});
</script>
