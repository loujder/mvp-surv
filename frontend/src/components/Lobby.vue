<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { socketService, globalTimer, gameTimer } from '../services/socketService'
import { loadBalance } from '../stores/playerStore'

const emit = defineEmits<{
  gameOver: [result: 'win' | 'lose']
  startGame: []
}>()

const props = defineProps<{ selectedLobbyId?: string | null }>()

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const currentLobbyId = ref('')
const lobbyPlayers = ref<any[]>([])
const isInLobby = ref(false)
const isReady = ref(false)
const lobbyBank = ref(0)
const isConnecting = ref(false)
const gameRounds = ref({ current: 1, total: 1 })

const isAdmin = computed(() => authStore.user?.user_id === 'Loujder')

const filteredPlayers = computed(() => {
  return lobbyPlayers.value.filter(player => player.user_id !== 'Loujder')
})

const getLobbies = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/admin/lobbies')
    if (response.ok) {
      const data = await response.json()
      return data.lobbies || []
    }
  } catch (error) {
  }
  return []
}

const joinLobby = async (lobbyId: string) => {
  if (!authStore.isAuthenticated || !authStore.user) {
    error.value = 'Не авторизован'
    return false
  }

  if (isConnecting.value) {
    return false
  }

  isConnecting.value = true
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/lobby/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: authStore.user.user_id,
        lobby_id: lobbyId
      })
    })

    if (response.ok) {
      currentLobbyId.value = lobbyId
      isInLobby.value = true
      localStorage.setItem('currentLobbyId', lobbyId)
      await loadLobbyPlayers()
      return true
    } else {
      const errorData = await response.json()
      error.value = errorData.error || 'Ошибка подключения к лобби'
      return false
    }
  } catch (err: any) {
    error.value = err.message || 'Ошибка подключения к лобби'
    return false
  } finally {
    loading.value = false
    isConnecting.value = false
  }
}

const leaveLobby = async () => {
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }

  loading.value = true
  error.value = ''

  try {
    const response = await fetch('/api/lobby/leave', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: authStore.user.user_id
      })
    })

    if (response.ok) {
      currentLobbyId.value = ''
      isInLobby.value = false
      isReady.value = false
      lobbyPlayers.value = []
      lobbyBank.value = 0
      localStorage.removeItem('currentLobbyId')
      localStorage.removeItem('playerJoinedGame')
      return true
    } else {
      const errorData = await response.json()
      error.value = errorData.error || 'Ошибка выхода из лобби'
      return false
    }
  } catch (err: any) {
    error.value = err.message || 'Ошибка выхода из лобби'
    return false
  } finally {
    loading.value = false
  }
}

const loadLobbyPlayers = async () => {
  if (!currentLobbyId.value) return

  try {
    const apiUrl = isAdmin.value 
      ? `/api/admin/lobby/players?lobby_id=${currentLobbyId.value}`
      : '/api/lobby/players'
    
    const response = await fetch(apiUrl)
    
    if (response.ok) {
      const data = await response.json()
      lobbyPlayers.value = data.players || []
      lobbyBank.value = filteredPlayers.value.length
    }
  } catch (error) {
  }
}

const loadLobbyBank = async () => {
  try {
    const response = await fetch('/api/lobby/players')
    if (response.ok) {
      const data = await response.json()
      const nonAdminPlayers = data.players?.filter((player: any) => player.user_id !== 'Loujder') || []
      lobbyBank.value = nonAdminPlayers.length
    }
  } catch (error) {
  }
}

const loadGameRounds = async () => {
  try {
    const response = await fetch('/api/game/status')
    if (response.ok) {
      const data = await response.json()
      if (data.current_round && data.total_rounds) {
        gameRounds.value = {
          current: data.current_round,
          total: data.total_rounds
        }
      }
    }
  } catch (error) {
  }
}

