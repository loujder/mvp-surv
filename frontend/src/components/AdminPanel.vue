<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

interface Lobby {
  lobby_id: string
  player_count: number
  status: string
}

const lobbies = ref<Lobby[]>([])
const loading = ref(false)
const error = ref('')
const creating = ref(false)
const newLobbyId = ref('')
let socket: Socket | null = null

const emit = defineEmits<{
  switchToLobby: [lobbyId: string]
}>()

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'waiting': 'Ожидание',
    'playing': 'Игра идет',
    'finished': 'Завершено'
  }
  return statusMap[status] || status
}

const generateLobbyId = () => {
  return 'lobby-' + Math.random().toString(36).substring(2, 8)
}

const setupSocket = () => {
  socket = io('http://localhost:5000', { transports: ['websocket'] })

  socket.on('connect', () => {
  })

  socket.on('admin_lobby_update', (data) => {
    lobbies.value = data.lobbies || []
    lobbies.value.forEach(async (lobby) => {
      try {
        const gameStatusResponse = await fetch(`http://localhost:5000/api/game/status?lobby_id=${lobby.lobby_id}`)
        if (gameStatusResponse.ok) {
          const gameData = await gameStatusResponse.json()
          lobby.status = gameData.status || 'waiting'
        }
      } catch (err) {
      }
    })
  })

  socket.on('game_result', (data) => {
    loadLobbies()
  })

  socket.on('game_finished', (data) => {
    loadLobbies()
  })
}

const cleanupSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

const loadLobbies = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch('http://localhost:5000/api/admin/lobbies')
    if (response.ok) {
      const data = await response.json()
      lobbies.value = data.lobbies
      for (const lobby of lobbies.value) {
        try {
          const gameStatusResponse = await fetch(`http://localhost:5000/api/game/status?lobby_id=${lobby.lobby_id}`)
          if (gameStatusResponse.ok) {
            const gameData = await gameStatusResponse.json()
            lobby.status = gameData.status || 'waiting'
          }
        } catch (err) {
        }
      }
    } else {
      error.value = 'Ошибка загрузки лобби'
    }
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  } finally {
    loading.value = false
  }
}

const createLobby = async () => {
  if (!newLobbyId.value) {
    error.value = 'Введите ID лобби'
    return
  }
  creating.value = true
  error.value = ''
  try {
    const response = await fetch('http://localhost:5000/api/admin/lobby/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ admin_id: 'Loujder', lobby_id: newLobbyId.value })
    })
    if (response.ok) {
      newLobbyId.value = ''
      await loadLobbies()
    } else {
      const data = await response.json()
      error.value = data.error || 'Ошибка создания лобби'
    }
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  } finally {
    creating.value = false
  }
}

const startGame = async (lobbyId: string) => {
  try {
    const response = await fetch(`http://localhost:5000/api/admin/lobby/${lobbyId}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      await loadLobbies()
    } else {
      error.value = 'Ошибка запуска игры'
    }
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  }
}

const deleteLobby = async (lobbyId: string) => {
  if (!confirm('Вы уверены, что хотите удалить это лобби?')) {
    return
  }

  try {
    const response = await fetch(`http://localhost:5000/api/admin/lobby/${lobbyId}/delete`, {
      method: 'DELETE'
    })

    if (response.ok) {
      await loadLobbies()
    } else {
      error.value = 'Ошибка удаления лобби'
    }
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  }
}

const viewLobby = async (lobbyId: string) => {
  try {
    emit('switchToLobby', lobbyId)
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  }
}

const viewAllPlayers = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/admin/lobby/players')
    if (response.ok) {
      const data = await response.json()
      alert(`Всего игроков: ${data.count}\nИгроки: ${data.players.map((p: any) => p.nickname).join(', ')}`)
    } else {
      error.value = 'Ошибка загрузки списка игроков'
    }
  } catch (err) {
    error.value = 'Ошибка подключения к серверу'
  }
}

onMounted(() => {
  loadLobbies()
  newLobbyId.value = generateLobbyId()
  setupSocket()
})

onUnmounted(() => {
  cleanupSocket()
})
</script>

