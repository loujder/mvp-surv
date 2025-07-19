<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  close: []
}>()

const rankings = ref([])

const closeLeaderboard = () => {
  emit('close')
}
</script>

<template>
  <div class="leaderboard">
    <div class="leaderboard-container">
      <button class="close-btn" @click="closeLeaderboard">×</button>
      
      <div class="rankings">
        <div
          v-for="player in rankings"
          :key="player.rank"
          class="ranking-item"
        >
          <div class="rank-number" :class="{ winner: player.isWinner }">
            #{{ player.rank }}
          </div>
          <div class="player-avatar" :style="{ backgroundColor: player.color }">
            {{ player.name.charAt(0).toUpperCase() }}
          </div>
          <div class="player-name">
            {{ player.name }}{{ player.isCurrentUser ? ' (You)' : '' }}
          </div>
          <div v-if="player.isWinner" class="trophy">🏆</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.leaderboard-container {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 20px;
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.rankings {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
}

.rank-number {
  font-size: 1.2em;
  font-weight: 600;
  color: #888;
  min-width: 40px;
}

.rank-number.winner {
  color: #E6D55A;
}

.player-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.2em;
}

.player-name {
  flex: 1;
  color: white;
  font-size: 1.1em;
}

.trophy {
  font-size: 1.5em;
}
</style>

export default {
  name: 'Leaderboard'
}