<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import ProfileModal from './components/ProfileModal.vue'
import Lobby from './components/Lobby.vue'
import GameWaiting from './components/GameWaiting.vue'
import GameRound from './components/GameRound.vue'
import GameChoice from './components/GameChoice.vue'
import EliminatedPlayer from './components/EliminatedPlayer.vue'
import AdminPanel from './components/AdminPanel.vue'
import Leaderboard from './components/Leaderboard.vue'
import GameOver from './components/GameOver.vue'
import AuthView from './components/Auth.vue'

import { deductCoin, canJoinGame, addCoins, loadBalance } from './stores/playerStore'
import { addPlayerToGame, isPlayerInGame, resetGame } from './stores/gameStore'
import { useAuthStore } from './stores/authStore'
import { socketService, globalTimer, gameFinished, gameWinner, gameResult, choicePhaseActive } from './services/socketService'

type GameState = 'auth' | 'lobby' | 'waiting' | 'game' | 'choice' | 'eliminated' | 'admin' | 'leaderboard' | 'gameover' | 'observer'

interface GameSession {
  id: number
  lobby_id: string
  status: string
  current_round: number
  total_rounds: number
  started_at: string
  finished_at?: string
  winner_id?: string
}

interface GamePlayer {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  isEliminated?: boolean
}

const authStore = useAuthStore()
const currentState = ref<GameState>('auth')
const showProfile = ref(false)
const gameResultState = ref<'win' | 'lose' | null>(null)
const playerJoinedGame = ref(false)

watch(playerJoinedGame, (val) => {
  localStorage.setItem('playerJoinedGame', val ? '1' : '0')
})

if (localStorage.getItem('playerJoinedGame')) {
  playerJoinedGame.value = localStorage.getItem('playerJoinedGame') === '1'
}
const isLoading = ref(true)

const currentGameSession = ref<GameSession | null>(null)
const gamePlayers = ref<GamePlayer[]>([])

const isPlayerInLobby = ref(false)

const isAdmin = computed(() => authStore.user?.user_id === 'Loujder')

const selectedLobbyId = ref<string | null>(null)

async function syncGameState() {
  let lobbyId = null;
  try {
    const resp = await fetch('/api/lobby/players');
    if (resp.ok) {
      const data = await resp.json();
      const currentUser = authStore.user?.user_id;
      const userLobby = data.players?.find((p: any) => p.user_id === currentUser && p.is_active);
      if (userLobby) lobbyId = userLobby.lobby_id;
    }
  } catch (e) { }
  if (!lobbyId) return;
  try {
    const playerStatusResp = await fetch(`/api/game/player-status?user_id=${authStore.user?.user_id}&lobby_id=${lobbyId}`);
    if (playerStatusResp.ok) {
      const playerStatus = await playerStatusResp.json();
      if (playerStatus.status === 'eliminated') {
        currentState.value = 'eliminated';
        return;
      }
    }
  } catch (e) { }
  try {
    const statusResp = await fetch(`/api/game/status?lobby_id=${lobbyId}`);
    if (!statusResp.ok) return;
    const gameStatus = await statusResp.json();
    if (gameStatus.status === 'playing') {
      currentGameSession.value = gameStatus;
      currentState.value = 'waiting';
    } else if (gameStatus.status === 'finished') {
      currentGameSession.value = gameStatus;
      currentState.value = 'gameover';
    } else {
      currentState.value = 'lobby';
    }
  } catch (e) { }
}

