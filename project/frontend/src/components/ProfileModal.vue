<script setup lang="ts">
import { playerBalance, playerColor, playerAvatar } from '../stores/playerStore'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()
const emit = defineEmits<{
  close: [],
  logout: []
}>()

const closeModal = () => {
  emit('close')
}

const handleLogout = () => {
  emit('logout')
}
</script>

<template>
  <div class="profile-modal" @click="closeModal">
    <div class="modal-content" @click.stop>
      <button class="close-btn" @click="closeModal">×</button>
      
      <div class="profile-header">
        <div class="avatar" :style="{ backgroundColor: playerColor }">
          {{ playerAvatar }}
        </div>
        <h2>{{ authStore.user?.nickname || 'Player' }}</h2>
        <p class="user-id">Chat ID: {{ authStore.user?.chat_id || 'N/A' }}</p>
      </div>
      
      <div class="profile-stats">
        <div class="stat-item">
          <span class="stat-label">Баланс:</span>
          <div class="balance">
            <span class="coin-icon">🪙</span>
            {{ playerBalance }}
          </div>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">Игр сыграно:</span>
          <span class="stat-value">0</span>
        </div>
        
        <div class="stat-item">
          <span class="stat-label">Побед:</span>
          <span class="stat-value">0</span>
        </div>
      </div>

      <button class="logout-btn" @click="handleLogout">Выйти из аккаунта</button>
    </div>
  </div>
</template>

<style scoped>
.profile-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 16px;
  padding: 32px;
  max-width: 400px;
  width: 90%;
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

.profile-header {
  text-align: center;
  margin-bottom: 24px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 2em;
  margin: 0 auto 12px;
}

.profile-header h2 {
  color: white;
  font-size: 1.5em;
  margin: 0 0 5px 0;
  font-weight: 600;
}

.user-id {
  color: #888;
  font-size: 0.9em;
  margin: 0;
}

.profile-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #444;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #ccc;
  font-size: 1.1em;
}

.stat-value {
  color: white;
  font-size: 1.1em;
  font-weight: 500;
}

.balance {
  color: #E6D55A;
  font-size: 1.1em;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.coin-icon {
  font-size: 1.2em;
}

.logout-btn {
  width: 100%;
  padding: 14px;
  background: #EF4444;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1.1em;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: #DC2626;
}
</style>