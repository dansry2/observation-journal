<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Журнал ошибок антенн</h1>
      <v-spacer />
      <div class="d-flex align-center mr-2">
        <v-btn icon="mdi-chevron-left" variant="text" density="comfortable" @click="changeDay(-1)" />
        <v-text-field v-model="selectedDate" type="date" label="Дата" variant="outlined" density="compact" style="max-width: 200px" hide-details @change="loadData" />
        <v-btn icon="mdi-chevron-right" variant="text" density="comfortable" @click="changeDay(1)" />
      </div>
      <v-select v-model="selectedGrid" :items="grids" item-title="name" item-value="id" label="Диапазон" variant="outlined" density="compact" style="max-width: 200px" hide-details @change="loadData" />
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error = ''">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" closable class="mb-4" @click:close="success = ''">{{ success }}</v-alert>

    <v-card v-for="(entry, idx) in entries" :key="idx" class="mb-3">
      <v-card-text>
        <div class="d-flex align-center ga-2 flex-wrap">
          <v-combobox v-model="entry.antenna_code" :items="antennaList" :custom-filter="filterAntennas" label="Антенна" density="compact" variant="outlined" style="max-width: 150px" hide-details />
          <v-select v-model="entry.eventType" :items="eventTypes" item-title="label" item-value="value" label="Тип" density="compact" variant="outlined" style="max-width: 200px" hide-details @update:model-value="onTypeChange(entry)" />
          <template v-if="entry.eventType === 'other'">
            <v-text-field v-model="entry.dateStart" type="date" label="Начало" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="entry.timeStart" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
            <v-text-field v-model="entry.dateEnd" type="date" label="Конец" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="entry.timeEnd" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
          </template>
          <template v-else>
            <v-text-field v-model="entry.date" type="date" label="Дата" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="entry.time" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
          </template>
          <v-text-field v-model="entry.note" label="Заметка" density="compact" variant="outlined" hide-details style="min-width: 200px; flex: 1" />
          <v-btn icon="mdi-plus" variant="text" color="primary" size="small" @click="addNestedEvent(entry)" />
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="removeEntry(entry)" />
        </div>

        <div v-for="(ev, evIdx) in entry.nested" :key="evIdx" class="d-flex align-center ga-2 flex-wrap ml-8 mt-2" :style="ev.future ? 'opacity: 0.5' : ''">
          <v-icon size="small" :color="ev.future ? 'info' : 'grey'">{{ ev.future ? 'mdi-clock-outline' : 'mdi-subdirectory-arrow-right' }}</v-icon>
          <v-select v-model="ev.eventType" :items="eventTypes" item-title="label" item-value="value" label="Тип" density="compact" variant="outlined" style="max-width: 200px" hide-details />
          <template v-if="ev.eventType === 'other'">
            <v-text-field v-model="ev.dateStart" type="date" label="Начало" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="ev.timeStart" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
            <v-text-field v-model="ev.dateEnd" type="date" label="Конец" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="ev.timeEnd" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
          </template>
          <template v-else>
            <v-text-field v-model="ev.date" type="date" label="Дата" density="compact" variant="outlined" style="max-width: 160px" hide-details />
            <v-text-field v-model="ev.time" type="time" label="Время" density="compact" variant="outlined" style="max-width: 120px" hide-details />
          </template>
          <v-text-field v-model="ev.note" label="Заметка" density="compact" variant="outlined" hide-details style="min-width: 200px; flex: 1" />
          <v-btn icon="mdi-delete" variant="text" color="error" size="small" @click="entry.nested.splice(evIdx, 1)" />
        </div>
      </v-card-text>
    </v-card>

    <v-btn variant="outlined" class="mb-4" @click="addAntenna">
      <v-icon class="mr-2">mdi-plus</v-icon> Добавить антенну
    </v-btn>

    <v-text-field v-model="changeNote" label="Примечание к диапазону" variant="outlined" hide-details class="mb-4" hint="Общее примечание" persistent-hint />

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

    <v-dialog v-model="nextDaysDialog" max-width="500">
      <v-card>
        <v-card-title>Внимание!</v-card-title>
        <v-card-text>
          После этой даты есть активные записи:
          <ul>
            <li v-for="d in nextDates" :key="d">{{ d }}</li>
          </ul>
          Они будут <strong>перезаписаны</strong> при сохранении. Продолжить?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="outlined" @click="nextDaysDialog = false">Отмена</v-btn>
          <v-btn color="warning" @click="proceedSaveAfterNextDays">Продолжить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title>Удалить антенну?</v-card-title>
        <v-card-text>
          Удалить запись для антенны <strong>{{ deleteTarget?.antenna_code }}</strong>?
          Это действие будет отмечено как "удалено пользователем" в истории.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="outlined" @click="deleteDialog = false; deleteTarget = null">Отмена</v-btn>
          <v-btn color="error" @click="confirmDelete">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="confirmDialog" max-width="500">
      <v-card>
        <v-card-title>Подтверждение</v-card-title>
        <v-card-text>Вы изменяете существующие данные. Продолжить?</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="outlined" @click="confirmDialog = false; loadData()">Отмена</v-btn>
          <v-btn color="primary" @click="doSave">Продолжить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import axios from "axios";