<template>
  <div class="admin-panel">
    <div class="admin-header">
      <h1>Панель администратора</h1>
      <div class="admin-actions">
        <button @click="loadLobbies" class="refresh-btn" :disabled="loading">
          {{ loading ? 'Обновление...' : 'Обновить' }}
        </button>
        <button @click="viewAllPlayers" class="view-players-btn">
          Показать всех игроков
        </button>
      </div>
    </div>

    <div class="create-lobby-section">
      <input v-model="newLobbyId" placeholder="ID лобби" class="lobby-id-input" />
      <button @click="createLobby" :disabled="creating || !newLobbyId" class="btn-create">
        {{ creating ? 'Создание...' : 'Создать лобби' }}
      </button>
      <button @click="newLobbyId = generateLobbyId()" class="btn-generate">Случайный ID</button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="lobbies-list">
      <h2>Список лобби ({{ lobbies.length }})</h2>

      <div v-if="lobbies.length === 0" class="no-lobbies">
        <p>Нет активных лобби</p>
      </div>

      <div v-else class="lobby-cards">
        <div
          v-for="lobby in lobbies"
          :key="lobby.lobby_id"
          class="lobby-card"
        >
          <div class="lobby-info">
            <h3>Лобби {{ lobby.lobby_id }}</h3>
            <div class="lobby-stats">
              <p>Игроков: {{ lobby.player_count }}</p>
              <p>Статус:
                <span class="status-badge" :class="lobby.status">
                  {{ getStatusText(lobby.status) }}
                </span>
              </p>
            </div>
          </div>

          <div class="lobby-actions">
            <button
              v-if="lobby.status === 'waiting'"
              @click="startGame(lobby.lobby_id)"
              class="btn-start"
              :disabled="lobby.player_count === 0"
            >
              Запустить игру
            </button>

            <button
              @click="viewLobby(lobby.lobby_id)"
              class="btn-view"
            >
              Посмотреть лобби
            </button>

            <button
              @click="deleteLobby(lobby.lobby_id)"
              class="btn-delete"
            >
              Удалить лобби
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1000px;
  width: 100%;
}

.admin-header {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.admin-header h1 {
  color: white;
  font-size: 2.2em;
  margin: 0;
  font-weight: 600;
}

.refresh-btn {
  background: #10B981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #059669;
}

.refresh-btn:disabled {
  background: #666;
  cursor: not-allowed;
}

.view-players-btn {
  background: #8B5CF6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-players-btn:hover {
  background: #7C3AED;
}

.error-message {
  color: #EF4444;
  font-size: 0.9em;
  padding: 10px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  text-align: center;
}

.lobbies-list {
  background: #2a2a2a;
  border: 2px solid #555;
  border-radius: 12px;
  padding: 24px;
}

.lobbies-list h2 {
  color: white;
  margin: 0 0 20px 0;
  font-size: 1.5em;
}

.no-lobbies {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 40px;
}

.lobby-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.lobby-card {
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s;
}

.lobby-card:hover {
  border-color: #10B981;
  transform: translateY(-2px);
}

.lobby-info h3 {
  color: white;
  margin: 0 0 12px 0;
  font-size: 1.2em;
}

.lobby-stats {
  margin-bottom: 16px;
}

.lobby-stats p {
  color: #ccc;
  margin: 4px 0;
  font-size: 0.9em;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: 600;
}

.status-badge.waiting {
  background: #F59E0B;
  color: white;
}

.status-badge.playing {
  background: #10B981;
  color: white;
}

.status-badge.finished {
  background: #6B7280;
  color: white;
}

.lobby-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-start, .btn-view, .btn-delete {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-start {
  background: #10B981;
  color: white;
}

.btn-start:hover:not(:disabled) {
  background: #059669;
}

.btn-start:disabled {
  background: #666;
  cursor: not-allowed;
}

.btn-view {
  background: #4F46E5;
  color: white;
}

.btn-view:hover {
  background: #4338CA;
}

.btn-delete {
  background: #EF4444;
  color: white;
}

.btn-delete:hover {
  background: #DC2626;
}

.create-lobby-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: center;
}
.lobby-id-input {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #555;
  font-size: 1em;
  width: 180px;
}
.btn-create {
  background: #10B981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-create:disabled {
  background: #666;
  cursor: not-allowed;
}
.btn-generate {
  background: #4F46E5;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-generate:hover {
  background: #4338CA;
}
</style> 

export default {
  name: 'AdminPanel'
} 