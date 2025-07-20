<script setup lang="ts">
const emit = defineEmits<{
  observe: []
  exit: []
}>()
</script>

<template>
  <div class="eliminated-modal">
    <div class="eliminated-content">
      <h2>Вы выбили из игры!</h2>
      <p>Вы можете остаться наблюдателем или выйти в главное меню.</p>
      <div class="eliminated-actions">
        <button class="btn btn-secondary" @click="emit('observe')">Наблюдать</button>
        <button class="btn btn-danger" @click="emit('exit')">Выйти</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.eliminated-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.eliminated-content {
  background: #232323;
  color: #fff;
  padding: 32px 40px;
  border-radius: 16px;
  box-shadow: 0 4px 32px #000a;
  text-align: center;
  min-width: 320px;
}
.eliminated-actions {
  margin-top: 32px;
  display: flex;
  gap: 24px;
  justify-content: center;
}
.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-secondary {
  background: #4F46E5;
  color: #fff;
}
.btn-secondary:hover {
  background: #3730A3;
}
.btn-danger {
  background: #DC2626;
  color: #fff;
}
.btn-danger:hover {
  background: #991B1B;
}
</style> 