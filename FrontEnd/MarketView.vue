<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const listings = ref([]) // 只存 Supply (牛源)
const loading = ref(true)
const API_BASE = 'http://43.248.188.75:38939'

// 筛选状态
const filters = reactive({
  state: '',
  race: ''
})

// 报价弹窗状态
const showOfferModal = ref(false)
const targetItem = ref(null)
const offerForm = reactive({
  price: null,
  price_per_unit: null,  // Price per arroba (@) for live weight
  message: '',
  loading_date: '',
  conditions: ''
})
const sendingOffer = ref(false)

// 基础数据 (用于筛选下拉框)
const states = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
const breeds = ["Nelore", "Angus", "Brahman", "Hereford", "Wagyu", "Other"] // 简化版，实际可用 API 获取

// 1. 加载市场数据
const loadMarket = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/market`)
    const data = await res.json()
    // 市场只展示 Supply (Farmer 卖的牛)
    // 且后端已经过滤了只显示 OPEN 的
    listings.value = data.supply
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 2. 计算属性：前端筛选
const filteredListings = computed(() => {
  return listings.value.filter(item => {
    const matchState = !filters.state || item.state === filters.state
    const matchRace = !filters.race || (item.race && item.race.includes(filters.race))
    return matchState && matchRace
  })
})

// 3. 打开报价弹窗
const openOfferModal = (item) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (!token) {
    if(confirm('Please login to make an offer.')) router.push('/login')
    return
  }

  // 🚫 阻止 Farmer 购买
  if (role === 'farmer') {
    alert('⚠️ Access Denied: Farmers cannot make offers on other cattle.\nPlease login as a Slaughterhouse/Buyer.')
    return
  }

  targetItem.value = item
  offerForm.price = null
  offerForm.price_per_unit = null
  offerForm.message = `I am interested in your ${item.quantity}x ${item.race}.`
  offerForm.loading_date = ''
  offerForm.conditions = ''
  showOfferModal.value = true
}

// 4. 提交报价 (Call Backend API)
const submitOffer = async () => {
  if (!offerForm.price) return alert('Please enter a price.')
  
  sendingOffer.value = true
  const token = localStorage.getItem('token')

  try {
    const payload = {
      supply_id: targetItem.value.id,
      price_offer: parseFloat(offerForm.price),
      price_per_unit: offerForm.price_per_unit ? parseFloat(offerForm.price_per_unit) : null,
      message: offerForm.message,
      loading_date: offerForm.loading_date || null,
      conditions: offerForm.conditions || null
    }

    const res = await fetch(`${API_BASE}/api/proposals`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      alert('✅ Offer Sent! The farmer will be notified.')
      showOfferModal.value = false
      router.push('/') // 跳转回 Dashboard 查看状态
    } else {
      const err = await res.json()
      alert('Error: ' + err.detail)
    }
  } catch (e) {
    alert('Network Error')
  } finally {
    sendingOffer.value = false
  }
}

// 辅助：图片处理
const getPhotoUrl = (filename) => {
  if (!filename) return 'https://via.placeholder.com/400x300?text=No+Photo'
  return `${API_BASE}/api/files/${filename}`
}

onMounted(loadMarket)
</script>

<template>
  <div class="market-page">
    <nav class="navbar">
      <div class="brand" @click="router.push('/')">CATTLE MATCH <span class="sub">Marketplace</span></div>
      <div class="actions">
        <button class="btn-dash" @click="router.push('/')">Go to Dashboard</button>
      </div>
    </nav>

    <div class="market-container">

      <aside class="filters">
        <h3>🔍 Filter Cattle</h3>

        <div class="filter-group">
          <label>State</label>
          <select v-model="filters.state">
            <option value="">All States</option>
            <option v-for="s in states" :key="s">{{ s }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Breed</label>
          <select v-model="filters.race">
            <option value="">All Breeds</option>
            <option v-for="b in breeds" :key="b">{{ b }}</option>
          </select>
        </div>

        <div class="results-count">
          Found: <strong>{{ filteredListings.length }}</strong> lots
        </div>
      </aside>

      <main class="listings-area">
        <div v-if="loading" class="loading">Loading Market Data...</div>

        <div v-else-if="filteredListings.length === 0" class="empty-state">
          No cattle found matching your criteria.
        </div>

        <div v-else class="grid">
          <div v-for="item in filteredListings" :key="item.id" class="card">

            <div class="card-img" :style="{ backgroundImage: `url(${getPhotoUrl(item.cattle_photo)})` }">
              <span class="qty-badge">{{ item.quantity }} Head</span>
            </div>

            <div class="card-body">
              <div class="header">
                <span class="race">{{ item.race }}</span>
                <span class="sex">{{ item.sex }}</span>
              </div>

              <div class="details">
                <p>📍 {{ item.city }}, {{ item.state }}</p>
                <p>⚖️ Age: {{ item.age }}mo</p>
                <p class="seller">User: {{ item.owner_id }}</p>
              </div>

              <button class="btn-offer" @click="openOfferModal(item)">
                💰 Make Offer
              </button>
            </div>
          </div>
        </div>
      </main>

    </div>

    <div v-if="showOfferModal" class="modal-overlay" @click="showOfferModal = false">
      <div class="modal-card" @click.stop>
        <h3>Make an Offer</h3>
        <p class="subtitle">Negotiate directly with the farmer.</p>

        <div class="item-summary" v-if="targetItem">
          <strong>{{ targetItem.quantity }}x {{ targetItem.race }}</strong>
          <br>
          <small>in {{ targetItem.city }}, {{ targetItem.state }}</small>
        </div>

        <form @submit.prevent="submitOffer">
          <div class="form-group">
            <label>Your Price Offer (Total R$)</label>
            <input
              type="number"
              v-model="offerForm.price"
              placeholder="e.g. 50000.00"
              required
              step="0.01"
            />
          </div>

          <div class="form-group" v-if="targetItem?.weight_type === 'live'">
            <label>Price per Arroba (@) - Optional</label>
            <input
              type="number"
              v-model.number="offerForm.price_per_unit"
              placeholder="e.g. 300.00"
              step="0.01"
            />
            <small class="hint">For live weight transactions. If not provided, will be calculated.</small>
          </div>

          <div class="form-group">
            <label>Loading Date</label>
            <input
              type="date"
              v-model="offerForm.loading_date"
            />
          </div>

          <div class="form-group">
            <label>Specific Conditions</label>
            <textarea v-model="offerForm.conditions" rows="2" placeholder="Any specific conditions or requirements..."></textarea>
          </div>

          <div class="form-group">
            <label>Message (Optional)</label>
            <textarea v-model="offerForm.message" rows="3" placeholder="I can pick them up next week..."></textarea>
          </div>

          <button type="submit" class="btn-submit" :disabled="sendingOffer">
            {{ sendingOffer ? 'Sending...' : 'Send Proposal' }}
          </button>
        </form>
        
        <button class="btn-cancel" @click="showOfferModal = false">Cancel</button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 布局 */
.market-page { min-height: 100vh; background: #f4f6f8; font-family: -apple-system, sans-serif; }
.navbar { background: white; padding: 0 40px; height: 60px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100; }
.brand { font-weight: 700; color: #2c3e50; font-size: 1.2rem; cursor: pointer; }
.brand .sub { font-weight: 400; color: #888; font-size: 0.9rem; margin-left: 5px; }
.btn-dash { border: 1px solid #2c3e50; background: transparent; color: #2c3e50; padding: 6px 15px; border-radius: 6px; cursor: pointer; font-weight: 500; }
.btn-dash:hover { background: #2c3e50; color: white; }

.market-container { max-width: 1200px; margin: 30px auto; display: flex; gap: 30px; padding: 0 20px; }

/* 侧边栏 */
.filters { width: 250px; flex-shrink: 0; background: white; padding: 20px; border-radius: 8px; height: fit-content; border: 1px solid #eee; }
.filters h3 { margin-top: 0; color: #333; font-size: 1rem; margin-bottom: 20px; }
.filter-group { margin-bottom: 20px; }
.filter-group label { display: block; font-size: 0.8rem; color: #777; margin-bottom: 5px; font-weight: 600; }
.filter-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.results-count { margin-top: 20px; font-size: 0.9rem; color: #555; border-top: 1px solid #eee; padding-top: 15px; }

/* 列表区 */
.listings-area { flex: 1; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }

/* 卡片样式 */
.card { background: white; border-radius: 12px; overflow: hidden; border: 1px solid #eee; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; }
.card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }

.card-img { height: 180px; background-size: cover; background-position: center; position: relative; background-color: #eee; }
.qty-badge { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }

.card-body { padding: 15px; display: flex; flex-direction: column; flex: 1; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.race { font-weight: 700; color: #2c3e50; font-size: 1.1rem; }
.sex { font-size: 0.8rem; background: #eef2f7; color: #555; padding: 2px 6px; border-radius: 4px; }

.details p { margin: 4px 0; font-size: 0.9rem; color: #666; }
.seller { font-size: 0.8rem; color: #999; margin-top: 10px !important; }

.btn-offer { margin-top: auto; width: 100%; padding: 10px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 15px; transition: background 0.2s; }
.btn-offer:hover { background: #34495e; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-card { background: white; width: 400px; padding: 30px; border-radius: 12px; box-shadow: 0 20px 50px rgba(0,0,0,0.2); }
.modal-card h3 { margin-top: 0; color: #2c3e50; }
.subtitle { color: #888; font-size: 0.9rem; margin-bottom: 20px; }
.item-summary { background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #eee; text-align: center; }

.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
.form-group input, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }

.btn-submit { width: 100%; padding: 12px; background: #27ae60; color: white; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.btn-cancel { width: 100%; padding: 10px; background: none; border: none; color: #888; margin-top: 10px; cursor: pointer; }

/* 响应式 */
@media (max-width: 768px) {
  .market-container { flex-direction: column; padding: 10px; }
  .filters { width: 100%; box-sizing: border-box; }
  .grid { grid-template-columns: 1fr; }
  .navbar { padding: 0 20px; }
  .modal-card { width: 90%; }
}
</style>