const selectedDate = ref(new Date().toISOString().substr(0, 10));
const selectedGrid = ref(5);
const entries = ref([]);

function hasRestore(entry) {
  const all = [entry, ...(entry.nested || [])];
  return all.some(e => e.eventType === "restore");
}
const changeNote = ref("");
const error = ref("");
const success = ref("");
const saving = ref(false);
const showHistory = ref(false);
const confirmDialog = ref(false);
const deleteDialog = ref(false);
const nextDaysDialog = ref(false);
const nextDates = ref([]);
const originalSnapshot = ref("");
const deleteTarget = ref(null);
const info = ref({});
const history = ref([]);
const grids = ref([
  { id: 5, name: "3-6 ГГц" },
  { id: 6, name: "6-12 ГГц" },
  { id: 7, name: "12-24 ГГц" },
]);
const antennaList = ref([]);

const eventTypes = [
  { label: "Поломка", value: "breakdown" },
  { label: "Восстановление", value: "restore" },
  { label: "Другое", value: "other" },
];

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

function makeEmptyEvent() {
  return {
    eventType: "breakdown",
    date: selectedDate.value,
    time: "",
    dateStart: selectedDate.value,
    timeStart: "",
    dateEnd: "",
    timeEnd: "",
    note: "",
  };
}

function removeEntry(entry) {
  // Если у антенны нет day_id — она ещё не сохранена на сервере, удаляем из UI
  if (!entry.day_id) {
    const idx = entries.value.indexOf(entry);
    if (idx !== -1) entries.value.splice(idx, 1);
    return;
  }
  deleteTarget.value = entry;
  deleteDialog.value = true;
}

async function confirmDelete() {
  const entry = deleteTarget.value;
  if (!entry) return;

  const dayId = entry.day_id || info.value.day_id;
  if (!dayId) {
    const idx = entries.value.indexOf(entry);
    if (idx !== -1) entries.value.splice(idx, 1);
    deleteDialog.value = false;
    deleteTarget.value = null;
    return;
  }

  try {
    await axios.delete(`errors-grid/entry/${dayId}/${entry.antenna_code}`);
    const idx = entries.value.indexOf(entry);
    if (idx !== -1) entries.value.splice(idx, 1);
    success.value = `Антенна ${entry.antenna_code} удалена`;
    deleteDialog.value = false;
    deleteTarget.value = null;
    await loadData();
  } catch (err) {
    error.value = err.response?.data?.detail || "Ошибка удаления";
    deleteDialog.value = false;
  }
}

function addAntenna() {
  entries.value.push({
    antenna_code: "",
    ...makeEmptyEvent(),
    nested: [],
  });
}

function addNestedEvent(entry) {
  entry.nested.push(makeEmptyEvent());
}

function onTypeChange(entry) {
  if (entry.eventType !== "other") {
    entry.date = entry.date || selectedDate.value;
    entry.dateStart = "";
    entry.timeStart = "";
    entry.dateEnd = "";
    entry.timeEnd = "";
  } else {
    entry.dateStart = entry.dateStart || selectedDate.value;
    entry.date = "";
    entry.time = "";
  }
}

