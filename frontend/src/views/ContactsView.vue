<template>
  <div>
    <h1 class="text-h4 mb-4">Контакты</h1>
    <v-card class="pa-6">
      <v-list>
        <v-list-item>
          <template #prepend>
            <v-icon color="primary">mdi-shield-account</v-icon>
          </template>
          <v-list-item-title>Администратор</v-list-item-title>
          <v-list-item-subtitle>Грабельных Даниил</v-list-item-subtitle>
        </v-list-item>
        <v-divider />
        <v-list-item>
          <template #prepend>
            <v-icon color="primary">mdi-email</v-icon>
          </template>
          <v-list-item-title>Email</v-list-item-title>
          <v-list-item-subtitle>
            <a href="mailto:dansry2@mail.ru">dansry2@mail.ru</a>
          </v-list-item-subtitle>
        </v-list-item>
        <v-divider />
        <v-list-item>
          <template #prepend>
            <v-icon color="primary">mdi-phone</v-icon>
          </template>
          <v-list-item-title>Телефон</v-list-item-title>
          <v-list-item-subtitle>
            <a href="tel:+79246330474">+7 924 633-04-74</a>
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>
