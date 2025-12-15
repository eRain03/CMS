<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const API_BASE = 'http://43.248.188.75:38939'

const transactionId = route.params.id
const transaction = ref(null)
const listing = ref(null)
const loading = ref(false)
const paying = ref(false)

onMounted(async () => {
  await loadTransaction()
})

const loadTransaction = async () => {
  loading.value = true
  const token = localStorage.getItem('token')
  try {
    // 直接通过transaction_id获取交易
    const res = await fetch(`${API_BASE}/api/transactions/${transactionId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Transaction not found')
    }
    
    const data = await res.json()
    transaction.value = data.data
    
    // 如果有listing_id，加载listing信息
    if (transaction.value?.listing_id) {
      const resListings = await fetch(`${API_BASE}/api/my-listings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const listingsData = await resListings.json()
      listing.value = listingsData.supply.find(l => l.id === transaction.value.listing_id)
    }
    
  } catch (error) {
    console.error('加载失败:', error)
    alert('无法加载交易信息')
    router.push('/')
  } finally {
    loading.value = false
  }
}

const handlePayment = async () => {
  if (!confirm(`确认支付尾款 R$ ${transaction.value.final_amount.toFixed(2)}?`)) {
    return
  }

  paying.value = true
  const token = localStorage.getItem('token')

  try {
    const res = await fetch(`${API_BASE}/api/transactions/${transaction.value.id}/pay-final`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '支付失败')
    }

    const result = await res.json()
    alert('✅ 尾款支付成功！等待卖家确认收款。')
    router.push('/')

  } catch (error) {
    console.error('支付失败:', error)
    alert('支付失败: ' + error.message)
  } finally {
    paying.value = false
  }
}

const depositAmount = computed(() => {
  return transaction.value?.deposit_amount || 0
})

const totalOwed = computed(() => {
  return transaction.value?.final_amount || 0
})
</script>

<template>
  <div class="form-page">
    <a href="#" @click.prevent="router.push('/')" class="back-link">← Back to Home</a>

    <div class="form-container">
      <header>
        <h2>Final Payment</h2>
        <p class="desc">Pay the final amount based on actual weight measurement.</p>
      </header>

      <div v-if="loading">Loading...</div>

      <template v-else-if="transaction">
        <!-- 交易摘要 -->
        <div class="summary-box">
          <h3>💰 Payment Summary</h3>
          
          <div class="summary-row">
            <span class="label">Transaction ID:</span>
            <span class="value">#{{ transaction.id.slice(0, 8) }}</span>
          </div>

          <div class="summary-row" v-if="transaction.total_weight">
            <span class="label">Total Weight:</span>
            <span class="value">{{ transaction.total_weight.toFixed(2) }} kg</span>
          </div>

          <div class="summary-row" v-if="transaction.at_quantity">
            <span class="label">@ Quantity:</span>
            <span class="value">{{ transaction.at_quantity.toFixed(2) }} @</span>
          </div>

          <div class="summary-row" v-if="transaction.gross_amount">
            <span class="label">Gross Amount:</span>
            <span class="value">R$ {{ transaction.gross_amount.toFixed(2) }}</span>
          </div>

          <div class="summary-row deduction" v-if="transaction.transport_fee">
            <span class="label">- Transport Fee:</span>
            <span class="value">R$ {{ transaction.transport_fee.toFixed(2) }}</span>
          </div>

          <div class="summary-row deduction" v-if="transaction.funrural_tax">
            <span class="label">- Funrural Tax:</span>
            <span class="value">R$ {{ transaction.funrural_tax.toFixed(2) }}</span>
          </div>

          <div class="summary-row total">
            <span class="label">Final Amount to Pay:</span>
            <span class="value">R$ {{ transaction.final_amount.toFixed(2) }}</span>
          </div>

          <div class="summary-row deposit-info" v-if="depositAmount > 0">
            <span class="label">Reservation Deposit:</span>
            <span class="value">R$ {{ depositAmount.toFixed(2) }} (will be refunded after seller confirms payment)</span>
          </div>
        </div>

        <div class="alert-box info">
          <p>ℹ️ After payment, the seller will confirm receipt and your reservation deposit will be automatically refunded.</p>
        </div>

        <button
          @click="handlePayment"
          class="btn-pay"
          :disabled="paying || transaction.status !== 'awaiting_final_payment'"
        >
          {{ paying ? 'Processing Payment...' : `💳 Pay R$ ${transaction.final_amount.toFixed(2)}` }}
        </button>

        <div v-if="transaction.status !== 'awaiting_final_payment'" class="status-message">
          <p v-if="transaction.status === 'final_payment_paid'">
            ✅ Payment completed. Waiting for seller confirmation.
          </p>
          <p v-else-if="transaction.status === 'completed'">
            ✅ Transaction completed.
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.form-page { max-width: 700px; margin: 40px auto; padding: 0 20px; font-family: 'Helvetica Neue', sans-serif; }
.back-link { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; font-size: 0.9rem; }
.form-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; }

h2 { margin-top: 0; font-weight: 300; color: #2c3e50; }
.desc { color: #95a5a6; font-size: 0.9rem; margin-bottom: 25px; }

.summary-box { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 25px; border-radius: 12px; margin-bottom: 30px; border: 2px solid #a5d6a7; }
.summary-box h3 { margin: 0 0 20px 0; color: #2e7d32; }

.summary-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px dashed #c8e6c9; }
.summary-row:last-child { border-bottom: none; }
.summary-row .label { color: #555; font-size: 0.95rem; }
.summary-row .value { font-weight: 600; color: #2c3e50; font-size: 1rem; }

.summary-row.deduction .label { color: #d32f2f; }
.summary-row.deduction .value { color: #d32f2f; }

.summary-row.total { margin-top: 10px; padding-top: 15px; border-top: 2px solid #81c784; }
.summary-row.total .label { font-weight: 700; font-size: 1.1rem; color: #1b5e20; }
.summary-row.total .value { font-weight: 700; font-size: 1.5rem; color: #1b5e20; }

.summary-row.deposit-info { background: rgba(255, 255, 255, 0.5); padding: 10px; border-radius: 6px; margin-top: 10px; }
.summary-row.deposit-info .label { color: #1976d2; }
.summary-row.deposit-info .value { color: #1976d2; font-size: 0.9rem; }

.alert-box { background: #e3f2fd; border: 1px solid #64b5f6; border-radius: 8px; padding: 15px; margin-bottom: 25px; }
.alert-box.info p { margin: 5px 0; font-size: 0.9rem; color: #1565c0; }

.btn-pay { width: 100%; padding: 16px; background: #27ae60; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-pay:hover:not(:disabled) { background: #219150; }
.btn-pay:disabled { background: #a5d6a7; cursor: not-allowed; }

.status-message { margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px; text-align: center; }
.status-message p { margin: 0; color: #2e7d32; font-weight: 500; }

@media (max-width: 768px) {
  .form-page { padding: 1rem; }
  .form-container { padding: 20px; }
}
</style>