onMounted(async () => {
  socketService.connect()
  socketService.onConnect(async () => {
    await syncGameState();
  });
  socketService.onGameStarted((data: any) => {
    if (currentState.value === 'eliminated') return;
    currentGameSession.value = data.game_session
    gamePlayers.value = data.players || []
    switchState('waiting')
  })
  socketService.onGameResult(async (data: any) => {
    let playerStatus = getCurrentPlayerStatus()
    if (!playerStatus && authStore.user?.user_id && currentGameSession.value) {
      try {
        const resp = await fetch(`/api/game/player-status?user_id=${authStore.user.user_id}&lobby_id=${currentGameSession.value.lobby_id}`)
        if (resp.ok) {
          const statusData = await resp.json()
          playerStatus = statusData.status
        }
      } catch { }
    }
    if (playerStatus !== 'active' && playerStatus !== 'winner') return;
    const isWinner = data.winner_id === authStore.user?.user_id
    gameResultState.value = isWinner ? 'win' : 'lose'
    switchState('gameover')
  })
  socketService.onGameFinished((winnerId: string) => {
    if (currentState.value === 'eliminated') return;
    const isWinner = winnerId === authStore.user?.user_id
    gameResultState.value = isWinner ? 'win' : 'lose'
    switchState('gameover')
  })
  socketService.onGameTimerStart((data: any) => {
    if (currentState.value === 'eliminated') return;
    switchState('game')
  })
  socketService.onChoicePhaseStarted(async (data: any) => {
    let playerStatus = getCurrentPlayerStatus()
    if (!playerStatus && authStore.user?.user_id && currentGameSession.value) {
      try {
        const resp = await fetch(`/api/game/player-status?user_id=${authStore.user.user_id}&lobby_id=${currentGameSession.value.lobby_id}`)
        if (resp.ok) {
          const statusData = await resp.json()
          playerStatus = statusData.status
        }
      } catch { }
    }
    if (currentState.value === 'eliminated' || playerStatus !== 'active') return;
    switchState('choice')
  })
  socketService.onChoiceTimerStart((data: any) => {
    if (currentState.value === 'eliminated' || getCurrentPlayerStatus() !== 'active') return;
    if (currentState.value !== 'choice') {
      switchState('choice')
    }
  })
  socketService.onPlayersEliminated((data: any) => {
    const currentUserId = authStore.user?.user_id
    if (currentUserId && data.eliminated_players && data.eliminated_players.includes(currentUserId)) {
      switchState('eliminated')
    }
    if (data.eliminated_players && data.eliminated_players.length > 0) {
      gamePlayers.value = gamePlayers.value.filter(player => 
        !data.eliminated_players.includes(player.id)
      )
    }
  })
  socketService.onRoundUpdated((data: any) => {
    if (currentGameSession.value) {
      currentGameSession.value.current_round = data.current_round
      currentGameSession.value.total_rounds = data.total_rounds
    }
  })
  socketService.onPlayerStatusUpdate((data: any) => {
    const currentUserId = authStore.user?.user_id
    if (currentUserId && data.statuses) {
      const currentUserStatus = data.statuses.find((s: any) => s.user_id === currentUserId)
      if (currentUserStatus && currentUserStatus.status === 'eliminated') {
        switchState('eliminated')
      }
    }
  })
  try {
    if (localStorage.getItem('user')) {
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
      if (storedUser.user_id) {
        await authStore.fetchUserData(storedUser.user_id)
        if (authStore.isAuthenticated) {
          await loadBalance()
          currentState.value = 'lobby'
          await checkLobbyStatus()
        }
      }
    }
  } catch (error) {
  } finally {
    isLoading.value = false
  }
})

const checkLobbyStatus = async () => {
  try {
    const response = await fetch('/api/lobby/players')
    if (response.ok) {
      const data = await response.json()
      const currentUser = authStore.user?.user_id
      const isInLobby = data.players?.some((player: any) => 
        player.user_id === currentUser && player.is_active
      )
      isPlayerInLobby.value = isInLobby
    }
  } catch (error) {
  }
}

watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) {
    currentState.value = 'lobby'
    checkLobbyStatus()
  } else {
    currentState.value = 'auth'
  }
})

const switchState = (state: GameState) => {
  currentState.value = state
  if (typeof window !== 'undefined') {
    (window as any).__appCurrentStateIsGame = (state === 'game')
  }
  if (state === 'game') {
    showProfile.value = false
  }
  if (state === 'lobby') {
    resetGame()
    gameResultState.value = null
    currentGameSession.value = null
    gamePlayers.value = []
    checkLobbyStatus()
  }
}

const toggleProfile = () => {
  showProfile.value = !showProfile.value
}

const joinGame = async () => {
  if (canJoinGame.value && authStore.isAuthenticated) {
    const success = await deductCoin()
    if (success) {
      const added = addPlayerToGame()
      if (added) {
        playerJoinedGame.value = true
      } else {
        await addCoins(1)
      }
    }
  } else if (!authStore.isAuthenticated) {
    switchState('auth')
  }
}

const handleGameEnd = async () => {
  if (gameResultState.value === 'win') {
    const success = await addCoins(2)
  }
  if (authStore.isAuthenticated && authStore.user) {
    try {
      const userResp = await fetch(`/api/user?user_id=${authStore.user.user_id}`)
      if (userResp.ok) {
        const userData = await userResp.json()
        authStore.updateBalance(userData.balance)
        await loadBalance()
      }
    } catch (e) {
    }
  }
}

