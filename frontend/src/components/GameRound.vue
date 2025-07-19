<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { socketService, roundTimer, currentRoundNumber, totalRounds, eliminatedPlayers, playerStatuses } from '../services/socketService'

interface GamePlayer {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  isEliminated?: boolean
}

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

const props = defineProps<{
  gameSession: GameSession
  players: GamePlayer[]
}>()

const emit = defineEmits<{
  gameFinished: [winnerId: string]
}>()

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.user_id === 'Loujder')

const gamePlayers = computed(() => 
  (props.players || []).filter(player => player && player.name)
)

function getPlayerStatus(playerId: string) {
  const status = playerStatuses.value.find(s => s.user_id === playerId)
  return status ? status.status : 'unknown'
}

const updatedPlayers = computed(() => {
  return gamePlayers.value.map(player => ({
    ...player,
    isEliminated: getPlayerStatus(player.id) !== 'active',
    status: getPlayerStatus(player.id)
  }))
})

onMounted(() => {
  if (getPlayerStatus(authStore.user?.user_id) !== 'active') {
    emit('gameFinished', 'eliminated')
  }
})

onUnmounted(() => {
})

const formatTime = (seconds: number) => {
  return `${seconds}`
}
</script>

<template>
  <div class="game-round">
    <div style="color: red; font-size: 2em; text-align: center; margin-top: 40px;">
      ЕСЛИ ВЫ ВИДИТЕ ЭТОТ ТЕКСТ — GameRound МОНТИРУЕТСЯ!
    </div>
    <pre style="color: #fff; background: #222; padding: 8px; border-radius: 8px; margin-bottom: 10px;">
      {{ JSON.stringify(updatedPlayers, null, 2) }}
    </pre>
    <div class="round-header">
      <h2>🎮 ИГРА ИДЕТ</h2>
      <div class="round-info">
        <span class="round-number">Раунд {{ currentRoundNumber }} из {{ totalRounds }}</span>
      </div>
      <div class="round-timer">
        <span class="timer-label">Время раунда:</span>
        <span class="timer-value" :class="{ 'warning': roundTimer <= 5 }">
          {{ formatTime(roundTimer) }}
        </span>
        <span class="timer-label">секунд</span>
      </div>
    </div>
    <div class="players-section">
      <h3>Игроки в раунде ({{ updatedPlayers.filter(p => !p.isEliminated).length }})</h3>
      <div class="players-grid">
        <div v-for="player in updatedPlayers" :key="player.id" class="player-card" :class="{ 'eliminated': player.isEliminated }">
          <div class="player-avatar" :style="{ backgroundColor: player.color || '#10B981' }">
            {{ typeof player.name === 'string' && player.name.length > 0 ? player.name.charAt(0).toUpperCase() : '?' }}
          </div>
          <div class="player-info">
            <div class="player-name">
              {{ player.name || '??' }}
              <span v-if="player.isCurrentUser" class="current-user">(Вы)</span>
            </div>
            <div class="player-status">
              {{ player.isEliminated ? 'Выбыл' : 'В игре' }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="isAdmin" class="admin-info">
      <p>👑 Как администратор, вы можете наблюдать за игрой</p>
    </div>
  </div>
</template>

<style scoped>
.game-round {
  display: flex;
  flex-direction: column;
  gap: 30px;
  max-width: 800px;
  width: 100%;
  padding: 20px;
}

.round-header {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.round-header h2 {
  color: white;
  font-size: 2em;
  margin: 0 0 20px 0;
  font-weight: 600;
}

.round-info {
  margin-bottom: 20px;
}

.round-number {
  color: #10B981;
  font-size: 1.4em;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #10B981;
}

.round-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.timer-label {
  color: #ccc;
  font-size: 1.5em;
  font-weight: 500;
}

.timer-value {
  color: #10B981;
  font-size: 3em;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.timer-value.warning {
  color: #EF4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.players-section {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
}

.players-section h3 {
  color: white;
  font-size: 1.5em;
  margin: 0 0 20px 0;
  text-align: center;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.player-card {
  background: #3a3a3a;
  border: 1px solid #555;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.player-card.eliminated {
  opacity: 0.5;
  text-decoration: line-through;
}

.player-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.2em;
}

.player-info {
  flex: 1;
}

.player-name {
  color: white;
  font-weight: 600;
  font-size: 1.1em;
  margin-bottom: 4px;
}

.current-user {
  color: #10B981;
  font-weight: 700;
}

.player-status {
  color: #10B981;
  font-size: 0.9em;
  font-weight: 500;
}

.admin-info {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.admin-info p {
  color: #ccc;
  font-size: 1.1em;
  margin: 0;
}
</style>

export default {
  name: 'GameRound'
}