function buildEventsFromEntry(entry) {
  const events = [];
  const main = {
    id: entry.id || `ev-${Math.random().toString(36).substr(2, 9)}`,
    type: entry.eventType,
    note: entry.note || null,
  };
  if (entry.eventType === "other") {
    main.date = entry.dateStart || null;
    main.time = entry.timeStart || null;
    main.date_end = entry.dateEnd || null;
    main.time_end = entry.timeEnd || null;
  } else {
    main.date = entry.date || null;
    main.time = entry.time || null;
  }
  events.push(main);

  for (const ev of (entry.nested || [])) {
    if (ev.future) continue;
    const nested = {
      id: ev.id || `ev-${Math.random().toString(36).substr(2, 9)}`,
      type: ev.eventType,
      note: ev.note || null,
    };
    if (ev.eventType === "other") {
      nested.date = ev.dateStart || null;
      nested.time = ev.timeStart || null;
      nested.date_end = ev.dateEnd || null;
      nested.time_end = ev.timeEnd || null;
    } else {
      nested.date = ev.date || null;
      nested.time = ev.time || null;
    }
    events.push(nested);
  }

  return events;
}

async function loadRefs() {
  const res = await axios.get("api/v1/references", { headers: { "X-API-Key": import.meta.env.VITE_API_KEY || "YOUR_API_KEY_HERE" } });
  antennaList.value = (res.data.antennas || []).map(a => a.code);
}

async function loadData() {
  entries.value = [];
  info.value = {};
  error.value = "";
  success.value = "";
  try {
    const res = await axios.get(`errors-grid/${selectedDate.value}/${selectedGrid.value}`);
    const data = res.data.entries || [];
    entries.value = data.map(e => {
      const rawEvents = e.events || [];
      const hasDeleted = rawEvents.some(ev => ev.type === "deleted");
      if (hasDeleted) return null;
      const events = rawEvents;
      const first = events[0] || {};
      const nested = events.slice(1).map(ev => ({
        id: ev.id,
        eventType: ev.type,
        date: ev.date || "",
        time: ev.time || "",
        dateStart: ev.date || "",
        timeStart: ev.time || "",
        dateEnd: ev.date_end || "",
        timeEnd: ev.time_end || "",
        note: ev.note || "",
        future: ev.future || false,
      }));
      return {
        day_id: e.day_id,
        id: first.id,
        antenna_code: e.antenna_code,
        eventType: first.type || "breakdown",
        date: first.date || selectedDate.value,
        time: first.time || "",
        dateStart: first.date || selectedDate.value,
        timeStart: first.time || "",
        dateEnd: first.date_end || "",
        timeEnd: first.time_end || "",
        note: first.note || "",
        nested: nested,
      };
    }).filter(Boolean);
    // Снимок только существующих событий (с id)
    const snapshot = {};
    for (const e of entries.value) {
      const allEvents = [e, ...(e.nested || [])];
      for (const ev of allEvents) {
        if (ev.id) {
          snapshot[ev.id] = {
            eventType: ev.eventType,
            date: ev.date,
            time: ev.time,
            dateStart: ev.dateStart,
            timeStart: ev.timeStart,
            note: ev.note,
          };
        }
      }
    }
    originalSnapshot.value = JSON.stringify(snapshot);

    // Сортировка: активные (без restore) сверху, закрытые (с restore) снизу
    entries.value.sort((a, b) => {
      const aHasRestore = [a, ...(a.nested || [])].some(x => x.eventType === "restore");
      const bHasRestore = [b, ...(b.nested || [])].some(x => x.eventType === "restore");
      if (aHasRestore !== bHasRestore) return aHasRestore ? 1 : -1;
      return 0;
    });

    info.value = { created_by: res.data.created_by, version: res.data.version, day_id: res.data.id };
  } catch (e) {}
}

