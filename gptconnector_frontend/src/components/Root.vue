<template>
  <v-card>
    <v-tabs v-model="tab"
      bg-color="primary"
    >
      <v-tab value="one">Первичные настройки приложения</v-tab>
      <v-tab value="two">Последние запросы</v-tab>
    </v-tabs>

    <v-card-text>
      <v-window v-model="tab">
        <v-window-item value="one">
          <v-text-field label="Ключ OpenAI" v-model="api_key"></v-text-field>
          <v-btn @click="saveApiKey">Сохранить ключ</v-btn>
        </v-window-item>

        <v-window-item value="two">
          Тут будут последние 10 запросов:)
        </v-window-item>

      </v-window>
    </v-card-text>
  </v-card>
</template>

<script>
  import api from '../api'

  export default {
    data: () => ({
      tab: null,
      api_key: null,
    }),
    methods: {
      async saveApiKey() {
        const {users} = await api.saveApiKey({
          api_key: this.api_key
        })
        this.users = users
      },
    }
  }
</script>
