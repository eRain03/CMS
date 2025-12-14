<script setup>
import { ref, onMounted, nextTick } from 'vue'

const logs = ref([])
const loading = ref(true)
const logContainer = ref(null)
const API_BASE = 'http://43.248.188.75:38939'

const fetchLogs = async () => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/admin/logs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    logs.value = data.logs
    // 自动滚动到底部
    nextTick(() => {
      if(logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
    })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const clearLogs = async () => {
  if(!confirm("Clear all system logs?")) return
  const token = localStorage.getItem('token')
  await fetch(`${API_BASE}/api/admin/logs`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  })
  fetchLogs()
}

onMounted(fetchLogs)
</script>

<template>
  <div class="admin-page">
    <div class="header">
      <h1 class="page-title">System Error Logs</h1>
      <div>
        <button class="btn refresh" @click="fetchLogs">Refresh</button>
        <button class="btn clear" @click="clearLogs">Clear Logs</button>
      </div>
    </div>

    <div class="terminal-window" ref="logContainer">
      <div v-if="logs.length === 0" class="empty">No logs available.</div>
      <div v-for="(line, i) in logs" :key="i" class="log-line">
        {{ line }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { margin: 0; font-weight: 300; color: #333; }

.btn { padding: 8px 16px; border: 1px solid #ddd; background: white; cursor: pointer; border-radius: 4px; margin-left: 10px; }
.btn:hover { background: #f0f0f0; }
.btn.clear { color: #c0392b; border-color: #c0392b; }
.btn.clear:hover { background: #c0392b; color: white; }

.terminal-window {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
  padding: 20px;
  border-radius: 8px;
  height: 500px;
  overflow-y: auto;
  white-space: pre-wrap; /* 保留换行 */
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.log-line { border-bottom: 1px solid #333; padding: 2px 0; }
.log-line:last-child { border-bottom: none; }
</style>