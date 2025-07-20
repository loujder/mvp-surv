import { ref, computed } from 'vue'
import { useAuthStore } from './authStore'

interface GamePlayer {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  isEliminated?: boolean
  is_admin?: boolean
}

interface LobbyPlayer {
  user_id: string
  nickname: string
  joined_at: string
  is_active: boolean
  is_admin?: boolean
  is_observer?: boolean
  is_joined?: boolean
  is_ready?: boolean
  is_in_game?: boolean
  is_eliminated?: boolean
  is_winner?: boolean
}

const gamePlayers = ref<GamePlayer[]>([])
const lobbyPlayers = ref<LobbyPlayer[]>([])
const gameStarted = ref(false)
const currentRound = ref(1)
const isPlayerInGame = ref(false)

const generateRandomColor = (): string => {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
  ]
  return colors[Math.floor(Math.random() * colors.length)]
}

const addPlayerToGame = (): boolean => {
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }
  const existingPlayer = gamePlayers.value.find(p => p.id === authStore.user!.user_id)
  if (existingPlayer) return false
  const gamePlayer: GamePlayer = {
    id: authStore.user.user_id,
    name: authStore.user.nickname,
    color: generateRandomColor(),
    avatar: authStore.user.nickname.charAt(0).toUpperCase(),
    isCurrentUser: true,
    isEliminated: false
  }
  gamePlayers.value.push(gamePlayer)
  isPlayerInGame.value = true
  return true
}

const removePlayerFromGame = (playerId: string) => {
  const index = gamePlayers.value.findIndex(p => p.id === playerId)
  if (index !== -1) {
    gamePlayers.value.splice(index, 1)
  }
}

const resetGame = () => {
  gamePlayers.value = []
  gameStarted.value = false
  currentRound.value = 1
  isPlayerInGame.value = false
}

const playerCount = computed(() => gamePlayers.value.length)
const activePlayers = computed(() => gamePlayers.value.filter(p => !p.isEliminated))
const activePlayerCount = computed(() => activePlayers.value.length)

const savePlayerInGameStatus = () => {
  localStorage.setItem('isPlayerInGame', isPlayerInGame.value ? '1' : '0')
}

const loadPlayerInGameStatus = () => {
  const stored = localStorage.getItem('isPlayerInGame')
  if (stored) {
    isPlayerInGame.value = stored === '1'
  }
}

loadPlayerInGameStatus()

let originalIsPlayerInGame = isPlayerInGame.value
Object.defineProperty(isPlayerInGame, 'value', {
  get() {
    return originalIsPlayerInGame
  },
  set(newValue) {
    originalIsPlayerInGame = newValue
    savePlayerInGameStatus()
  }
})

export {
  gamePlayers,
  lobbyPlayers,
  gameStarted,
  currentRound,
  isPlayerInGame,
  addPlayerToGame,
  removePlayerFromGame,
  resetGame,
  playerCount,
  activePlayers,
  activePlayerCount
}