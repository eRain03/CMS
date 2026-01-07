<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoggedIn = ref(false)
const activeTab = ref('negotiations') // 默认优先显示交易动态
const notifications = ref([])
const myListings = ref({ supply: [], demand: [] })

// 存储提案数据
const myProposals = ref({ sent: [], received: [] })
const loading = ref(false)
const expandedNotif = ref(null)

// --- 支付/解锁弹窗状态 ---
const showPayModal = ref(false)
const paying = ref(false)
const pendingNotif = ref(null)
const unlockedSet = reactive(new Set())
const showActionSheet = ref(false)
const currentPaymentProp = ref(null)

// ✅ 新增：详情弹窗控制状态
const showDetailModal = ref(false)
const selectedProposal = ref(null)
const selectedTransaction = ref(null)
const userRole = ref(localStorage.getItem('role') || '')
const transactionStatus = computed(() => selectedTransaction.value?.data?.status || null)
const transactionFinalAmount = computed(() => selectedTransaction.value?.data?.final_amount || 0)

const API_BASE = 'http://43.248.188.75:38939'

// 计算未读消息
const unreadCount = computed(() => {
  return notifications.value.filter(n => !unlockedSet.has(n.timestamp)).length
})

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    isLoggedIn.value = true
    await loadDashboard(token)
  }
})