const handleGameStarted = (gameSession?: GameSession, players?: GamePlayer[]) => {
  if (gameSession) {
    currentGameSession.value = gameSession
  }
  if (players) {
    gamePlayers.value = players
  }
  switchState('game')
}

const handleGameFinished = (winnerId: string) => {
  const isWinner = winnerId === authStore.user?.user_id
  gameResultState.value = isWinner ? 'win' : 'lose'
  currentState.value = 'gameover'
}

const handlePlayAgain = async () => {
  if (authStore.isAuthenticated && authStore.user && authStore.user.user_id !== 'Loujder') {
    try {
      await fetch('/api/lobby/unready', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: authStore.user.user_id
        })
      })
      const userResp = await fetch(`/api/user?user_id=${authStore.user.user_id}`)
      if (userResp.ok) {
        const userData = await userResp.json()
        authStore.updateBalance(userData.balance)
        await loadBalance()
      }
    } catch (err) {
    }
  }
  playerJoinedGame.value = false
  if (canJoinGame.value && authStore.isAuthenticated) {
    switchState('lobby')
    setTimeout(async () => {
      await joinGame()
    }, 100)
  } else {
    switchState('lobby')
  }
}

const handleExit = async () => {
  if (authStore.isAuthenticated && authStore.user && authStore.user.user_id !== 'Loujder') {
    try {
      await fetch('/api/lobby/unready', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: authStore.user.user_id })
      })
      await fetch('/api/lobby/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: authStore.user.user_id })
      })
      const userResp = await fetch(`/api/user?user_id=${authStore.user.user_id}`)
      if (userResp.ok) {
        const userData = await userResp.json()
        authStore.updateBalance(userData.balance)
      }
    } catch (e) {
    }
  }
}

const handleGameOver = (result: 'win' | 'lose') => {
  gameResultState.value = result
  playerJoinedGame.value = false
  if (isAdmin.value) {
    switchState('admin')
  } else {
    switchState('gameover')
  }
}

const showNavigation = computed(() => {
  return authStore.isAuthenticated && 
         currentState.value !== 'auth' &&
         !isLoading.value
})

const handleAuthSuccess = async () => {
  await loadBalance()
  switchState('lobby')
}

const logout = () => {
  authStore.logout()
  switchState('auth')
}

const switchToAdmin = () => {
  if (isAdmin.value) {
    switchState('admin')
  }
}

const handleChoiceMade = (choice: 'stay' | 'leave') => {
  console.log('Player made choice:', choice)
}

const handleExitGame = () => {
  console.log('Player chose to exit game')
  playerJoinedGame.value = false
  localStorage.removeItem('playerJoinedGame')
  switchState('lobby')
}

const handleSpectateGame = () => {
  console.log('Player chose to spectate game')
}

const handleSwitchToLobby = (lobbyId?: string) => {
  if (lobbyId) {
    selectedLobbyId.value = lobbyId
  }
  switchState('lobby')
  setTimeout(() => {
    selectedLobbyId.value = null
  }, 3000)
}

function handleObserve() {
  currentState.value = 'observer'
}

const handleExitEliminated = async () => {
  if (authStore.isAuthenticated && authStore.user) {
    try {
      await fetch('/api/lobby/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: authStore.user.user_id })
      })
      playerJoinedGame.value = false
      currentGameSession.value = null
      gamePlayers.value = []
      localStorage.removeItem('playerJoinedGame')
      localStorage.removeItem('currentLobbyId')
      socketService.disconnect && socketService.disconnect()
      currentState.value = 'lobby'
    } catch (e) {
      isPlayerInLobby.value = false
      playerJoinedGame.value = false
      currentGameSession.value = null
      gamePlayers.value = []
      localStorage.removeItem('playerJoinedGame')
      localStorage.removeItem('currentLobbyId')
      socketService.disconnect && socketService.disconnect()
      currentState.value = 'lobby'
    }
  }
}

function getCurrentPlayerStatus() {
  if (!authStore.user?.user_id || !gameResultState.value) return null;
  const stat = gameResultState.value.player_statistics?.find((s: any) => s.user_id === authStore.user.user_id)
  return stat ? stat.status : null;
}

watch(currentState, (val) => {
  if (val === 'gameover' && getCurrentPlayerStatus() && !['winner', 'active'].includes(getCurrentPlayerStatus())) {
    switchState('lobby')
  }
})


</script>

