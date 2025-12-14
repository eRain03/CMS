<script setup>
import { ref, onMounted } from 'vue'

// 定义数据结构，包含 recent_activity
const stats = ref({
  total_users: 0,
  total_supply: 0,
  total_demand: 0,
  recent_activity: []
})
const loading = ref(true)

// 记得把 IP 换成你的 VPS 地址/域名
const API_BASE = 'http://43.248.188.75:38939'

onMounted(async () => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/admin/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) stats.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <header class="page-header">
      <h1 class="page-title">Dashboard Overview</h1>
      <p class="subtitle">Real-time snapshot of platform activity.</p>
    </header>

    <div class="stats-grid">
      <div class="stat-card blue">
        <div class="icon">👥</div>
        <div class="info">
          <h3>Total Users</h3>
          <div class="number">{{ stats.total_users }}</div>
        </div>
      </div>

      <div class="stat-card green">
        <div class="icon">🌾</div>
        <div class="info">
          <h3>Active Offers</h3>
          <div class="number">{{ stats.total_supply }}</div>
        </div>
      </div>

      <div class="stat-card red">
        <div class="icon">🏭</div>
        <div class="info">
          <h3>Active Demands</h3>
          <div class="number">{{ stats.total_demand }}</div>
        </div>
      </div>
    </div>

    <div class="recent-section">
      <div class="section-header">
        <h2>Recently Created Listings</h2>
        <span class="tag-new">Latest 5</span>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Race / Breed</th>
              <th>Quantity</th>
              <th>Location</th>
              <th>Owner</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="stats.recent_activity.length === 0">
              <td colspan="6" class="empty">No recent activity found.</td>
            </tr>

            <tr v-for="item in stats.recent_activity" :key="item.id">
              <td>
                <span class="badge" :class="item.type">
                  {{ item.type === 'supply' ? 'OFFER' : 'DEMAND' }}
                </span>
              </td>
              <td class="bold">{{ item.race }}</td>
              <td>{{ item.qty }}</td>
              <td class="location">📍 {{ item.location }}</td>
              <td>{{ item.owner }}</td>
              <td class="time">{{ new Date(item.timestamp * 1000).toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<style scoped>
.page-header { margin-bottom: 30px; }
.page-title { margin: 0; font-weight: 300; color: #333; font-size: 1.8rem; }
.subtitle { color: #888; font-size: 0.9rem; margin-top: 5px; }

/* --- Stats Grid --- */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 40px; }
.stat-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); display: flex; align-items: center; transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-3px); }

.stat-card .icon { font-size: 2.5rem; margin-right: 20px; opacity: 0.8; }
.stat-card h3 { margin: 0; font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.stat-card .number { font-size: 2.2rem; font-weight: 700; color: #2c3e50; line-height: 1.2; }

/* 颜色主题 */
.stat-card.blue { border-left: 5px solid #3498db; }
.stat-card.green { border-left: 5px solid #27ae60; }
.stat-card.red { border-left: 5px solid #c0392b; }

/* --- Recent Activity Table --- */
.recent-section { background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); padding: 25px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
.section-header h2 { margin: 0; font-size: 1.2rem; color: #2c3e50; }
.tag-new { background: #eef2f7; color: #3498db; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { text-align: left; padding: 12px; color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
td { padding: 15px 12px; border-bottom: 1px solid #f9f9f9; color: #333; vertical-align: middle; }
tr:last-child td { border-bottom: none; }

/* Table Elements */
.badge { padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; }
.badge.supply { background: #e8f5e9; color: #2e7d32; } /* 绿色 Offer */
.badge.demand { background: #ffebee; color: #c62828; } /* 红色 Demand */

.bold { font-weight: 600; color: #2c3e50; }
.location { color: #555; }
.time { color: #999; font-size: 0.85rem; }
.empty { text-align: center; padding: 30px; font-style: italic; color: #ccc; }
</style>