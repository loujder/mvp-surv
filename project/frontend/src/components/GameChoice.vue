<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { socketService, choiceTimer, choicePhaseData, currentRoundNumber, totalRounds, playerStatuses } from '../services/socketService'

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
  choiceMade: [choice: 'stay' | 'leave']
}>()

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.is_admin || false)

const playerChoice = ref<'stay' | 'leave' | null>(null)
const choiceSubmitted = ref(false)

const gamePlayers = computed(() => 
  props.players.filter(player => !player.is_admin)
)

function getPlayerStatus(playerId: string) {
  const status = playerStatuses.value.find(s => s.chat_id === playerId)
  return status ? status.status : 'unknown'
}

const isCurrentUserActive = computed(() => {
  if (!authStore.user) return false
  return getPlayerStatus(authStore.user.chat_id) === 'active'
})

const isCurrentUserEliminated = computed(() => {
  if (!authStore.user) return false
  return getPlayerStatus(authStore.user.chat_id) === 'eliminated'
})

onMounted(() => {
})

onUnmounted(() => {
})

const formatTime = (seconds: number) => {
  return `${seconds}`
}

const makeChoice = async (choice: 'stay' | 'leave') => {
  if (choiceSubmitted.value || isAdmin.value) return

  try {
    playerChoice.value = choice
    choiceSubmitted.value = true

    const response = await fetch('/api/game/choice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: authStore.user?.chat_id,
        game_session_id: props.gameSession.id,
        round_number: currentRoundNumber.value,
        choice: choice
      })
    })

    if (response.ok) {
      emit('choiceMade', choice)
    } else {
      choiceSubmitted.value = false
      playerChoice.value = null
    }
  } catch (error) {
    choiceSubmitted.value = false
    playerChoice.value = null
  }
}
</script>

<template>
  <div class="game-choice">
    <div style="color: red; font-size: 2em; text-align: center; margin-top: 40px;">
      ЕСЛИ ВЫ ВИДИТЕ ЭТОТ ТЕКСТ — GameChoice МОНТИРУЕТСЯ!
    </div>
    <div class="choice-header">
      <h2>🎯 ФАЗА ВЫБОРА</h2>
      <div class="round-info">
        <span class="round-number">Раунд {{ currentRoundNumber }} из {{ totalRounds }}</span>
      </div>
      <div class="choice-timer">
        <span class="timer-label">Время на выбор:</span>
        <span class="timer-value" :class="{ 'warning': choiceTimer <= 5 }">
          {{ formatTime(choiceTimer) }}
        </span>
        <span class="timer-label">секунд</span>
      </div>
    </div>
    
    <div v-if="!isAdmin && !isCurrentUserEliminated" class="choice-section">
      <h3>Выберите действие:</h3>
      <div class="choice-buttons">
        <button 
          @click="makeChoice('stay')" 
          :disabled="choiceSubmitted || !isCurrentUserActive || playerChoice === 'leave'"
          :class="{ 
            'choice-btn': true, 
            'stay-btn': true, 
            'selected': playerChoice === 'stay',
            'disabled': choiceSubmitted && playerChoice !== 'stay'
          }"
        >
          <span class="choice-icon">🎮</span>
          <span class="choice-text">Продолжить игру</span>
        </button>
        
        <button 
          @click="makeChoice('leave')" 
          :disabled="choiceSubmitted || !isCurrentUserActive || playerChoice === 'stay'"
          :class="{ 
            'choice-btn': true, 
            'leave-btn': true, 
            'selected': playerChoice === 'leave',
            'disabled': choiceSubmitted && playerChoice !== 'leave'
          }"
        >
          <span class="choice-icon">🚪</span>
          <span class="choice-text">Выйти из игры</span>
        </button>
      </div>
      
      <div v-if="choiceSubmitted" class="choice-status">
        <p v-if="playerChoice === 'stay'" class="status-stay">
          ✅ Вы выбрали продолжить игру
        </p>
        <p v-else-if="playerChoice === 'leave'" class="status-leave">
          🚪 Вы выбрали выйти из игры
        </p>
      </div>
    </div>
    
    <div v-if="!isAdmin && isCurrentUserEliminated" class="eliminated-section">
      <div class="eliminated-message">
        <div class="message-icon">💔</div>
        <h3>Вы выбыли из игры</h3>
        <p>К сожалению, вы больше не можете участвовать в голосовании</p>
      </div>
    </div>
    
    <div v-if="isAdmin" class="admin-info">
      <h3>👑 Администратор</h3>
      <p>Вы наблюдаете за фазой выбора игроков</p>
    </div>
    
    <div class="players-section">
      <h3>Игроки в фазе выбора ({{ gamePlayers.length }})</h3>
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
            <div class="player-status">
              {{ player.isCurrentUser && choiceSubmitted ? 
                (playerChoice === 'stay' ? 'Продолжает' : 'Выходит') : 
                'Выбирает...' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-choice {
  display: flex;
  flex-direction: column;
  gap: 30px;
  max-width: 800px;
  width: 100%;
  padding: 20px;
}

.choice-header {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.choice-header h2 {
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

.choice-timer {
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

.choice-section {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.choice-section h3 {
  color: white;
  font-size: 1.8em;
  margin: 0 0 30px 0;
}

.choice-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 30px;
}

.choice-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 25px 40px;
  border: 3px solid #555;
  border-radius: 12px;
  background: #3a3a3a;
  color: white;
  font-size: 1.2em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 200px;
}

.choice-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.stay-btn {
  border-color: #10B981;
}

.stay-btn:hover:not(.disabled) {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10B981;
}

.leave-btn {
  border-color: #EF4444;
}

.leave-btn:hover:not(.disabled) {
  background: rgba(239, 68, 68, 0.1);
  border-color: #EF4444;
}

.choice-btn.selected {
  transform: scale(1.05);
}

.stay-btn.selected {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10B981;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.leave-btn.selected {
  background: rgba(239, 68, 68, 0.2);
  border-color: #EF4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

.choice-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.choice-icon {
  font-size: 2em;
}

.choice-text {
  font-size: 1.1em;
}

.choice-status {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
  font-size: 1.2em;
  font-weight: 600;
}

.status-stay {
  color: #10B981;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid #10B981;
}

.status-leave {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #EF4444;
}

.admin-info {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.admin-info h3 {
  color: #F59E0B;
  font-size: 1.8em;
  margin: 0 0 15px 0;
}

.admin-info p {
  color: #ccc;
  font-size: 1.2em;
}

.eliminated-section {
  background: #2a2a2a;
  border: 2px solid #EF4444;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
}

.eliminated-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.eliminated-message .message-icon {
  font-size: 3em;
}

.eliminated-message h3 {
  color: #EF4444;
  font-size: 1.8em;
  margin: 0;
}

.eliminated-message p {
  color: #ccc;
  font-size: 1.2em;
  margin: 0;
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
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1.2em;
}

.player-info {
  flex: 1;
}

.player-name {
  color: white;
  font-weight: 600;
  margin-bottom: 5px;
}

.current-user {
  color: #10B981;
  font-size: 0.9em;
}

.player-status {
  color: #ccc;
  font-size: 0.9em;
}
</style> 