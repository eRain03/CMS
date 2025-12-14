<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const notifications = ref([])
const loading = ref(true)

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }

  try {
    const res = await fetch('http://43.248.188.75:38939/api/notifications', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    notifications.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="notif-page">
    <a href="#" @click.prevent="router.push('/')" class="back">← Home</a>
    <h2>My Notifications</h2>
    
    <div v-if="loading">Loading...</div>
    <div v-else-if="notifications.length === 0" class="empty">No notifications yet.</div>
    
    <div v-else class="list">
      <div v-for="(n, i) in notifications" :key="i" class="item">
        <div class="msg">{{ n.message }}</div>
        <div class="time">{{ new Date(n.timestamp * 1000).toLocaleString() }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notif-page { max-width: 600px; margin: 40px auto; padding: 20px; font-family: sans-serif; }
.item { padding: 15px; border-bottom: 1px solid #eee; background: white; margin-bottom: 10px; border-radius: 4px; }
.time { font-size: 0.8rem; color: #999; margin-top: 5px; }
.back { text-decoration: none; color: #666; display: block; margin-bottom: 20px; }
.empty { text-align: center; color: #999; margin-top: 50px; }
</style>