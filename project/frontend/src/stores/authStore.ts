import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<{ user_id: string; nickname: string; balance?: number } | null>(null)

  const isAuthenticated = computed(() => !!user.value)

  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      user.value = JSON.parse(storedUser)
    } catch (e) {
      localStorage.removeItem('user')
    }
  }

  const login = (userData: { user_id: string; nickname: string; balance?: number }) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  const register = async (userData: { user_id: string; nickname: string }) => {
    login(userData)
  }

  const logout = () => {
    user.value = null
    localStorage.removeItem('user')
  }

  const updateBalance = (newBalance: number) => {
    if (user.value) {
      user.value = {
        ...user.value,
        balance: newBalance
      }
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  const fetchUserData = async (userId: string) => {
    try {
      const response = await fetch(`/api/user?user_id=${userId}`)
      if (response.ok) {
        const userData = await response.json()
        login({
          user_id: userData.user_id,
          nickname: userData.nickname,
          balance: userData.balance
        })
        return true
      }
    } catch (error) {
    }
    return false
  }

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