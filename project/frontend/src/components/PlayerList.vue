<script setup lang="ts">
interface GamePlayer {
  id: string
  name: string
  color: string
  avatar: string
  isCurrentUser: boolean
  isEliminated?: boolean
}

defineProps<{
  players: GamePlayer[]
  showElimination?: boolean
}>()
</script>

<template>
  <div class="player-list">
    <div class="player-list-container">
      <div
        v-for="(player, index) in players"
        :key="player.id"
        class="player-item"
        :class="{ eliminated: player.isEliminated, current: player.isCurrentUser }"
      >
        <div class="player-number">
          #{{ index + 1 }}
        </div>
        <div 
          class="player-avatar"
          :style="{ backgroundColor: player.color }"
        >
          {{ player.avatar }}
        </div>
        <div class="player-name">
          {{ player.name }}{{ player.isCurrentUser ? ' (You)' : '' }}
        </div>
        <div v-if="showElimination && player.isEliminated" class="elimination-mark">
          ×
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-list {
  width: 100%;
}

.player-list-container {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #333;
  transition: all 0.2s;
}

.player-item:last-child {
  border-bottom: none;
}

.player-item.eliminated {
  opacity: 0.5;
}

.player-item.current {
  background: rgba(230, 213, 90, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin: 0 -12px;
}

.player-number {
  color: #E6D55A;
  font-size: 1.1em;
  font-weight: 600;
  min-width: 32px;
  text-align: left;
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
  flex-shrink: 0;
}

.player-name {
  flex: 1;
  color: white;
  font-size: 1.1em;
}

.elimination-mark {
  color: #999;
  font-size: 1.5em;
  font-weight: 600;
}
</style>