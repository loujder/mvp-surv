<script setup lang="ts">
interface Player {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  isEliminated?: boolean
  isDisconnected?: boolean
  isObserver?: boolean
  isWinner?: boolean
}

interface Props {
  players: Player[]
  title: string
  showDisconnected?: boolean
}

const props = defineProps<Props>()

const getStatusIcon = (player: Player) => {
  if (player.isDisconnected) return '🔴'
  if (player.isEliminated) return '❌'
  if (player.isObserver) return '👁️'
  return '🟢'
}

const getStatusText = (player: Player) => {
  if (player.isDisconnected) return 'Отключился'
  if (player.isEliminated) return 'Выбыл'
  if (player.isObserver) return 'Наблюдатель'
  return 'В игре'
}
</script>

<template>
  <div class="players-section">
    <h3>{{ title }}</h3>
    <div class="players-grid">
      <div 
        v-for="player in players" 
        :key="player.id"
        class="player-card"
        :class="{ 
          'current-user': player.isCurrentUser,
          'eliminated': player.isEliminated,
          'disconnected': player.isDisconnected,
          'observer': player.isObserver
        }"
      >
        <div class="player-avatar" :style="{ backgroundColor: player.color }">
          {{ player.avatar }}
        </div>
        <div class="player-info">
          <div class="player-name">
            {{ player.name }}
            <span v-if="player.isCurrentUser" class="current-user-badge">Вы</span>
          </div>
          <div class="player-status">
            <span class="status-icon">{{ getStatusIcon(player) }}</span>
            <span class="status-text">{{ getStatusText(player) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="players-status-summary">
      <div v-for="player in players" :key="player.id" class="player-status-summary-item">
        <span class="player-name">{{ player.name }}:</span>
        <span class="player-status-text">
          <template v-if="player.isObserver">Наблюдатель</template>
          <template v-else-if="player.isEliminated">Проигравший</template>
          <template v-else-if="player.isWinner">Победитель</template>
          <template v-else>Играет</template>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.players-section {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}

.players-section h3 {
  color: white;
  margin: 0 0 20px 0;
  text-align: center;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.player-card {
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
  position: relative;
}

.player-card:hover {
  border-color: #10B981;
  transform: translateY(-2px);
}

.player-card.current-user {
  border-color: #4F46E5;
  background: #1a1a2e;
}

.player-card.eliminated {
  opacity: 0.6;
  border-color: #EF4444;
}

.player-card.disconnected {
  opacity: 0.4;
  border-color: #F59E0B;
}

.player-card.observer {
  opacity: 0.7;
  border-color: #8B5CF6;
}

.player-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5em;
  font-weight: 600;
  margin: 0 auto 12px;
}

.player-info {
  text-align: center;
}

.player-name {
  color: #ccc;
  font-size: 0.9em;
  position: relative;
  margin-bottom: 8px;
}

.current-user-badge {
  background: #4F46E5;
  color: white;
  font-size: 0.7em;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}

.player-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 0.8em;
}

.status-icon {
  font-size: 1.2em;
}

.status-text {
  color: #ccc;
}

.players-status-summary {
  margin-top: 18px;
  padding-top: 10px;
  border-top: 1px solid #444;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.player-status-summary-item {
  display: flex;
  gap: 8px;
  color: #ccc;
  font-size: 1em;
}
.player-status-summary-item .player-name {
  font-weight: 600;
  color: #E6D55A;
}
.player-status-summary-item .player-status-text {
  font-weight: 500;
}
</style> 