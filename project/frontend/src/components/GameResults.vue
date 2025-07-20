<script setup lang="ts">
import { computed } from 'vue'
interface GameResult {
  winner_id: string
  winner_name: string
  bank?: number
  players: Array<{
    chat_id: string
    nickname: string
    is_winner: boolean
    position: number
    is_admin: boolean
  }>
}

interface Props {
  gameResult: GameResult
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  playAgain: []
  exit: []
}>()

const playAgain = () => {
  emit('playAgain')
}

const exit = () => {
  emit('exit')
}

const filteredPlayers = computed(() => 
  props.gameResult.players.filter(player => !player.is_admin)
)
</script>

<template>
  <div v-if="show" class="game-results">
    <div class="results-container">
      <h1>Игра окончена!</h1>
      
      <!-- Победитель -->
      <div class="winner-section">
        <div class="winner-avatar">
          🏆
        </div>
        <h2 class="winner-name">{{ gameResult.winner_name }}</h2>
        <p class="winner-text">Победитель игры!</p>
        <p class="bank-info">Банк игры: {{ gameResult.bank || filteredPlayers.length }} монет</p>
      </div>
      
      <!-- Результаты всех игроков -->
      <div class="results-section">
        <h3>Результаты игры</h3>
        <div class="results-list">
          <div
            v-for="player in filteredPlayers"
            :key="player.chat_id"
            class="result-item"
            :class="{ winner: player.is_winner }"
          >
            <div class="position">
              {{ player.position === 1 ? '🥇' : player.position === 2 ? '🥈' : player.position === 3 ? '🥉' : `#${player.position}` }}
            </div>
            <div class="player-name">
              {{ player.nickname }}
            </div>
            <div v-if="player.is_winner" class="winner-badge">
              Победитель
            </div>
          </div>
        </div>
      </div>
      
      <!-- Кнопки действий -->
      <div class="action-buttons">
        <button @click="playAgain" class="btn btn-primary">
          Играть снова
        </button>
        <button @click="exit" class="btn btn-secondary">
          Выйти
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-results {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.results-container {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  max-width: 600px;
  width: 90%;
}

h1 {
  color: white;
  font-size: 2.5em;
  margin: 0 0 32px 0;
  font-weight: 600;
}

.winner-section {
  margin-bottom: 40px;
}

.winner-avatar {
  font-size: 4em;
  margin-bottom: 16px;
}

.winner-name {
  color: #10B981;
  font-size: 2em;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.winner-text {
  color: #ccc;
  font-size: 1.2em;
  margin: 0;
}

.bank-info {
  color: #10B981;
  font-size: 1.1em;
  font-weight: 600;
  margin: 8px 0 0 0;
}

.results-section {
  margin-bottom: 40px;
}

.results-section h3 {
  color: white;
  font-size: 1.5em;
  margin: 0 0 24px 0;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  display: flex;
  align-items: center;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.result-item.winner {
  border-color: #10B981;
  background: #1a1a2e;
}

.position {
  font-size: 1.5em;
  margin-right: 16px;
  min-width: 40px;
}

.player-name {
  color: #ccc;
  font-size: 1.1em;
  flex: 1;
  text-align: left;
}

.winner-badge {
  background: #10B981;
  color: white;
  font-size: 0.8em;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.btn {
  padding: 14px 28px;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #10B981;
  color: white;
}

.btn-primary:hover {
  background: #059669;
}

.btn-secondary {
  background: #6B7280;
  color: white;
}

.btn-secondary:hover {
  background: #4B5563;
}
</style> 