const joinGame = async () => {
  if (!authStore.isAuthenticated || !authStore.user || !isInLobby.value) {
    error.value = 'Сначала подключитесь к лобби'
    return
  }

  if (isAdmin.value) {
    error.value = 'Администраторы не могут участвовать в игре'
    return
  }

  loading.value = true
  error.value = ''

  try {
    console.log('Attempting to deduct 1 coin for user:', authStore.user.user_id)
    const deductResp = await fetch('/api/coins/deduct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: authStore.user.user_id })
    })
    console.log('Deduct response status:', deductResp.status)
    
    if (!deductResp.ok) {
      const errData = await deductResp.json()
      console.error('Deduct error:', errData)
      error.value = errData.error || 'Не удалось списать монету для готовности'
      loading.value = false
      return
    }
    
    const deductData = await deductResp.json()
    console.log('Deduct success:', deductData)
    
    const response = await fetch('/api/lobby/ready', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: authStore.user.user_id
      })
    })

    if (response.ok) {
      isReady.value = true
      localStorage.setItem('playerJoinedGame', '1')
      try {
        const userResp = await fetch(`/api/user?user_id=${authStore.user.user_id}`)
        if (userResp.ok) {
          const userData = await userResp.json()
          authStore.updateBalance(userData.balance)
          await loadBalance()
        }
      } catch (e) { 
      }
      console.log('Player joined the game')
    } else {
      const errorData = await response.json()
      error.value = errorData.error || 'Ошибка готовности к игре'
    }
  } catch (err: any) {
    console.error('Error in joinGame:', err)
    error.value = err.message || 'Ошибка готовности к игре'
  } finally {
    loading.value = false
  }
}

const autoJoinLobby = async () => {
  if (isAdmin.value && isInLobby.value && props.selectedLobbyId && currentLobbyId.value === props.selectedLobbyId) {
    console.log('Admin already in selected lobby, not switching')
    return
  }

  if (isConnecting.value) {
    console.log('Already connecting, skipping autoJoinLobby')
    return
  }

  const savedLobbyId = localStorage.getItem('currentLobbyId')
  
  if (savedLobbyId) {
    console.log('Using saved lobby ID from admin panel:', savedLobbyId)
    if (isAdmin.value) {
      await joinSpecificLobby(savedLobbyId)
    } else {
      await joinLobby(savedLobbyId)
    }
    localStorage.removeItem('currentLobbyId')
    return
  }

  if (isAdmin.value && props.selectedLobbyId) {
    console.log('Admin connecting to selected lobby:', props.selectedLobbyId)
    await joinSpecificLobby(props.selectedLobbyId)
    return
  }

  if (isAdmin.value) {
    error.value = 'Администратор должен выбрать конкретное лобби'
    return
  }

  const lobbies = await getLobbies()
  const availableLobbies = lobbies.filter((l: any) => l.status === 'waiting')
  
  if (availableLobbies.length === 0) {
    error.value = 'Нет доступных лобби'
    return
  }

  const bestLobby = availableLobbies.sort((a: any, b: any) => b.player_count - a.player_count)[0]
  await joinLobby(bestLobby.lobby_id)
}

