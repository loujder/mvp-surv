<template>
  <div class="auth-container">
    <div v-if="isAuthenticated && user" class="welcome">
      <h2>Добро пожаловать, {{ user.nickname }}!</h2>
      <p>Ваш ID: {{ user.user_id }}</p>
      <button @click="logout" class="logout-btn">Выйти</button>
    </div>
    <div v-else>
      <div class="tabs">
        <button @click="mode = 'login'" :class="{ active: mode === 'login' }">Вход</button>
        <button @click="mode = 'register'" :class="{ active: mode === 'register' }">Регистрация</button>
      </div>
      <form @submit.prevent="submitForm" class="auth-form">
        <div class="form-group" v-if="mode === 'register'">
          <label for="nickname">Никнейм:</label>
          <input type="text" id="nickname" v-model="form.nickname" placeholder="Введите ваш никнейм" required />
        </div>
        <div class="form-group">
          <label for="user_id">Уникальный ID:</label>
          <input type="text" id="user_id" v-model="form.user_id" :placeholder="mode === 'register' ? 'Придумайте уникальный ID' : 'Введите ваш ID'" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? 'Загрузка...' : (mode === 'login' ? 'Войти' : 'Зарегистрироваться') }}
        </button>
      </form>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'

const emit = defineEmits<{
  'auth-success': []
}>()

const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)

const mode = ref<'login' | 'register'>('login')
const form = ref({
  user_id: '',
  nickname: ''
})
const error = ref('')
const loading = ref(false)

const submitForm = async () => {
  error.value = ''
  loading.value = true

  try {
    const endpoint = mode.value === 'login' ? '/api/login' : '/api/register'
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form.value)
    })
    let data
    try {
      data = await response.json()
    } catch (parseError) {
      throw new Error('Сервер недоступен. Проверьте, что backend запущен.')
    }
    if (!response.ok) {
      throw new Error(data.error || 'Ошибка сервера')
    }
    if (mode.value === 'login') {
      authStore.login({
        user_id: form.value.user_id,
        nickname: data.nickname
      })
    } else {
      authStore.register({
        user_id: form.value.user_id,
        nickname: form.value.nickname
      })
    }
    form.value = { user_id: '', nickname: '' }
    emit('auth-success')
  } catch (err: any) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const logout = () => {
  authStore.logout()
}
</script>

<style scoped>
.auth-container {
  max-width: 500px;
  margin: 50px auto;
  padding: 30px;
  background: #2a2a2a;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #444;
}

.tabs button {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  color: #aaa;
  font-size: 1.1em;
  cursor: pointer;
  transition: all 0.3s;
}

.tabs button.active {
  color: white;
  border-bottom: 3px solid #10B981;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  color: #ddd;
  font-size: 1em;
}

input {
  padding: 12px 15px;
  border: 1px solid #444;
  border-radius: 8px;
  background: #1a1a1a;
  color: white;
  font-size: 1em;
  transition: border 0.3s;
}

input:focus {
  border-color: #10B981;
  outline: none;
}

.submit-btn {
  padding: 14px;
  background: #10B981;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:hover {
  background: #059669;
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
}

.logout-btn:hover {
  background: #DC2626;
}

.welcome {
  text-align: center;
  padding: 30px;
}

.welcome h2 {
  color: white;
  margin-bottom: 10px;
}

.welcome p {
  color: #bbb;
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