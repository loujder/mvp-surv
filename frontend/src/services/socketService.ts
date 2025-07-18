import { io, Socket } from 'socket.io-client'
import { ref } from 'vue'

export const globalTimer = ref(10)
export const gameFinished = ref(false)
export const gameWinner = ref<string | null>(null)
export const gameTimer = ref(10)
export const gameTimerRunning = ref(false)
export const gameResult = ref<any>(null)

export const roundTimer = ref(15)
export const choiceTimer = ref(10)
export const choicePhaseActive = ref(false)
export const choicePhaseData = ref<any>(null)

export const eliminatedPlayers = ref<string[]>([])
export const currentRoundNumber = ref(1)
export const totalRounds = ref(1)
export const playerStatuses = ref<any[]>([])

let socket: Socket | null = null
let isConnected = false

const onGameFinishedCallbacks: Array<(winnerId: string) => void> = []
const onTimerUpdateCallbacks: Array<(time: number) => void> = []
const onGameTimerStartCallbacks: Array<(data: any) => void> = []
const onGameTimerUpdateCallbacks: Array<(data: any) => void> = []
const onGameResultCallbacks: Array<(data: any) => void> = []
const onGameStartedCallbacks: Array<(data: any) => void> = []
const onConnectCallbacks: Array<() => void> = []
const onChoicePhaseStartedCallbacks: Array<(data: any) => void> = []
const onChoiceTimerStartCallbacks: Array<(data: any) => void> = []
const onChoiceTimerUpdateCallbacks: Array<(data: any) => void> = []
const onPlayersEliminatedCallbacks: Array<(data: any) => void> = []
const onRoundUpdatedCallbacks: Array<(data: any) => void> = []
const onPlayerStatusUpdateCallbacks: Array<(data: any) => void> = []

export const socketService = {
  connect() {
    if (socket && isConnected) return
    socket = io('http://localhost:5000', { transports: ['websocket'] })
    socket.on('connect', () => {
      isConnected = true
      onConnectCallbacks.forEach(cb => cb())
    })
    socket.on('disconnect', () => {
      isConnected = false
    })
    socket.on('connect_error', (error) => {
    })
    socket.on('timer_update', (data) => {
      globalTimer.value = data.time
      onTimerUpdateCallbacks.forEach(callback => callback(data.time))
    })
    socket.on('game_timer_start', (data) => {
      roundTimer.value = data.time
      gameTimer.value = data.time
      gameTimerRunning.value = true
      choicePhaseActive.value = false
      onGameTimerStartCallbacks.forEach(callback => callback(data))
    })
    socket.on('game_timer_update', (data) => {
      roundTimer.value = data.time
      gameTimer.value = data.time
      gameTimerRunning.value = data.time > 0
      onGameTimerUpdateCallbacks.forEach(callback => callback(data))
    })
    socket.on('choice_phase_started', (data) => {
      choicePhaseActive.value = true
      choicePhaseData.value = data
      gameTimerRunning.value = false
      onChoicePhaseStartedCallbacks.forEach(callback => callback(data))
    })
    socket.on('choice_timer_start', (data) => {
      choiceTimer.value = data.time
      choicePhaseActive.value = true
      onChoiceTimerStartCallbacks.forEach(callback => callback(data))
    })
    socket.on('choice_timer_update', (data) => {
      choiceTimer.value = data.time
      onChoiceTimerUpdateCallbacks.forEach(callback => callback(data))
    })
    socket.on('players_eliminated', (data) => {
      eliminatedPlayers.value = data.eliminated_players || []
      onPlayersEliminatedCallbacks.forEach(callback => callback(data))
    })
    socket.on('round_updated', (data) => {
      currentRoundNumber.value = data.current_round || 1
      totalRounds.value = data.total_rounds || 1
      onRoundUpdatedCallbacks.forEach(callback => callback(data))
    })
    socket.on('game_started', (data) => {
      choicePhaseActive.value = false
      eliminatedPlayers.value = []
      currentRoundNumber.value = 1
      if (data.game_session) {
        totalRounds.value = data.game_session.total_rounds || 1
      }
      onGameStartedCallbacks.forEach(callback => callback(data))
    })
    socket.on('game_result', (data) => {
      gameResult.value = data
      gameFinished.value = true
      gameWinner.value = data.winner_id
      choicePhaseActive.value = false
      gameTimerRunning.value = false
      onGameResultCallbacks.forEach(callback => callback(data))
      onGameFinishedCallbacks.forEach(callback => callback(data.winner_id))
    })
    socket.on('game_finished', (data) => {
      gameFinished.value = true
      gameWinner.value = data.winner_id
      choicePhaseActive.value = false
      gameTimerRunning.value = false
      onGameFinishedCallbacks.forEach(callback => callback(data.winner_id))
    })
    socket.on('lobby_update', (data) => {
    })
    socket.on('admin_lobby_update', (data) => {
    })
    socket.on('player_status_update', (data) => {
      playerStatuses.value = data.statuses || []
      onPlayerStatusUpdateCallbacks.forEach(callback => callback(data))
    })
    socket.on('error', (error) => {
    })
  },
  disconnect() {
    if (socket) {
      socket.disconnect()
      socket = null
      isConnected = false
    }
  },
  emit(event: string, data?: any) {
    if (socket && isConnected) {
      socket.emit(event, data)
    }
  },
  onGameFinished(callback: (winnerId: string) => void) {
    onGameFinishedCallbacks.push(callback)
  },
  onTimerUpdate(callback: (time: number) => void) {
    onTimerUpdateCallbacks.push(callback)
  },
  onGameTimerStart(callback: (data: any) => void) {
    onGameTimerStartCallbacks.push(callback)
  },
  onGameTimerUpdate(callback: (data: any) => void) {
    onGameTimerUpdateCallbacks.push(callback)
  },
  onGameResult(callback: (data: any) => void) {
    onGameResultCallbacks.push(callback)
  },
  onGameStarted(callback: (data: any) => void) {
    onGameStartedCallbacks.push(callback)
  },
  onConnect(callback: () => void) {
    onConnectCallbacks.push(callback)
  },
  onChoicePhaseStarted(callback: (data: any) => void) {
    onChoicePhaseStartedCallbacks.push(callback)
  },
  onChoiceTimerStart(callback: (data: any) => void) {
    onChoiceTimerStartCallbacks.push(callback)
  },
  onChoiceTimerUpdate(callback: (data: any) => void) {
    onChoiceTimerUpdateCallbacks.push(callback)
  },
  onPlayersEliminated(callback: (data: any) => void) {
    onPlayersEliminatedCallbacks.push(callback)
  },
  onRoundUpdated(callback: (data: any) => void) {
    onRoundUpdatedCallbacks.push(callback)
  },
  onPlayerStatusUpdate(callback: (data: any) => void) {
    onPlayerStatusUpdateCallbacks.push(callback)
  },
  get isConnected() {
    return isConnected
  }
} 