<template>
  <!-- Экран загрузки -->
  <div v-if="isLoading" class="loading-screen">
    <div class="loader"></div>
    <p>Загрузка...</p>
  </div>
  
  <div v-else id="app">

    <!-- Profile Modal -->
    <ProfileModal 
      v-if="showProfile && authStore.isAuthenticated" 
      @close="showProfile = false"
      @logout="logout"
      :user="authStore.user"
    />

    <!-- Game States -->
    <div class="game-container">
      <!-- Состояние аутентификации -->
      <AuthView 
        v-if="currentState === 'auth' || !authStore.isAuthenticated"
        @auth-success="handleAuthSuccess"
      />
      <!-- Игровые состояния (только для аутентифицированных) -->
      <template v-if="authStore.isAuthenticated">
        <Lobby 
          v-if="currentState === 'lobby'" 
          :player-joined-game="playerJoinedGame"
          :selected-lobby-id="selectedLobbyId"
          @game-over="handleGameOver" 
          @start-game="switchState('game')"
        />
        <GameWaiting
          v-if="currentState === 'waiting'"
          :game-session="currentGameSession || { id: 1, lobby_id: 'default', status: 'playing', current_round: 1, total_rounds: 1, started_at: new Date().toISOString() }"
          :players="gamePlayers"
          @game-started="handleGameStarted"
        />
        <GameRound 
          v-if="currentState === 'game'"
          :game-session="currentGameSession || { id: 1, lobby_id: 'default', status: 'playing', current_round: 1, total_rounds: 1, started_at: new Date().toISOString() }"
          :players="gamePlayers"
          @game-finished="handleGameFinished"
        />
        <GameChoice 
          v-if="currentState === 'choice'"
          :game-session="currentGameSession || { id: 1, lobby_id: 'default', status: 'playing', current_round: 1, total_rounds: 1, started_at: new Date().toISOString() }"
          :players="gamePlayers"
          @choice-made="handleChoiceMade"
        />
        <EliminatedPlayer 
          v-if="currentState === 'eliminated'"
          :game-session="currentGameSession || { id: 1, lobby_id: 'default', status: 'playing', current_round: 1, total_rounds: 1, started_at: new Date().toISOString() }"
          :players="gamePlayers"
          @observe="handleObserve" 
          @exit="handleExitEliminated" 
        />
        <AdminPanel v-if="currentState === 'admin'" @switch-to-lobby="handleSwitchToLobby" />
        <Leaderboard v-if="currentState === 'leaderboard'" @close="switchState('gameover')" />
        <GameOver 
          v-if="currentState === 'gameover'" 
          :result="gameResultState"
          @play-again="handlePlayAgain" 
          @exit="handleExit" 
        />
      </template>
      <div v-if="currentState === 'observer'">
        <h2 style="text-align:center;margin-top:40px;">Вы наблюдаете за игрой</h2>
        <GameRound v-if="currentGameSession && gamePlayers" :gameSession="currentGameSession" :players="gamePlayers" />
        <!-- Можно добавить другие компоненты для наблюдения -->
        <button class="btn btn-danger" style="margin: 32px auto; display: block;" @click="handleExitEliminated">Выйти в меню</button>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-nav" v-if="showNavigation">
      <button @click="switchState('lobby')" :class="{ active: currentState === 'lobby' }">
        Lobby
      </button>
      <button 
        v-if="isAdmin"
        @click="switchToAdmin" 
        :class="{ active: currentState === 'admin' }"
      >
        Admin
      </button>
      <button @click="toggleProfile" :class="{ active: showProfile }">
        Profile
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Стили для экрана загрузки */
.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #1a1a1a;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loader {
  border: 5px solid #333;
  border-top: 5px solid #10B981;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-screen p {
  color: #ddd;
  font-size: 1.2em;
}

/* Остальные стили */
.bottom-nav {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 20px;
  z-index: 1000;
}

.bottom-nav button {
  padding: 12px 24px;
  border: 2px solid #555;
  background: #2a2a2a;
  color: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.1em;
  font-weight: 500;
  min-width: 100px;
}

.bottom-nav button:hover {
  background: #3a3a3a;
  transform: translateY(-2px);
}

.bottom-nav button.active {
  background: #646cff;
  border-color: #646cff;
}

.game-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

export default {
  components: {
    ProfileModal,
    Lobby,
    GameRound,
    AdminPanel,
    Leaderboard,
    GameOver,
    AuthView
  }
}