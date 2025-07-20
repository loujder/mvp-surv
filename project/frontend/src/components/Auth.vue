<template>
  <div class="auth-container">
    <div v-if="isAuthenticated && user" class="welcome">
      <h2>Добро пожаловать, {{ user.nickname }}!</h2>
      <p>Ваш Chat ID: {{ user.chat_id }}</p>
      <p v-if="user.is_admin" class="admin-badge">👑 Администратор</p>
      <button @click="logout" class="logout-btn">Выйти</button>
    </div>
    <div v-else class="loading">
      <div class="loader"></div>
      <p>Подключение к Telegram...</p>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'

const emit = defineEmits<{
  'auth-success': []
}>()

const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)

const error = ref('')
const loading = ref(true)

const authenticateWithTelegram = async () => {
  try {
    // Проверяем, что мы в Telegram Web App
    if (!window.Telegram?.WebApp) {
      error.value = 'Это приложение должно быть открыто в Telegram'
      return
    }

    const webApp = window.Telegram.WebApp
    
    // Инициализируем Web App
    webApp.ready()
    webApp.expand()
    
    // Получаем InitData
    const initData = webApp.initData
    if (!initData) {
      error.value = 'Не удалось получить данные от Telegram'
      return
    }

    // Отправляем данные на сервер для аутентификации
    const response = await fetch('/api/telegram/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ initData })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Ошибка аутентификации')
    }

    const data = await response.json()
    
    // Сохраняем пользователя в store
    authStore.login(data.user)
    emit('auth-success')
    
  } catch (err: any) {
    error.value = err.message || 'Ошибка подключения к серверу'
    console.error('Auth error:', err)
  } finally {
    loading.value = false
  }
}

const logout = () => {
  authStore.logout()
}

onMounted(() => {
  authenticateWithTelegram()
})
</script>

<style scoped>
.auth-container {
  max-width: 500px;
  margin: 50px auto;
  padding: 30px;
  background: #2a2a2a;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.welcome {
  padding: 30px;
}

.welcome h2 {
  color: white;
  margin-bottom: 15px;
  font-size: 1.8em;
}

.welcome p {
  color: #bbb;
  margin-bottom: 10px;
  font-size: 1.1em;
}

.admin-badge {
  background: linear-gradient(45deg, #FFD700, #FFA500);
  color: #000 !important;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  display: inline-block;
  margin: 10px 0;
}

.logout-btn {
  padding: 12px 24px;
  background: #EF4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  margin-top: 20px;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: #DC2626;
}

.loading {
  padding: 40px 20px;
  text-align: center;
}

.loader {
  border: 4px solid #333;
  border-top: 4px solid #10B981;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: #ddd;
  font-size: 1.2em;
  margin-bottom: 20px;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid #EF4444;
  border-radius: 8px;
  color: #EF4444;
  text-align: center;
}
</style>

export default {
  name: 'AuthView'
}