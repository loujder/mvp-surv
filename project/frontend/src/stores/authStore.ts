import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface TelegramUser {
  chat_id: string
  user_id: string
  nickname: string
  first_name?: string
  last_name?: string
  username?: string
  balance: number
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<TelegramUser | null>(null)
  const isAuthenticated = computed(() => !!user.value)

  const login = (userData: TelegramUser) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const register = async (userData: TelegramUser) => {
    // Для Telegram Web App регистрация происходит автоматически при первом входе
    login(userData)
  }

  const logout = () => {
    user.value = null
    localStorage.removeItem('user')
  }

  const updateBalance = (newBalance: number) => {
    if (user.value) {
      user.value.balance = newBalance
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  const loadUserFromStorage = () => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Error loading user from storage:', e)
        localStorage.removeItem('user')
      }
    }
  }

  const fetchUserData = async (chatId: string) => {
    try {
      const response = await fetch(`/api/user?chat_id=${chatId}`)
      if (response.ok) {
        const userData = await response.json()
        login(userData)
        return userData
      }
    } catch (error) {
      console.error('Error fetching user data:', error)
    }
    return null
  }

  // Загружаем пользователя из localStorage при инициализации
  loadUserFromStorage()

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    updateBalance,
    fetchUserData
  }
})