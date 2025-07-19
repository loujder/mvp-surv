import { ref, computed } from 'vue'
import { useAuthStore } from './authStore'

interface Player {
  id: string
  name: string
  color: string
  balance: number
  avatar: string
}

const generateRandomColor = (): string => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
  ]
  return colors[Math.floor(Math.random() * colors.length)]
}

const currentPlayer = ref<Player | null>(null)

const initializePlayer = () => {
  if (!currentPlayer.value) {
    currentPlayer.value = {
      id: '',
      name: '',
      color: generateRandomColor(),
      balance: 0,
      avatar: ''
    }
  }
}

initializePlayer()

const deductCoin = async (): Promise<boolean> => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }
  try {
    const response = await fetch('/api/coins/deduct', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: authStore.user.user_id,
        amount: 1
      })
    })
    if (response.ok) {
      const data = await response.json()
      if (currentPlayer.value) {
        currentPlayer.value.balance = data.balance
      }
      return true
    } else {
      const errorData = await response.json()
      return false
    }
  } catch (error) {
    return false
  }
}

const addCoins = async (amount: number): Promise<boolean> => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }
  try {
    const response = await fetch('/api/coins/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: authStore.user.user_id,
        amount: amount
      })
    })
    if (response.ok) {
      const data = await response.json()
      if (currentPlayer.value) {
        currentPlayer.value.balance = data.balance
      }
      return true
    } else {
      const errorData = await response.json()
      return false
    }
  } catch (error) {
    return false
  }
}

const loadBalance = async (): Promise<void> => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated || !authStore.user) {
    return
  }
  try {
    const response = await fetch(`/api/coins/balance?user_id=${authStore.user.user_id}`)
    if (response.ok) {
      const data = await response.json()
      if (currentPlayer.value) {
        currentPlayer.value.balance = data.balance
        currentPlayer.value.id = authStore.user.user_id
        currentPlayer.value.name = authStore.user.nickname
        currentPlayer.value.avatar = authStore.user.nickname.charAt(0).toUpperCase()
      }
    }
  } catch (error) {
  }
}

const playerName = computed(() => {
  const authStore = useAuthStore()
  return authStore.isAuthenticated && authStore.user ? authStore.user.nickname : (currentPlayer.value?.name || '')
})

const playerBalance = computed(() => currentPlayer.value?.balance || 0)
const playerColor = computed(() => currentPlayer.value?.color || '#666')
const playerAvatar = computed(() => {
  const authStore = useAuthStore()
  return authStore.isAuthenticated && authStore.user ? authStore.user.nickname.charAt(0).toUpperCase() : (currentPlayer.value?.avatar || 'P')
})

const canJoinGame = computed(() => currentPlayer.value && currentPlayer.value.balance > 0)

export {
  currentPlayer,
  initializePlayer,
  deductCoin,
  addCoins,
  loadBalance,
  playerName,
  playerBalance,
  playerColor,
  playerAvatar,
  canJoinGame
}