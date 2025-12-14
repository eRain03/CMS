<script setup>
import { ref, onMounted, computed } from 'vue'

const activeTab = ref('supply') // 'supply' | 'demand'
const listings = ref({ supply: [], demand: [] })
const loading = ref(true)
const API_BASE = 'http://43.248.188.75:38939' // 记得确认你的 IP

// 加载数据
const loadData = async () => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/admin/listings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) listings.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 删除供需
const deleteItem = async (id, type) => {
  if(!confirm('Are you sure you want to delete this listing? This action cannot be undone.')) return

  const token = localStorage.getItem('token')
  // type 参数对应后端: 'supply' 或 'demand' (API中是 /listing/supply/xxx)
  // 注意：这里的 type 变量是 'supply' 或 'demand'
  const endpointType = type // 保持一致

  try {
    const res = await fetch(`${API_BASE}/api/admin/listing/${endpointType}/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (res.ok) {
      // 前端移除
      listings.value[type] = listings.value[type].filter(item => item.id !== id)
      alert('Listing deleted.')
    } else {
      alert('Failed to delete.')
    }
  } catch (e) {
    alert('Error: ' + e.message)
  }
}

// 辅助：格式化 Buyer 区域
const formatTargets = (targets) => {
  if (!targets) return '-'
  return targets.map(t => `${t.state}`).join(', ')
}

onMounted(loadData)
</script>

<template>
  <div class="admin-page">
    <h1 class="page-title">Listings Management</h1>

    <div class="tabs">
      <button
        :class="{ active: activeTab === 'supply' }"
        @click="activeTab = 'supply'"
      >
        🌾 Supply ({{ listings.supply.length }})
      </button>
      <button
        :class="{ active: activeTab === 'demand' }"
        @click="activeTab = 'demand'"
      >
        🏭 Demand ({{ listings.demand.length }})
      </button>
    </div>

    <div class="table-container">

      <table v-if="activeTab === 'supply'">
        <thead>
          <tr>
            <th>Date</th>
            <th>Owner</th>
            <th>Details (Race/Qty)</th>
            <th>Location</th>
            <th>Contact</th>
            <th class="action-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in listings.supply" :key="item.id">
            <td class="date-cell">{{ new Date(item.timestamp * 1000).toLocaleDateString() }}</td>
            <td>{{ item.owner_id || 'Unknown' }}</td>
            <td>
              <div class="bold">{{ item.race }}</div>
              <div class="sub">{{ item.quantity }} head · {{ item.sex }}</div>
            </td>
            <td>{{ item.city }}, {{ item.state }}</td>
            <td>{{ item.contact }}</td>
            <td>
              <button class="btn-del" @click="deleteItem(item.id, 'supply')">Remove</button>
            </td>
          </tr>
          <tr v-if="listings.supply.length === 0">
            <td colspan="6" class="empty">No active supply listings.</td>
          </tr>
        </tbody>
      </table>

      <table v-if="activeTab === 'demand'">
        <thead>
          <tr>
            <th>Date</th>
            <th>Owner</th>
            <th>Requirements</th>
            <th>Target Regions</th>
            <th>Contact</th>
            <th class="action-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in listings.demand" :key="item.id">
            <td class="date-cell">{{ new Date(item.timestamp * 1000).toLocaleDateString() }}</td>
            <td>{{ item.owner_id || 'Unknown' }}</td>
            <td>
              <div class="bold">{{ item.race }}</div>
              <div class="sub">Qty: {{ item.quantity }}+</div>
            </td>
            <td>{{ formatTargets(item.targets) }}</td>
            <td>{{ item.contact }}</td>
            <td>
              <button class="btn-del" @click="deleteItem(item.id, 'demand')">Remove</button>
            </td>
          </tr>
          <tr v-if="listings.demand.length === 0">
            <td colspan="6" class="empty">No active demand requests.</td>
          </tr>
        </tbody>
      </table>

    </div>
  </div>
</template>

<style scoped>
.page-title { margin-bottom: 20px; font-weight: 300; color: #333; }

/* Tabs */
.tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.tabs button {
  padding: 10px 20px; border: none; background: #e0e0e0;
  border-radius: 6px; cursor: pointer; color: #666; font-weight: 500;
  transition: all 0.2s;
}
.tabs button.active { background: #2c3e50; color: white; }

/* Table */
.table-container { background: white; padding: 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { background: #f8f9fa; color: #888; font-size: 0.8rem; text-transform: uppercase; text-align: left; padding: 15px; border-bottom: 2px solid #eee; }
td { padding: 15px; border-bottom: 1px solid #eee; vertical-align: middle; color: #333; }
tr:last-child td { border-bottom: none; }
tr:hover { background-color: #fafafa; }

/* Cell Styles */
.date-cell { color: #999; font-size: 0.85rem; white-space: nowrap; }
.bold { font-weight: 600; color: #2c3e50; }
.sub { font-size: 0.8rem; color: #888; margin-top: 2px; }
.empty { text-align: center; padding: 40px; color: #aaa; font-style: italic; }

/* Actions */
.action-col { text-align: right; }
.btn-del {
  background: #ffebee; color: #c62828; border: 1px solid #ffcdd2;
  padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; font-weight: 500;
  transition: all 0.2s;
}
.btn-del:hover { background: #c62828; color: white; border-color: #c62828; }

/* 确保表格容器支持滚动 */
.table-container {
  background: white;
  padding: 0;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);

  /* 👇 关键：允许横向滚动 */
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; /* iOS 惯性滚动 */
}

/* 稍微缩小一点手机上的字体 */
@media (max-width: 768px) {
  table { font-size: 0.8rem; }
  th, td { padding: 10px 8px; } /* 减少内边距 */
  .btn-action { padding: 4px 6px; font-size: 0.7rem; }
}
</style>