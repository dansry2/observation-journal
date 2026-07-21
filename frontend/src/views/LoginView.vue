<template>
  <v-app>
    <v-container class="fill-height" fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <v-card class="pa-6">
            <v-card-title class="text-center text-h4 mb-4">Журнал наблюдений</v-card-title>
            <v-card-subtitle class="text-center mb-6">Вход в систему</v-card-subtitle>
            <v-form @submit.prevent="login">
              <v-text-field v-model="username" label="Логин" prepend-inner-icon="mdi-account" variant="outlined" required />
              <v-text-field v-model="password" label="Пароль" :type="showPassword ? 'text' : 'password'" prepend-inner-icon="mdi-lock" variant="outlined" required>
                <template #append-inner>
                  <v-icon @click="showPassword = !showPassword">{{ showPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
                </template>
              </v-text-field>
              <v-btn type="submit" color="primary" block size="large" :loading="loading">Войти</v-btn>
            </v-form>
            <v-divider class="my-4" />
            <v-btn variant="text" block @click="$router.push('/register')">Регистрация</v-btn>
            <v-alert v-if="error" type="error" class="mt-4" closable>{{ error }}</v-alert>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");
const showPassword = ref(false);

async function login() {
  loading.value = true;
  error.value = "";
  try {
    await auth.login(username.value, password.value);
    router.push("/");
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка входа";
  } finally { loading.value = false; }
}
</script>