async function save() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    error.value = "Войдите в систему, чтобы вносить изменения";
    return;
  }

  error.value = "";
  success.value = "";

  const filtered = entries.value.filter(e => e.antenna_code);
  if (filtered.length === 0) {
    error.value = "Добавьте хотя бы одну антенну";
    return;
  }

  // Проверяем, есть ли НОВОЕ закрывающее событие (restore без id)
  const hasNewClosing = entries.value.some(e => {
    const all = [e, ...(e.nested || [])];
    return all.some(ev => ev.eventType === "restore" && !ev.id);
  });

  if (hasNewClosing) {
    try {
      const checkNext = await axios.get(`errors-grid/check-next-days/${selectedDate.value}/${selectedGrid.value}`);
      if (checkNext.data.next_dates && checkNext.data.next_dates.length > 0) {
        nextDates.value = checkNext.data.next_dates;
        nextDaysDialog.value = true;
        return;
      }
    } catch (e) {}
  }

  // Проверяем, изменились ли существующие данные
  const hasExistingEntries = entries.value.some(e => e.day_id);
  if (info.value.version && hasExistingEntries) {
    const currentSnapshot = {};
    for (const e of entries.value) {
      const allEvents = [e, ...(e.nested || [])];
      for (const ev of allEvents) {
        if (ev.id) {
          currentSnapshot[ev.id] = {
            eventType: ev.eventType,
            date: ev.date,
            time: ev.time,
            dateStart: ev.dateStart,
            timeStart: ev.timeStart,
            note: ev.note,
          };
        }
      }
    }

    const cur = JSON.stringify(currentSnapshot);
    const orig = originalSnapshot.value;
    if (cur !== orig) {
      confirmDialog.value = true;
      return;
    }
  }

  await doSave();
}

async function proceedSaveAfterNextDays() {
  nextDaysDialog.value = false;
  await doSave();
}

async function doSave() {
  confirmDialog.value = false;

  const token = localStorage.getItem("access_token");
  if (!token) {
    error.value = "Войдите в систему, чтобы вносить изменения";
    return;
  }

  const filtered = entries.value.filter(e => e.antenna_code);

  for (const e of filtered) {
    const allEvents = [e, ...(e.nested || [])].filter(ev => ev.eventType === "breakdown" || ev.eventType === "restore");
    for (const ev of allEvents) {
      if (!ev.date) {
        error.value = `Укажите дату для события "${ev.eventType === "breakdown" ? "Поломка" : "Восстановление"}" антенны ${e.antenna_code}`;
        return;
      }
      if (!ev.time) {
        error.value = `Укажите время для события "${ev.eventType === "breakdown" ? "Поломка" : "Восстановление"}" антенны ${e.antenna_code}`;
        return;
      }
    }

    // Проверка последовательности breakdown → restore
    const breakdown = allEvents.find(ev => ev.eventType === "breakdown");
    const restore = allEvents.find(ev => ev.eventType === "restore");

    // Нельзя восстановить то, что не сломано
    if (restore && !breakdown) {
      error.value = `У антенны ${e.antenna_code} есть восстановление, но нет поломки. Сначала добавьте поломку.`;
      return;
    }

    if (breakdown && restore) {
      const bDT = new Date(`${breakdown.date}T${breakdown.time}`);
      const rDT = new Date(`${restore.date}T${restore.time}`);
      if (rDT <= bDT) {
        error.value = `У антенны ${e.antenna_code} время восстановления (${restore.date} ${restore.time}) должно быть позже времени поломки (${breakdown.date} ${breakdown.time})`;
        return;
      }
    }
  }

  saving.value = true;
  try {
    const payload = {
      date: selectedDate.value,
      grid_id: selectedGrid.value,
      entries: filtered.map(e => ({
        antenna_code: e.antenna_code,
        error_description: e.note || null,
        is_ok: !hasOpenBreakdown(e),
        events: buildEventsFromEntry(e),
      })),
      change_note: changeNote.value || "Обновление",
      is_ok: true,
    };
    await axios.post("errors-grid/", payload);
    success.value = "Сохранено!";
    await loadData();
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка сохранения";
  } finally {
    saving.value = false;
  }
}

function hasOpenBreakdown(entry) {
  const all = [entry, ...(entry.nested || [])];
  const hasBreakdown = all.some(e => e.eventType === "breakdown");
  const hasRestore = all.some(e => e.eventType === "restore");
  return hasBreakdown && !hasRestore;
}

async function loadHistory() {
  try {
    const res = await axios.get(`errors-grid/${selectedDate.value}/${selectedGrid.value}/history`);
    history.value = res.data.versions || [];
  } catch (e) { history.value = []; }
}

function changeDay(delta) {
  const d = new Date(selectedDate.value);
  d.setDate(d.getDate() + delta);
  selectedDate.value = d.toISOString().substr(0, 10);
  loadData();
}

watch(showHistory, (val) => { if (val) loadHistory(); });
watch(selectedGrid, () => { loadData(); });

onMounted(async () => {
  await loadRefs();
  await loadData();
});
</script>