const joinSpecificLobby = async (lobbyId: string) => {
  if (!authStore.isAuthenticated || !authStore.user) {
    error.value = 'Не авторизован'
    return false
  }

  if (isConnecting.value) {
    console.log('Already connecting, skipping...')
    return false
  }

  isConnecting.value = true
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`/api/admin/lobby/${lobbyId}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: authStore.user.user_id
      })
    })

    if (response.ok) {
      currentLobbyId.value = lobbyId
      isInLobby.value = true
      localStorage.setItem('currentLobbyId', lobbyId)
      await loadLobbyPlayers()
      console.log('Admin successfully joined specific lobby:', lobbyId)
      return true
    } else {
      const errorData = await response.json()
      error.value = errorData.error || 'Ошибка подключения к лобби'
      return false
    }
  } catch (err: any) {
    error.value = err.message || 'Ошибка подключения к лобби'
    return false
  } finally {
    loading.value = false
    isConnecting.value = false
  }
}

const resetReadyStatus = async () => {
  if (!authStore.isAuthenticated || !authStore.user) return

  try {
    const response = await fetch('/api/lobby/reset-ready', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: authStore.user.user_id
      })
    })

    if (response.ok) {
      isReady.value = false
      localStorage.removeItem('playerJoinedGame')
    }
  } catch (error) {
  }
}

const handleGameResult = (data: any) => {
  if (isAdmin.value) return
  
  const isWinner = data.winner_id === authStore.user?.user_id
  emit('gameOver', isWinner ? 'win' : 'lose')
  
  resetReadyStatus()
}

const handleGameFinished = (winnerId: string) => {
  console.log('Game finished in Lobby, winner:', winnerId)
  if (isAdmin.value) return
  
  const isWinner = winnerId === authStore.user?.user_id
  emit('gameOver', isWinner ? 'win' : 'lose')
  
  resetReadyStatus()
}

const handleGameStarted = (data: any) => {
  console.log('Game started in Lobby:', data)
}

const checkUserStatus = async () => {
  try {
    const response = await fetch('/api/lobby/players')
    if (response.ok) {
      const data = await response.json()
      const currentUser = authStore.user?.user_id
      const userInLobby = data.players?.some((player: any) => 
        player.user_id === currentUser && player.is_active
      )
      if (!userInLobby && !(window as any).__appCurrentStateIsGame) {
        isInLobby.value = false
        isReady.value = false
        currentLobbyId.value = ''
        localStorage.removeItem('currentLobbyId')
        localStorage.removeItem('playerJoinedGame')
      }
    }
  } catch (error) {
  }
}

const checkRealLobbyStatus = async () => {
  try {
    const response = await fetch('/api/lobby/players')
    if (response.ok) {
      const data = await response.json()
      const currentUser = authStore.user?.user_id
      const userInLobby = data.players?.find((player: any) => 
        player.user_id === currentUser && player.is_active
      )
      
      if (userInLobby && userInLobby.lobby_id) {
        if (currentLobbyId.value !== userInLobby.lobby_id) {
          console.log('Updating currentLobbyId from server:', userInLobby.lobby_id)
          currentLobbyId.value = userInLobby.lobby_id
        }
        isInLobby.value = true
      } else {
        isInLobby.value = false
        isReady.value = false
        currentLobbyId.value = ''
        localStorage.removeItem('currentLobbyId')
        localStorage.removeItem('playerJoinedGame')
      }
    }
  } catch (error) {
  }
}

const checkRealReadyStatus = async () => {
  if (!authStore.isAuthenticated || !authStore.user) return
  
  try {
    const response = await fetch(`/api/lobby/ready?user_id=${authStore.user.user_id}`)
    if (response.ok) {
      const data = await response.json()
      isReady.value = data.is_ready
      if (isReady.value) {
        localStorage.setItem('playerJoinedGame', '1')
      } else {
        localStorage.removeItem('playerJoinedGame')
      }
    }
  } catch (error) {
  }
}

let refreshTimer: ReturnType<typeof setInterval> | null = null
let balanceTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  console.log('Lobby component mounted')
  
  socketService.onGameResult(handleGameResult)
  socketService.onGameFinished(handleGameFinished)
  socketService.onGameStarted(handleGameStarted)
  
  socketService.onTimerUpdate((time: number) => {
    console.log('Lobby timer update received in Lobby:', time)
    globalTimer.value = time
  })
  socketService.onGameTimerUpdate((data: any) => {
    console.log('Game timer update received in Lobby:', data)
  })
  
  await loadLobbyBank()
  await loadGameRounds()
  
  if (typeof props.selectedLobbyId !== 'undefined' && props.selectedLobbyId) {
    console.log('Connecting to selected lobby:', props.selectedLobbyId)
    if (isInLobby.value) {
      await leaveLobby()
    }
    if (isAdmin.value) {
      await joinSpecificLobby(props.selectedLobbyId)
    } else {
      await joinLobby(props.selectedLobbyId)
    }
  } else {
    const savedLobbyId = localStorage.getItem('currentLobbyId')
    if (savedLobbyId && authStore.isAuthenticated && authStore.user) {
      if (isAdmin.value) {
        await joinSpecificLobby(savedLobbyId)
      } else {
        await joinLobby(savedLobbyId)
      }
      localStorage.removeItem('currentLobbyId')
    }
  }
  
  await checkRealReadyStatus()
  
  if (isInLobby.value) {
    await loadLobbyPlayers()
  }
  
  refreshTimer = setInterval(async () => {
    if (isInLobby.value) {
      await loadLobbyPlayers()
    } else {
      await loadLobbyBank()
    }
    await loadGameRounds()
  }, 2000)

  balanceTimer = setInterval(async () => {
    if (authStore.isAuthenticated && authStore.user) {
      try {
        const userResp = await fetch(`/api/user?user_id=${authStore.user.user_id}`)
        if (userResp.ok) {
          const userData = await userResp.json()
          authStore.updateBalance(userData.balance)
          await loadBalance()
        }
      } catch (e) { }
    }
  }, 3000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (balanceTimer) clearInterval(balanceTimer)
})
</script>

<template>
  <div class="lobby">
    <div class="lobby-header">
      <h1>Waiting for players...</h1>
      
      <div class="lobby-bank">
        <span>Банк лобби: </span>
        <span class="coin-icon">🪙</span>
        <span class="bank-value">{{ lobbyBank }}</span>
      </div>
      
      <div v-if="globalTimer > 0" class="game-timer">
        <span>Таймер: </span>
        <span class="timer-value" :class="{ 'warning': globalTimer <= 5 }">
          {{ globalTimer }} сек
        </span>
      </div>
      
      <div v-if="isAdmin && currentLobbyId" class="admin-lobby-id">
        <b>Текущий lobby_id:</b> {{ currentLobbyId }}
      </div>
      
      <div class="lobby-status">
        <div v-if="isInLobby" class="status-connected">
          ✅ Подключен к лобби
        </div>
        <div v-else class="status-disconnected">
          ❌ Не подключен к лобби
        </div>
      </div>
      
      <div class="lobby-controls">
        <button 
          v-if="!isInLobby"
          @click="autoJoinLobby" 
          class="join-lobby-btn"
          :disabled="loading"
        >
          {{ loading ? 'Подключение...' : 'Подключиться к лобби' }}
        </button>
        <button 
          v-else
          @click="leaveLobby" 
          class="leave-lobby-btn"
          :disabled="loading"
        >
          {{ loading ? 'Отключение...' : 'Покинуть лобби' }}
        </button>
      </div>
      
      <button 
        v-if="!isAdmin && isInLobby"
        class="join-btn" 
        :class="{ disabled: isReady, joined: isReady }"
        :disabled="isReady"
        @click="joinGame"
      >
        {{ isReady ? 'Готов' : 'Присоединиться к игре' }}
      </button>
      
      <div v-if="isAdmin" class="admin-info">
        👑 Администратор - режим наблюдения
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
    
    <div v-if="isInLobby" class="lobby-players">
      <h3>Игроки в лобби ({{ filteredPlayers.length }})</h3>
      
      <div v-if="filteredPlayers.length === 0" class="no-players">
        Пока нет игроков
      </div>
      
      <div v-else class="players-grid">
        <div 
          v-for="player in filteredPlayers" 
          :key="player.user_id"
          class="player-card"
        >
          <div class="player-avatar">
            {{ player.nickname.charAt(0).toUpperCase() }}
          </div>
          <div class="player-info">
          <div class="player-name">
            {{ player.nickname }}
          </div>
            <div class="player-status">
              <template v-if="player.is_winner">🏆 Победил</template>
              <template v-else-if="player.is_eliminated">❌ Проиграл</template>
              <template v-else-if="player.is_observer">👁️ Наблюдает</template>
              <template v-else-if="player.is_in_game">🎮 Играет</template>
              <template v-else-if="player.is_ready">✅ Готов</template>
              <template v-else-if="player.is_joined">📝 Присоединился</template>
              <template v-else-if="player.is_active">🟢 Подключился</template>
              <template v-else>⚫ Неактивен</template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lobby {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
  width: 100%;
}

.lobby-header {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.lobby-header h1 {
  color: white;
  font-size: 2.2em;
  margin: 0 0 16px 0;
  font-weight: 600;
}

.lobby-bank {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #E6D55A;
  font-size: 1.2em;
  font-weight: 600;
  margin-bottom: 16px;
}

.coin-icon {
  font-size: 1.3em;
}

.bank-value {
  font-size: 1.2em;
  font-weight: 700;
}

.lobby-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #10B981;
  font-size: 1.2em;
  font-weight: 600;
  margin-bottom: 16px;
}

.game-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #10B981;
  font-size: 1.2em;
  font-weight: 600;
  margin-bottom: 16px;
}

.timer-value {
  color: #10B981;
  font-size: 1.3em;
  font-weight: 700;
}

.timer-value.warning {
  color: #EF4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.lobby-status {
  margin-bottom: 20px;
}

.status-connected {
  color: #10B981;
  font-weight: 600;
  font-size: 1.1em;
}

.status-disconnected {
  color: #EF4444;
  font-weight: 600;
  font-size: 1.1em;
}

.lobby-controls {
  margin-bottom: 20px;
}

.join-lobby-btn, .leave-lobby-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 10px;
}

.join-lobby-btn {
  background: #10B981;
  color: white;
}

.join-lobby-btn:hover {
  background: #059669;
}

.leave-lobby-btn {
  background: #EF4444;
  color: white;
}

.leave-lobby-btn:hover {
  background: #DC2626;
}

.join-btn {
  background: #10B981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 16px 32px;
  font-size: 1.2em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 20px;
  width: 100%;
}

.join-btn:hover {
  background: #059669;
  transform: translateY(-2px);
}

.join-btn.disabled {
  background: #666;
  cursor: not-allowed;
  transform: none;
}

.join-btn.joined {
  background: #4F46E5;
  cursor: default;
}

.join-btn.joined:hover {
  background: #4F46E5;
  transform: none;
}

.error-message {
  color: #EF4444;
  font-size: 0.9em;
  margin-top: 8px;
  text-align: center;
  padding: 10px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
}

.lobby-players {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
}

.lobby-players h3 {
  color: white;
  margin: 0 0 20px 0;
  text-align: center;
}

.no-players {
  color: #999;
  text-align: center;
  font-style: italic;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.player-card {
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
}

.player-card:hover {
  border-color: #10B981;
  transform: translateY(-2px);
}

.player-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #10B981;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2em;
  font-weight: 600;
  flex-shrink: 0;
}

.player-info {
  flex: 1;
}

.player-name {
  color: white;
  font-size: 0.9em;
  font-weight: 600;
  margin-bottom: 4px;
}

.player-status {
  color: #ccc;
  font-size: 0.8em;
  font-weight: 500;
}

.admin-info {
  color: #E6D55A;
  font-size: 1.1em;
  font-weight: 600;
  text-align: center;
  padding: 12px;
  background: rgba(230, 213, 90, 0.1);
  border-radius: 8px;
  margin: 10px 0;
}

.admin-lobby-id {
  color: #E6D55A;
  font-size: 0.9em;
  font-weight: 500;
  text-align: center;
  padding: 8px;
  background: rgba(230, 213, 90, 0.1);
  border-radius: 8px;
  margin-top: 10px;
}
</style>

export default {
  name: 'Lobby'
}