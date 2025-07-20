<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { socketService, roundTimer, currentRoundNumber, totalRounds } from '../services/socketService'

interface GamePlayer {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  is_admin?: boolean
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
  gameStarted: [gameSession: GameSession, players: GamePlayer[]]
}>()

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.is_admin || false)

const gamePlayers = computed(() => 
  props.players.filter(player => !player.is_admin)
)

onMounted(() => {
})

onUnmounted(() => {
})

const formatTime = (seconds: number) => {
  return `${seconds}`
}
</script>

<template>
  <div class="game-waiting">
    <div class="waiting-header">
      <h2>Игра начинается через</h2>
      <div class="round-info">
        <span class="round-number">Раунд {{ currentRoundNumber }} из {{ totalRounds }}</span>
      </div>
      <div class="waiting-timer">
        <span class="timer-value" :class="{ 'warning': roundTimer <= 5 }">
          {{ formatTime(roundTimer) }}
        </span>
        <span class="timer-label">секунд</span>
      </div>
    </div>
    <div class="players-section">
      <h3>Игроки в игре ({{ gamePlayers.length }})</h3>
      <div class="players-grid">
        <div v-for="player in gamePlayers" :key="player.id" class="player-card">
          <div class="player-avatar" :style="{ backgroundColor: player.color || '#10B981' }">
            {{ player.name ? player.name.charAt(0).toUpperCase() : '?' }}
          </div>
          <div class="player-info">
            <div class="player-name">
              {{ player.name }}
              <span v-if="player.isCurrentUser" class="current-user">(Вы)</span>
            </div>
            <div class="player-status">Готов к игре</div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="isAdmin" class="admin-info">
      <p>Как администратор, вы можете наблюдать за игрой</p>
    </div>
  </div>
</template>

<style scoped>
.game-waiting {
  display: flex;
  flex-direction: column;
  gap: 30px;
  max-width: 800px;
  width: 100%;
  padding: 20px;
}

.waiting-header {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.waiting-header h2 {
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

.waiting-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
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

.timer-label {
  color: #ccc;
  font-size: 1.5em;
  font-weight: 500;
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
  name: 'GameWaiting'
} 