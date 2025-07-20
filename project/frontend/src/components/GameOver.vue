<script setup lang="ts">
import { ref, onUnmounted, computed, defineExpose, onMounted } from 'vue'
import { gamePlayers } from '../stores/gameStore'
import { playerBalance } from '../stores/playerStore'
import { gameResult } from '../services/socketService'
import { useAuthStore } from '../stores/authStore'

const props = defineProps<{ result: any }>()

const emit = defineEmits<{
  playAgain: []
  exit: []
}>()

const authStore = useAuthStore()
const exitCountdown = ref(2)
const showResults = ref(false)

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // GameOver component mounted
})

const playerStat = computed(() => {
  if (
    props.result &&
    typeof props.result === 'object' &&
    Array.isArray(props.result.player_statistics)
  ) {
    return props.result.player_statistics.find(
      (s: any) => s.chat_id === authStore.user?.chat_id
    )
  }
  return null
})

const coinsWon = computed(() => {
  return playerStat.value?.total_coins_earned ?? 0
})

const shouldShowGameOver = computed(() => {
  return (
    playerStat.value &&
    ['winner', 'active'].includes(playerStat.value.status) &&
    coinsWon.value > 0
  )
})

defineExpose({ shouldShowGameOver })

const resultsTable = computed(() => {
  if (gameResult.value && gameResult.value.players) {
    // Фильтруем администраторов из результатов
    const filteredPlayers = gameResult.value.players.filter((player: any) => !player.is_admin)
    return filteredPlayers.map((player: any, index: number) => ({
      id: player.chat_id,
      name: player.nickname,
      position: index + 1,
      isWinner: player.is_winner,
      isCurrentUser: player.chat_id === authStore.user?.chat_id
    }))
  }
  // Fallback к старой логике
  const players = [...gamePlayers.value].filter(player => !player.is_admin)
  return players.sort((a, b) => {
    if (a.isCurrentUser && !b.isCurrentUser) return -1
    if (!a.isCurrentUser && b.isCurrentUser) return 1
    return 0
  }).map((player, index) => ({
    ...player,
    position: index + 1,
    isWinner: index === 0
  }))
})

const canPlayAgain = computed(() => playerBalance.value >= 1)

const startExitCountdown = () => {
  timer = setInterval(() => {
    if (exitCountdown.value > 0) {
      exitCountdown.value--
    } else {
      emit('exit')
    }
  }, 1000)
}

const toggleResults = () => {
  showResults.value = !showResults.value
}

const playAgain = () => {
  emit('playAgain')
}

const exit = () => {
  emit('exit')
}

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<template>
  <div>
    <!-- Отладочная информация -->
    <div style="position: fixed; top: 50px; right: 10px; background: rgba(255,0,0,0.8); color: white; padding: 10px; border-radius: 5px; z-index: 9999; font-size: 12px;">
      <div>GameOver Debug:</div>
      <div>shouldShowGameOver: {{ shouldShowGameOver }}</div>
      <div>playerStat: {{ playerStat ? 'exists' : 'null' }}</div>
      <div>coinsWon: {{ coinsWon }}</div>
      <div>result: {{ result ? 'exists' : 'null' }}</div>
    </div>
    
    <!-- Временно убираю условие shouldShowGameOver для отладки -->
    <div class="gameover-modal">
      <div class="gameover-content">
        <h2 v-if="shouldShowGameOver">Победа!</h2>
        <h2 v-else>Игра окончена</h2>
        
        <div v-if="shouldShowGameOver" class="coins-won">
          +{{ coinsWon }} монет
        </div>
        <div v-else class="coins-won lose">
          Вы проиграли
        </div>
        
        <div class="gameover-actions">
          <button class="btn btn-primary" @click="playAgain" :disabled="!canPlayAgain">Сыграть ещё</button>
          <button class="btn btn-secondary" @click="exit">Выйти</button>
        </div>
        <div class="show-results">
          <button class="btn btn-link" @click="toggleResults">Показать результаты</button>
        </div>
        <div v-if="showResults" class="results-table">
          <table>
            <thead>
              <tr>
                <th>Игрок</th>
                <th>Статус</th>
                <th>Монеты</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stat in (gameResult?.player_statistics || [])" :key="stat.chat_id">
                <td>{{ stat.nickname }}</td>
                <td>{{ stat.status }}</td>
                <td>{{ stat.total_coins_earned }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gameover-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.gameover-content {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  min-width: 320px;
  text-align: center;
  box-shadow: 0 4px 32px rgba(0,0,0,0.2);
}
.coins-won {
  font-size: 2rem;
  color: #2ecc40;
  margin-bottom: 16px;
}
.coins-won.lose {
  color: #e74c3c;
}
.gameover-actions {
  margin-top: 24px;
  display: flex;
  gap: 16px;
  justify-content: center;
}
.show-results {
  margin-top: 16px;
}
.results-table {
  margin-top: 16px;
  text-align: left;
}
.results-table table {
  width: 100%;
  border-collapse: collapse;
}
.results-table th, .results-table td {
  padding: 4px 8px;
  border-bottom: 1px solid #eee;
}
</style>

export default {
  name: 'GameOver'
}