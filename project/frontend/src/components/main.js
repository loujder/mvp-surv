import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import axios from 'axios'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
axios.get('/api/data')
  .then(response => {
    console.log(response.data);
  })
const initApp = async () => {
  try {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      const user = JSON.parse(storedUser)
      const response = await axios.get(`/api/user?user_id=${user.user_id}`)
      if (response.data) {
        app.mount('#app')
      } else {
        localStorage.removeItem('user')
        app.mount('#app')
      }
    } else {
      app.mount('#app')
    }
  } catch (error) {
    console.error('Initialization error:', error)
    app.mount('#app')
  }
}
initApp()