const loadDashboard = async (token) => {
  loading.value = true
  try {
    const headers = { 'Authorization': `Bearer ${token}` }

    // 并行加载所有数据
    const [resNotif, resListings, resReceived, resSent] = await Promise.all([
      fetch(`${API_BASE}/api/notifications`, { headers }),
      fetch(`${API_BASE}/api/my-listings`, { headers }),
      fetch(`${API_BASE}/api/my-proposals`, { headers }),      // 卖家视角
      fetch(`${API_BASE}/api/my-sent-proposals`, { headers })  // 买家视角
    ])

    if (resNotif.status === 401) return handleLogout()

    notifications.value = await resNotif.json()
    myListings.value = await resListings.json()
    myProposals.value.received = await resReceived.json()
    myProposals.value.sent = await resSent.json()

  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ✅ 新增：打开详情弹窗的方法
const loadTransactionForProposal = async (proposal) => {
  selectedTransaction.value = null
  const token = localStorage.getItem('token')
  if (!proposal?.supply_id) return
  try {
    const res = await fetch(`${API_BASE}/api/transactions/by-listing/${proposal.supply_id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      selectedTransaction.value = await res.json()
    }
  } catch (e) {
    console.warn('No transaction yet for listing', proposal.supply_id)
  }
}

const openProposalDetails = async (proposal) => {
  selectedProposal.value = proposal
  await loadTransactionForProposal(proposal)
  showDetailModal.value = true
}

// --- 卖家操作：接受/拒绝提案 ---
const handleProposalAction = async (id, action) => {
  if(!confirm(`Are you sure you want to ${action} this offer?`)) return

  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/proposals/${id}/${action}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if(res.ok) {
      alert('Success! Status updated.')
      loadDashboard(token) // 刷新数据
    } else {
      const err = await res.json()
      alert(err.detail || 'Action failed')
    }
  } catch(e) {
    alert('Error: ' + e.message)
  }
}

// 跳转到称重页面
const goToWeighing = (supplyId) => {
  router.push(`/weighing/${supplyId}`)
}

// --- 买家操作：打开支付弹窗 ---
const openPaymentModal = (proposal) => {
  currentPaymentProp.value = proposal
  showPayModal.value = true
}

// --- 买家操作：执行支付 ---
const processPayment = async () => {
  if(!currentPaymentProp.value) return
  paying.value = true
  const token = localStorage.getItem('token')

  try {
    const res = await fetch(`${API_BASE}/api/pay-reservation/${currentPaymentProp.value.id}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if(res.ok) {
      const data = await res.json()
      alert(`Payment Successful! Reservation deposit paid.\n\nStatus: ${data.status || 'RESERVED'}\n\nNext: Wait for seller to start weighing.`)
      showPayModal.value = false
      loadDashboard(token)
    } else {
      const err = await res.json()
      alert(err.detail || 'Payment failed')
    }
  } catch(e) {
    alert('Network Error during payment')
  } finally {
    paying.value = false
  }
}

// 买家支付尾款
const payFinalPayment = async () => {
  const tx = selectedTransaction.value?.data
  if (!tx) return alert('No transaction found for this listing yet.')
  if (tx.status !== 'awaiting_final_payment') return alert(`Transaction status is ${tx.status}, cannot pay final amount.`)

  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/transactions/${tx.id}/pay-final`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      alert('✅ Final payment sent. Waiting for seller confirmation.')
      await loadDashboard(token)
      await loadTransactionForProposal(selectedProposal.value)
    } else {
      const err = await res.json()
      alert(err.detail || 'Payment failed')
    }
  } catch (e) {
    alert('Network Error during final payment')
  }
}

// 卖家确认收款并退押金
const confirmPaymentReceipt = async () => {
  const tx = selectedTransaction.value?.data
  if (!tx) return alert('No transaction found for this listing yet.')
  if (!confirm('确认已收到尾款？确认后将完成交易并退还押金。')) return

  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/transactions/${tx.id}/confirm-payment`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      alert('✅ 收款确认成功！交易已完成，押金已退还。')
      await loadDashboard(token)
      await loadTransactionForProposal(selectedProposal.value)
    } else {
      const err = await res.json()
      alert('确认失败: ' + err.detail)
    }
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

const toggleNotif = (index) => { expandedNotif.value = expandedNotif.value === index ? null : index }
const openUnlockModal = (notif, event) => { event.stopPropagation(); pendingNotif.value = notif; showPayModal.value = true }
const confirmPay = () => { paying.value = true; setTimeout(() => { unlockedSet.add(pendingNotif.value.timestamp); paying.value = false; showPayModal.value = false; pendingNotif.value = null }, 800) }

const handleLogout = () => { localStorage.removeItem('token'); isLoggedIn.value = false; router.push('/login') }

// 辅助函数
const formatTargets = (targets) => {
  if (!targets || targets.length === 0) return 'No region specified'
  return targets.map(t => {
    if (typeof t === 'string') return t
    return `${t.state}${t.city !== 'ANY' ? '-' + t.city : ''}`
  }).join(', ')
}
</script>

<template>
  <div class="home-container">

    <nav class="navbar">
      <div class="brand-section">
        <span class="brand-logo">CATTLE MATCH</span>
        <span class="brand-divider">|</span>
        <span class="brand-slogan">Intelligent Allocation</span>
      </div>

      <div class="nav-right">
        <a href="#" @click.prevent="router.push('/market')" class="nav-link">
          <span class="icon">🌎</span> Marketplace
        </a>
        <template v-if="isLoggedIn">
          <div class="user-status"><span class="dot"></span> Online</div>
          <button @click="handleLogout" class="nav-btn-outline">Logout</button>
        </template>
        <template v-else>
          <button @click="router.push('/login')" class="nav-btn-primary">Sign In</button>
        </template>
      </div>
    </nav>

    <div v-if="!isLoggedIn" class="landing-wrapper fade-in-up">
      <div class="hero-section">
        <div class="status-pill">● System Operational</div>
        <h1 class="hero-title">Bridging the Gap between <br> Pasture and Market.</h1>
        <p class="hero-subtitle">An algorithmic approach to livestock allocation.</p>
      </div>
      <div class="entry-cards">
        <router-link to="/login" class="entry-card card-farmer">
          <div class="card-bg-icon">🌾</div>
          <div class="card-inner">
            <span class="role-tag">The Origin</span>
            <h2>Farmer</h2>
            <p class="role-desc">Register livestock supply.</p>
            <div class="fake-btn">Start Submission →</div>
          </div>
        </router-link>
        <router-link to="/login" class="entry-card card-buyer">
          <div class="card-bg-icon">🏭</div>
          <div class="card-inner">
            <span class="role-tag">The Destination</span>
            <h2>Slaughterhouse</h2>
            <p class="role-desc">Secure standardized inventory.</p>
            <div class="fake-btn">Post Demand →</div>
          </div>
        </router-link>
      </div>
      <footer class="landing-footer">© 2025 Tayen System · Secure & Rational</footer>
    </div>

    <div v-else class="dashboard-wrapper fade-in">

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">Notifications</span>
          <span class="stat-value">{{ notifications.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Active Supply</span>
          <span class="stat-value">{{ myListings.supply.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Negotiations</span>
          <span class="stat-value">{{ myProposals.received.length + myProposals.sent.length }}</span>
        </div>
      </div>

      <div class="action-grid">
        <div class="action-card farmer" @click="router.push('/farmer')">
          <div class="icon">🌾</div>
          <div class="text"><h3>Post Supply</h3><p>I have cattle to sell</p></div>
          <div class="arrow">＋</div>
        </div>
        <div class="action-card buyer" @click="router.push('/slaughterhouse')">
          <div class="icon">🏭</div>
          <div class="text"><h3>Post Demand</h3><p>I need to buy cattle</p></div>
          <div class="arrow">＋</div>
        </div>
      </div>

      <div class="content-area">
        <div class="tabs-header">
          <button class="tab-btn" :class="{ active: activeTab === 'negotiations' }" @click="activeTab = 'negotiations'">
            💰 Deals
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'notifications' }" @click="activeTab = 'notifications'">
            Alerts <span class="badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'listings' }" @click="activeTab = 'listings'">
            Listings
          </button>
        </div>

        <div class="tab-body">

          <div v-if="activeTab === 'negotiations'" class="negotiation-list">

            <div v-if="myProposals.received.length > 0">
              <h3 class="sub-header">📥 Incoming Offers (You are Seller)</h3>
              <div v-for="p in myProposals.received" :key="p.id" class="minimal-card deal-card">
                <div class="deal-header">
                  <span class="price-tag">R$ {{ p.price_offer.toLocaleString() }}</span>
                  <span class="status-badge" :class="p.status">{{ p.status }}</span>
                </div>
                <div class="deal-body">
                  <p><strong>From Buyer:</strong> {{ p.buyer_id }}</p>
                  <p class="msg">"{{ p.message }}"</p>
                </div>

                <div class="deal-actions">
                  <button class="btn-sm view-btn" @click.stop="openProposalDetails(p)">📄 View Details</button>
                  <template v-if="p.status === 'PENDING'">
                    <button class="btn-sm reject" @click.stop="handleProposalAction(p.id, 'reject')">Reject</button>
                    <button class="btn-sm accept" @click.stop="handleProposalAction(p.id, 'accept')">Accept</button>
                  </template>
                </div>

                <div class="deal-footer" v-if="p.status === 'ACCEPTED'">
                  <span>⏳ Accepted. Waiting for buyer payment...</span>
                </div>
                <div class="deal-footer success" v-if="p.status === 'PAID'">
                  <span>✅ Buyer paid reservation fee. Ready for weighing!</span>
                  <div style="margin-top: 8px;">
                    <button 
                      class="btn-sm weighing-btn" 
                      @click.stop="goToWeighing(p.supply_id)"
                      style="background: #27ae60; color: white;"
                    >
                      ⚖️ Start Weighing
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="myProposals.sent.length > 0" class="mt-40">
              <h3 class="sub-header">📤 My Offers (You are Buyer)</h3>
              <div v-for="p in myProposals.sent" :key="p.id" class="minimal-card deal-card">
                <div class="deal-header">
                  <div class="supply-mini-info">
                    <span class="race">{{ p.supply_detail?.race }}</span>
                    <span class="qty">x{{ p.supply_detail?.qty }}</span>
                  </div>
                  <span class="status-badge" :class="p.status">{{ p.status }}</span>
                </div>
                <div class="deal-body">
                  <p><strong>Your Offer:</strong> R$ {{ p.price_offer.toLocaleString() }}</p>
                  <p class="loc">📍 {{ p.supply_detail?.location }}</p>
                </div>

                <div class="deal-actions">
                  <button class="btn-sm view-btn" @click.stop="openProposalDetails(p)">📄 View Details</button>
                  <div v-if="p.status === 'ACCEPTED'" style="margin-left:auto">
                    <p class="pay-hint">Offer Accepted!</p>
                    <button class="btn-sm pay" @click.stop="openPaymentModal(p)">
                      💳 Pay Fee
                    </button>
                  </div>
                </div>

                <div class="deal-footer success" v-if="p.status === 'PAID'">
                  <span>✅ Deal Sealed. Waiting for seller to start weighing.</span>
                  <div v-if="p.supply_detail" style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                    <a 
                      v-if="p.supply_detail.nfe_file || p.supply_detail.gta_file"
                      :href="`${API_BASE}/api/files/${p.supply_detail.nfe_file || p.supply_detail.gta_file}`"
                      target="_blank"
                      class="btn-sm"
                      style="background: #3498db; color: white; text-decoration: none;"
                    >
                      📄 Download Documents
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="myProposals.received.length === 0 && myProposals.sent.length === 0" class="empty-state">
              <span class="empty-icon">🤝</span>
              <p>No active negotiations yet. Go to Market to make offers.</p>
            </div>
          </div>

          <div v-if="activeTab === 'notifications'">
            <div v-if="notifications.length === 0" class="empty-state">
              <span class="empty-icon">📭</span><p>No new messages.</p>
            </div>
            <div v-else class="notif-list">
              <div v-for="(n, i) in notifications" :key="i" class="minimal-card notif-card" :class="{ expanded: expandedNotif === i }" @click="toggleNotif(i)">
                <div class="card-header">
                  <span class="status-dot" :class="{ read: unlockedSet.has(n.timestamp) }"></span>
                  <div class="header-main">
                    <span class="msg-title">{{ n.message }}</span>
                    <span class="time">{{ new Date(n.timestamp * 1000).toLocaleDateString() }}</span>
                  </div>
                  <span class="expand-icon">{{ expandedNotif === i ? '−' : '+' }}</span>
                </div>
                <div v-if="expandedNotif === i" class="card-details slide-down">
                  <div v-if="n.details" class="info-grid">
                    <div class="info-item full-width">
                      <label>Contact Info</label>
                      <div v-if="unlockedSet.has(n.timestamp)" class="contact-revealed fade-in">
                        <span class="phone-icon">📞</span> <strong>{{ n.details.contact }}</strong>
                      </div>
                      <div v-else class="contact-locked">
                        <span class="blur-text">+55 11 9****-****</span>

                      </div>
                    </div>
                    <div class="info-item"><label>Race</label> {{ n.details.race }}</div>
                    <div class="info-item"><label>Location</label> {{ n.details.location }}</div>
                    <div class="info-item"><label>Quantity</label> {{ n.details.qty }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ✅ Listings Tab 修改区域 -->
          <div v-if="activeTab === 'listings'">
             <div v-if="myListings.supply.length === 0 && myListings.demand.length === 0" class="empty-state">
                <span class="empty-icon">📝</span><p>You haven't posted any listings yet.</p>
             </div>

             <div v-if="myListings.supply.length > 0">
                <h3 class="sub-header">Supply (Active)</h3>
                <div class="listings-grid">
                  <div v-for="item in myListings.supply" :key="item.id" class="minimal-card listing-card supply-border">
                    <div class="l-top">
                      <span class="l-race">{{ item.race }}</span>
                      <span class="status-tag" :class="item.status">{{ item.status }}</span>
                    </div>
                    <div class="l-btm">📍 {{ item.city }}, {{ item.state }} · {{ item.quantity }} head</div>

                    <!-- ✅ 新增：操作按钮区域 -->
                    <div class="listing-actions" style="margin-top: 12px; display: flex; gap: 8px;">
                      <!-- 如果状态是 RESERVED, SOLD 或 AWAITING_PAYMENT，显示称重按钮 -->
                      <button
                        v-if="['RESERVED', 'SOLD', 'AWAITING_PAYMENT'].includes(item.status)"
                        @click="router.push(`/weighing/${item.id}`)"
                        class="btn-sm weighing-btn"
                        style="background: #27ae60; color: white;"
                      >
                        ⚖️ Start Weighing
                      </button>

                      <!-- 如果已经完成称重，显示结算按钮 -->
                      <button
                        v-if="item.status === 'WEIGHING_COMPLETE'"
                        @click="router.push(`/finalize/${item.id}`)"
                        class="btn-sm finalize-btn"
                      >
                        💰 Finalize
                      </button>
                    </div>
                  </div>
                </div>
             </div>
             
             <div v-if="myListings.demand.length > 0" class="mt-40">
                <h3 class="sub-header">Demand (Active)</h3>
                <div class="listings-grid">
                  <div v-for="item in myListings.demand" :key="item.id" class="minimal-card listing-card demand-border">
                    <div class="l-top"><span class="l-race">{{ item.race }}</span><span class="l-qty">Need {{ item.quantity }}+</span></div>
                    <div class="l-btm">🎯 Target: {{ formatTargets(item.targets) }}</div>
                  </div>
                </div>
             </div>
          </div>

        </div>
      </div>
    </div>

    <!-- 弹窗部分保持不变 -->
    <div v-if="showDetailModal && selectedProposal" class="modal-overlay" @click="showDetailModal = false">
      <div class="modal-card modal-lg" @click.stop>

        <div class="modal-header-bar">
          <div class="header-left">
            <span class="modal-label">PROPOSAL ID</span>
            <span class="modal-id">#{{ selectedProposal.id }}</span>
          </div>
          <div class="header-right">
            <span class="status-badge large" :class="selectedProposal.status">{{ selectedProposal.status }}</span>
            <button class="close-icon" @click="showDetailModal = false">×</button>
          </div>
        </div>

        <div class="modal-scroll-body">

          <div class="detail-block highlight-block">
            <div class="db-row">
              <div class="db-item big-price">
                <label>Total Offer Amount</label>
                <span class="currency">R$</span> {{ selectedProposal.price_offer.toLocaleString() }}
              </div>
              <div class="db-item" v-if="selectedProposal.supply_detail">
                <label>Unit Price (Est.)</label>
                <span>R$ {{ (selectedProposal.price_offer / selectedProposal.supply_detail.quantity).toFixed(2) }} / head</span>
              </div>
              <div class="db-item">
                <label>Payment Terms</label>
                <span>Standard Escrow</span>
              </div>
            </div>
          </div>

          <div class="detail-block">
            <h3 class="block-title">🐄 Livestock Specifications</h3>
            <div class="info-grid-detailed" v-if="selectedProposal.supply_detail">
              <div class="ig-row">
                <div class="ig-cell"><label>Breed / Race</label> <strong>{{ selectedProposal.supply_detail.race }}</strong></div>
                <div class="ig-cell"><label>Quantity</label> <strong>{{ selectedProposal.supply_detail.quantity }} Head</strong></div>
              </div>
              <div class="ig-row">
                <div class="ig-cell"><label>Average Weight</label> <span>{{ selectedProposal.supply_detail.weight || 'N/A' }} kg</span></div>
                <div class="ig-cell"><label>Age</label> <span>{{ selectedProposal.supply_detail.age || 'N/A' }} months</span></div>
              </div>
              <div class="ig-row">
                <div class="ig-cell"><label>Origin Farm</label> <span>{{ selectedProposal.seller_id }}</span></div>
                <div class="ig-cell"><label>Location</label> <span>{{ selectedProposal.supply_detail.city }}, {{ selectedProposal.supply_detail.state }}</span></div>
              </div>
            </div>
            <div v-else class="no-data">Supply details data unavailable.</div>
          </div>

          <div class="detail-block" v-if="selectedProposal.loading_date || selectedProposal.conditions">
            <h3 class="block-title">📋 Proposal Details</h3>
            <div class="info-grid-detailed" v-if="selectedProposal.loading_date || selectedProposal.conditions">
              <div class="ig-row" v-if="selectedProposal.loading_date">
                <div class="ig-cell"><label>Loading Date</label> <span>{{ selectedProposal.loading_date }}</span></div>
              </div>
              <div class="ig-row" v-if="selectedProposal.conditions">
                <div class="ig-cell full-width"><label>Conditions</label> <span>{{ selectedProposal.conditions }}</span></div>
              </div>
            </div>
          </div>

          <div class="detail-block" v-if="selectedProposal.status === 'PAID' && selectedProposal.supply_detail">
            <h3 class="block-title">📄 Documents</h3>
            <div class="info-grid-detailed">
              <div class="ig-row" style="gap: 10px;">
                <a 
                  v-if="selectedProposal.supply_detail.nfe_file"
                  :href="`${API_BASE}/api/files/${selectedProposal.supply_detail.nfe_file}`"
                  target="_blank"
                  class="btn-sm"
                  style="background: #3498db; color: white; text-decoration: none; display: inline-block;"
                >
                  📄 Download NF-e
                </a>
                <a 
                  v-if="selectedProposal.supply_detail.gta_file"
                  :href="`${API_BASE}/api/files/${selectedProposal.supply_detail.gta_file}`"
                  target="_blank"
                  class="btn-sm"
                  style="background: #27ae60; color: white; text-decoration: none; display: inline-block;"
                >
                  🚛 Download GTA
                </a>
                <span v-if="!selectedProposal.supply_detail.nfe_file && !selectedProposal.supply_detail.gta_file" class="no-data">
                  Documents will be available after seller uploads them.
                </span>
              </div>
            </div>
          </div>

          <div class="detail-block">
            <h3 class="block-title">💬 Negotiation Context</h3>
            <div class="message-box">
              <label>Message from Counterparty:</label>
              <p>"{{ selectedProposal.message }}"</p>
            </div>
            <div class="meta-info">
              <span>Counterparty ID: {{ selectedProposal.buyer_id || selectedProposal.seller_id }}</span>
              <span>Date: {{ new Date(selectedProposal.timestamp * 1000).toLocaleDateString() }}</span>
            </div>
          </div>

        </div>

        <div class="modal-footer-bar">
          <!-- 卖家操作：接受/拒绝收到的提案 -->
          <template v-if="selectedProposal.status === 'PENDING' && myProposals.received.some(p => p.id === selectedProposal.id)">
            <button class="btn-modal reject" @click="handleProposalAction(selectedProposal.id, 'reject'); showDetailModal = false">Reject Offer</button>
            <button class="btn-modal accept" @click="handleProposalAction(selectedProposal.id, 'accept'); showDetailModal = false">Accept Deal</button>
          </template>

          <!-- 买家操作：支付押金 -->
          <template v-if="selectedProposal.status === 'ACCEPTED' && myProposals.sent.some(p => p.id === selectedProposal.id)">
            <button class="btn-modal pay" @click="showDetailModal = false; openPaymentModal(selectedProposal)">Proceed to Payment</button>
          </template>

          <!-- PAID：卖家开始称重 -->
          <template v-if="selectedProposal.status === 'PAID' && myProposals.received.some(p => p.id === selectedProposal.id)">
            <button class="btn-modal accept" @click="showDetailModal = false; goToWeighing(selectedProposal.supply_id)">⚖️ Start Weighing</button>
          </template>

          <!-- 尾款：买家支付 -->
          <template v-if="transactionStatus === 'awaiting_final_payment' && myProposals.sent.some(p => p.id === selectedProposal.id)">
            <button class="btn-modal pay" @click="payFinalPayment">
              💳 Pay Final Amount (R$ {{ transactionFinalAmount.toFixed(2) }})
            </button>
          </template>

          <!-- 尾款：买家已支付，卖家确认 -->
          <template v-if="transactionStatus === 'final_payment_paid' && myProposals.received.some(p => p.id === selectedProposal.id)">
            <button class="btn-modal accept" @click="confirmPaymentReceipt">
              ✅ Confirm Receipt & Refund Deposit
            </button>
          </template>

          <!-- 状态提示 -->
          <div v-if="transactionStatus === 'final_payment_paid' && myProposals.sent.some(p => p.id === selectedProposal.id)" class="footer-hint">
            Final payment sent. Waiting for seller confirmation.
          </div>
          <div v-if="transactionStatus === 'awaiting_final_payment' && myProposals.received.some(p => p.id === selectedProposal.id)" class="footer-hint">
            Waiting for buyer to pay final amount.
          </div>

          <button class="btn-modal secondary" @click="showDetailModal = false">Close Window</button>
        </div>

      </div>
    </div>

    <div v-if="showPayModal" class="modal-overlay" @click="showPayModal = false">
      <div class="modal-card" @click.stop>
        <div class="modal-icon">{{ currentPaymentProp ? '🔒' : '💳' }}</div>
        <h3>{{ currentPaymentProp ? 'Confirm Deal' : 'Confirm Unlock' }}</h3>
        <p v-if="currentPaymentProp">Pay reservation fee to lock this deal.</p>
        <p v-else>Unlock contact details for this match.</p>

        <div class="price-tag"><span class="currency">US$</span> {{ currentPaymentProp ? '50.00' : '5.00' }}</div>

        <button class="pay-btn" @click="currentPaymentProp ? processPayment() : confirmPay()" :disabled="paying">
          {{ paying ? 'Processing...' : 'Confirm Payment' }}
        </button>
        <button class="cancel-btn" @click="showPayModal = false">Cancel</button>
      </div>
    </div>

    <nav class="mobile-tab-bar" v-if="isLoggedIn">
      <div class="tab-link" :class="{ active: activeTab === 'negotiations' }" @click="activeTab = 'negotiations'">
        <span class="tab-icon">💰</span><span class="tab-text">Deals</span>
      </div>
      <div class="tab-link" :class="{ active: activeTab === 'notifications' }" @click="activeTab = 'notifications'">
        <span class="tab-icon">🔔</span><span class="tab-text">Alerts</span>
      </div>
      <div class="tab-link highlight" @click="showActionSheet = true"><span class="tab-icon-plus">＋</span></div>
      <div class="tab-link" :class="{ active: activeTab === 'listings' }" @click="activeTab = 'listings'">
        <span class="tab-icon">📝</span><span class="tab-text">List</span>
      </div>
      <div class="tab-link" @click="router.push('/market')">
        <span class="tab-icon">🌎</span><span class="tab-text">Market</span>
      </div>
    </nav>

    <div v-if="showActionSheet" class="mobile-action-overlay" @click="showActionSheet = false">
      <div class="mobile-action-sheet" @click.stop>
        <h3>Create New Listing</h3>
        <button class="sheet-btn farmer" @click="router.push('/farmer')">🌾 Post Supply (Farmer)</button>
        <button class="sheet-btn buyer" @click="router.push('/slaughterhouse')">🏭 Post Demand (Buyer)</button>
        <button class="sheet-cancel" @click="showActionSheet = false">Cancel</button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 基础样式 (保留原样) */
.home-container { min-height: 100vh; background-color: #f8f9fa; font-family: 'Helvetica Neue', Helvetica, sans-serif; color: #333; display: flex; flex-direction: column; align-items: center; padding-bottom: 80px; }
.navbar { width: 100%; height: 70px; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; background: white; border-bottom: 1px solid #eaeaea; box-sizing: border-box; position: sticky; top: 0; z-index: 100; }
.brand-section { display: flex; align-items: center; gap: 12px; }
.brand-logo { font-weight: 700; letter-spacing: 1px; font-size: 1.1rem; color: #1a1a1a; }
.brand-divider { color: #ddd; font-weight: 300; }
.brand-slogan { font-size: 0.85rem; color: #888; letter-spacing: 0.5px; text-transform: uppercase; }
.nav-right { display: flex; align-items: center; gap: 25px; }
.nav-link { text-decoration: none; color: #666; font-size: 0.9rem; font-weight: 500; display: flex; align-items: center; gap: 6px; transition: color 0.2s; }
.nav-link:hover { color: #2c3e50; }
.user-status { font-size: 0.85rem; color: #27ae60; font-weight: 500; display: flex; align-items: center; gap: 6px; background: rgba(39, 174, 96, 0.08); padding: 4px 10px; border-radius: 20px; }
.dot { width: 6px; height: 6px; background: #27ae60; border-radius: 50%; }
.nav-btn-outline { background: transparent; border: 1px solid #ddd; padding: 6px 16px; border-radius: 6px; cursor: pointer; color: #666; font-size: 0.85rem; transition: all 0.2s; }
.nav-btn-primary { background: #2c3e50; color: white; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; }

.landing-wrapper { width: 100%; max-width: 1000px; padding: 60px 20px; text-align: center; }
.hero-section { margin-bottom: 60px; }
.status-pill { display: inline-block; padding: 6px 14px; border-radius: 20px; background: #eef1f5; color: #666; font-size: 0.75rem; font-weight: 600; margin-bottom: 25px; }
.hero-title { font-size: 3rem; font-weight: 300; line-height: 1.1; margin-bottom: 25px; color: #111; letter-spacing: -1px; }
.hero-subtitle { font-size: 1.1rem; color: #7f8c8d; line-height: 1.6; font-weight: 300; }
.entry-cards { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; }
.entry-card { position: relative; width: 300px; height: 360px; background: white; border-radius: 16px; text-decoration: none; color: #333; border: 1px solid rgba(0,0,0,0.06); overflow: hidden; transition: all 0.3s; display: flex; flex-direction: column; }
.entry-card:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.08); }
.card-bg-icon { position: absolute; top: -20px; right: -20px; font-size: 10rem; opacity: 0.03; transition: transform 0.5s; }
.entry-card:hover .card-bg-icon { transform: rotate(10deg) scale(1.1); }
.card-inner { padding: 40px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; z-index: 1; text-align: left; }
.role-tag { font-size: 0.75rem; text-transform: uppercase; color: #999; letter-spacing: 2px; font-weight: 600; }
.entry-card h2 { font-size: 2rem; font-weight: 400; margin: 10px 0; }
.role-desc { font-size: 0.9rem; color: #666; line-height: 1.5; }
.fake-btn { margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; color: #333; font-weight: 600; font-size: 0.9rem; }
.landing-footer { margin-top: 80px; color: #ccc; font-size: 0.8rem; }

.dashboard-wrapper { width: 100%; max-width: 900px; padding: 40px 20px; }
.stats-bar { display: flex; gap: 20px; margin-bottom: 30px; }
.stat-item { flex: 1; background: white; border: 1px solid #eee; padding: 15px 20px; border-radius: 8px; display: flex; flex-direction: column; align-items: flex-start; }
.stat-label { font-size: 0.75rem; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
.stat-value { font-size: 1.8rem; font-weight: 600; color: #2c3e50; line-height: 1; }
.action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }
.action-card { background: white; border: 1px solid #eee; padding: 25px; border-radius: 12px; display: flex; align-items: center; cursor: pointer; transition: all 0.2s; position: relative; overflow: hidden; }
.action-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.04); border-color: transparent; }
.action-card.farmer:hover { border-left: 4px solid #4a7c59; }
.action-card.buyer:hover { border-left: 4px solid #c05c5c; }
.action-card .icon { font-size: 2rem; margin-right: 20px; }
.action-card .text h3 { margin: 0; font-size: 1.1rem; font-weight: 500; color: #333; }
.action-card .text p { margin: 4px 0 0 0; font-size: 0.85rem; color: #888; }
.action-card .arrow { margin-left: auto; font-size: 1.5rem; color: #ddd; font-weight: 300; }

.content-area { background: white; border: 1px solid #eee; border-radius: 12px; overflow: hidden; min-height: 400px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); }
.tabs-header { display: flex; border-bottom: 1px solid #eee; background: #fafafa; }
.tab-btn { flex: 1; background: none; border: none; padding: 18px; font-size: 0.95rem; color: #888; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.2s; position: relative; }
.tab-btn.active { background: white; color: #2c3e50; border-bottom-color: #2c3e50; font-weight: 600; }
.badge { background: #c0392b; color: white; font-size: 0.7rem; padding: 2px 6px; border-radius: 10px; position: absolute; top: 12px; margin-left: 5px; }
.tab-body { padding: 30px; }
.empty-state { text-align: center; color: #ccc; padding: 60px 0; }
.empty-icon { font-size: 3rem; display: block; margin-bottom: 15px; opacity: 0.5; }

/* Lists & Cards */
.notif-card { border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; cursor: pointer; transition: background 0.2s; }
.notif-card:hover { background: #f9f9f9; }
.card-header { padding: 15px; display: flex; align-items: center; }
.status-dot { width: 8px; height: 8px; background: #c0392b; border-radius: 50%; margin-right: 15px; flex-shrink: 0; }
.status-dot.read { background: #e0e0e0; }
.header-main { flex: 1; display: flex; justify-content: space-between; align-items: center; }
.msg-title { font-weight: 500; color: #333; font-size: 0.95rem; }
.time { font-size: 0.8rem; color: #aaa; }
.expand-icon { font-size: 1.2rem; color: #ccc; margin-left: 15px; font-weight: 300; }
.card-details { border-top: 1px solid #eee; background: #fafafa; padding: 20px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.9rem; }
.info-item label { display: block; font-size: 0.75rem; color: #999; text-transform: uppercase; margin-bottom: 4px; }
.full-width { grid-column: 1 / -1; margin-bottom: 10px; }
.sub-header { font-size: 0.85rem; color: #999; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; font-weight: 600; }
.listings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
.listing-card { border: 1px solid #eee; border-radius: 8px; padding: 15px; transition: transform 0.2s; }
.listing-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
.supply-border { border-top: 3px solid #4a7c59; }
.demand-border { border-top: 3px solid #c05c5c; }
.l-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.l-race { font-weight: 600; font-size: 1.05rem; }
.l-qty { font-size: 0.85rem; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; color: #666; }
.l-btm { font-size: 0.85rem; color: #888; }
.mt-40 { margin-top: 40px; }
.contact-locked { display: flex; justify-content: space-between; align-items: center; background: white; border: 1px dashed #ddd; padding: 10px 15px; border-radius: 6px; }
.blur-text { filter: blur(4px); opacity: 0.5; }
.unlock-btn { background: #2c3e50; color: white; border: none; padding: 6px 14px; border-radius: 4px; font-size: 0.85rem; cursor: pointer; transition: background 0.2s; }
.unlock-btn:hover { background: #34495e; }
.contact-revealed { display: flex; align-items: center; gap: 8px; font-size: 1.1rem; color: #2c3e50; padding: 5px 0; }

/* Modals */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 999; }
.modal-card { background: white; width: 320px; padding: 30px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.1); text-align: center; border: 1px solid #eee; }
.modal-icon { font-size: 2.5rem; margin-bottom: 15px; }
.price-tag { font-size: 2rem; font-weight: 700; color: #2c3e50; margin-bottom: 20px; }
.pay-btn { width: 100%; padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 8px; cursor: pointer; }
.cancel-btn { background: none; border: none; color: #999; margin-top: 10px; cursor: pointer; font-size: 0.9rem; }

/* Negotiations & Status */
.negotiation-list { padding-bottom: 20px; }
.deal-card { background: white; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.deal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f9f9f9; }
.status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.status-badge.PENDING { background: #fff3e0; color: #e67e22; }
.status-badge.ACCEPTED, .status-badge.AWAITING_PAYMENT { background: #e3f2fd; color: #2196f3; }
.status-badge.REJECTED { background: #ffebee; color: #c62828; }
.status-badge.PAID, .status-badge.SOLD { background: #e8f5e9; color: #2e7d32; }
.status-tag { font-size: 0.7rem; padding: 2px 6px; background: #eee; border-radius: 4px; color: #666; margin-left: 5px; }
.status-tag.SOLD { background: #27ae60; color: white; }
.status-tag.AWAITING_PAYMENT { background: #3498db; color: white; }

.deal-body { font-size: 0.9rem; color: #555; margin-bottom: 15px; }
.deal-actions { display: flex; gap: 10px; justify-content: flex-end; align-items: center; flex-wrap: wrap; }
.btn-sm { padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; border: none; cursor: pointer; }
.btn-sm.accept { background: #27ae60; color: white; }
.btn-sm.reject { background: #f5f5f5; color: #c0392b; }
.btn-sm.pay { background: #2c3e50; color: white; width: 100%; margin-top: 10px; }
.deal-footer { margin-top: 10px; font-size: 0.85rem; font-weight: 500; text-align: right; }
.deal-footer.success { color: #27ae60; }
.pay-hint { font-size: 0.8rem; color: #27ae60; margin: 0 0 5px 0; text-align: right; font-weight: 600; }

/* --- ✅ 新增：查看详情按钮样式 --- */
.view-btn {
  background: #eef2f7;
  color: #34495e;
  border: 1px solid #dce1e6;
  margin-right: auto; /* 让它靠左，和其他按钮分开 */
}
.view-btn:hover {
  background: #e1e7ed;
  border-color: #cbd5e0;
}

/* --- ✅ 新增：SaaS 风格详情弹窗 (Professional Modal) --- */
.modal-lg {
  width: 650px;
  max-width: 95vw;
  padding: 0; /* 重置 padding，使用内部布局 */
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  border-radius: 12px;
  overflow: hidden;
  text-align: left;
}

/* 头部 */
.modal-header-bar {
  padding: 20px 25px;
  background: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-label {
  display: block;
  font-size: 0.7rem;
  color: #999;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.modal-id {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2c3e50;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}
.status-badge.large {
  font-size: 0.8rem;
  padding: 6px 12px;
}
.close-icon {
  background: none;
  border: none;
  font-size: 1.8rem;
  color: #ccc;
  cursor: pointer;
  line-height: 1;
}
.close-icon:hover { color: #333; }

/* 内容滚动区 */
.modal-scroll-body {
  padding: 25px;
  overflow-y: auto;
  background: #fdfdfd;
  flex: 1;
}

/* 信息区块 */
.detail-block {
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}
.highlight-block {
  background: #f8fbff;
  border-color: #dbeafe;
}
.block-title {
  font-size: 0.9rem;
  color: #555;
  text-transform: uppercase;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
  font-weight: 600;
}

/* 财务行 */
.db-row {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}
.db-item label {
  display: block;
  font-size: 0.75rem;
  color: #888;
  margin-bottom: 4px;
}
.db-item span {
  font-weight: 600;
  color: #333;
}
.big-price {
  font-size: 1.4rem;
  color: #27ae60;
  font-weight: 700;
}
.currency { font-size: 1rem; color: #27ae60; }

/* 规格网格 */
.info-grid-detailed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ig-row {
  display: flex;
  border-bottom: 1px dashed #f0f0f0;
  padding-bottom: 8px;
}
.ig-row:last-child { border-bottom: none; }
.ig-cell {
  flex: 1;
}
.ig-cell label {
  font-size: 0.75rem;
  color: #999;
  display: block;
}
.ig-cell strong {
  font-size: 1rem;
  color: #2c3e50;
}

/* 消息框 */
.message-box {
  background: #f4f6f8;
  padding: 15px;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 10px;
  font-style: italic;
}
.message-box label {
  font-style: normal;
  font-weight: 600;
  font-size: 0.75rem;
  color: #888;
  display: block;
  margin-bottom: 5px;
}
.meta-info {
  font-size: 0.75rem;
  color: #aaa;
  display: flex;
  gap: 15px;
}

/* 底部操作栏 */
.modal-footer-bar {
  padding: 15px 25px;
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.btn-modal {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-modal.accept, .btn-modal.pay { background: #27ae60; color: white; }
.btn-modal.reject { background: #fff; border: 1px solid #e74c3c; color: #e74c3c; }
.btn-modal.secondary { background: #f1f2f6; color: #666; }
.btn-modal:hover { opacity: 0.9; }

/* Mobile Adaptation */
.mobile-tab-bar, .mobile-action-overlay { display: none; }
@media (max-width: 768px) {
  .navbar .nav-right, .navbar .brand-slogan, .navbar .brand-divider { display: none !important; }
  .navbar { justify-content: center !important; border-bottom: none !important; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
  .dashboard-wrapper { padding: 20px; padding-bottom: 80px; }
  .stats-bar { overflow-x: auto; padding-bottom: 10px; }
  .stat-item { min-width: 120px; }
  .entry-cards, .action-grid, .listings-grid { grid-template-columns: 1fr !important; display: grid !important; }
  .mobile-tab-bar { display: flex; position: fixed; bottom: 0; left: 0; width: 100%; height: 70px; background: white; border-top: 1px solid #eee; box-shadow: 0 -4px 20px rgba(0,0,0,0.05); z-index: 1000; justify-content: space-around; align-items: center; padding-bottom: 10px; }
  .tab-link { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; font-size: 0.7rem; flex: 1; height: 100%; cursor: pointer; }
  .tab-link.active { color: #2c3e50; font-weight: 600; }
  .tab-icon { font-size: 1.4rem; margin-bottom: 2px; }
  .tab-link.highlight { position: relative; top: -20px; }
  .tab-icon-plus { width: 56px; height: 56px; background: #2c3e50; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 8px 20px rgba(44, 62, 80, 0.4); font-weight: 300; }
  .mobile-action-overlay { display: flex !important; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 2000; align-items: flex-end; animation: fadeIn 0.2s; }
  .mobile-action-sheet { width: 100%; background: white; border-radius: 20px 20px 0 0; padding: 30px 20px 40px 20px; text-align: center; animation: slideUp 0.3s cubic-bezier(0.2, 0.8, 0.2, 1); }
  .mobile-action-sheet h3 { margin: 0 0 20px 0; font-size: 1.1rem; color: #333; }
  .sheet-btn { display: block; width: 100%; padding: 16px; margin-bottom: 12px; border: none; border-radius: 12px; font-size: 1rem; font-weight: 600; text-align: left; padding-left: 20px; }
  .sheet-btn.farmer { background: #e8f5e9; color: #2e7d32; }
  .sheet-btn.buyer { background: #ffebee; color: #c62828; }
  .sheet-cancel { background: none; border: none; color: #999; margin-top: 10px; font-size: 1rem; padding: 10px; }
}

.fade-in { animation: fadeIn 0.5s ease; }
.fade-in-up { animation: fadeInUp 0.8s ease; }
.slide-down { animation: slideDown 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }

/* ✅ 新增：Listing 按钮样式 */
.listing-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.weighing-btn {
  background: #9f7aea;
  color: white;
}

.weighing-btn:hover {
  background: #805ad5;
}

.finalize-btn {
  background: #27ae60;
  color: white;
}

.finalize-btn:hover {
  background: #219150;
}
</style>