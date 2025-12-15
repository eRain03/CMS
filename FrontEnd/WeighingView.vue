<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const API_BASE = 'http://43.248.188.75:38939'

const listingId = route.params.id
const listing = ref(null)
const weights = ref([])
const loading = ref(false)
const submitting = ref(false)
const weightType = ref('live')  // 'live' or 'dead'
const performInternalWeighing = ref(false)  // For dead weight: whether to perform internal weighing

const currentBatch = ref({
  quantity: null,
  total_weight: null
})

// 加载数据
onMounted(async () => {
  await loadListing()
  await loadWeights()
})

const loadListing = async () => {
  // 从你的 my-listings 接口获取
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/my-listings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    listing.value = data.supply.find(l => l.id === listingId)
    if (listing.value) {
      weightType.value = listing.value.weight_type || 'live'
    }
  } catch (error) {
    console.error('加载列表失败:', error)
  }
}

const loadWeights = async () => {
  loading.value = true
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/listings/${listingId}/weights`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    weights.value = data.data || []
  } catch (error) {
    console.error('加载称重记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 计算属性
const totalWeighed = computed(() => {
  return weights.value.reduce((sum, w) => sum + w.quantity, 0)
})

const totalWeight = computed(() => {
  return weights.value.reduce((sum, w) => sum + w.total_weight, 0)
})

const remaining = computed(() => {
  return (listing.value?.quantity || 0) - totalWeighed.value
})

const progressPercent = computed(() => {
  if (!listing.value) return 0
  return Math.min((totalWeighed.value / listing.value.quantity) * 100, 100)
})

const averageWeight = computed(() => {
  if (totalWeighed.value === 0) return '0.00'
  return (totalWeight.value / totalWeighed.value).toFixed(2)
})

const nextBatchNumber = computed(() => {
  return weights.value.length + 1
})

const canAddWeight = computed(() => {
  return currentBatch.value.quantity &&
         currentBatch.value.total_weight &&
         currentBatch.value.quantity <= remaining.value
})

const isComplete = computed(() => {
  return totalWeighed.value >= (listing.value?.quantity || 0)
})

// 添加称重记录
const addWeightEntry = async () => {
  if (!canAddWeight.value) return

  submitting.value = true
  const token = localStorage.getItem('token')

  try {
    const weightData = {
      batch_number: nextBatchNumber.value,
      quantity: currentBatch.value.quantity,
      total_weight: currentBatch.value.total_weight
    }

    const res = await fetch(`${API_BASE}/api/listings/${listingId}/weights`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(weightData)
    })

    if (!res.ok) throw new Error('添加失败')

    await loadWeights()

    currentBatch.value = {
      quantity: null,
      total_weight: null
    }

  } catch (error) {
    console.error('添加称重记录失败:', error)
    alert('添加失败,请重试')
  } finally {
    submitting.value = false
  }
}

// 死重模式：处理内部称重（可选）
const handleInternalWeight = async () => {
  if (!performInternalWeighing.value) {
    // 跳过称重，直接标记为可运输
    submitting.value = true
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(`${API_BASE}/api/listings/${listingId}/internal-weight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ perform_weighing: false })
      })
      if (!res.ok) throw new Error('操作失败')
      alert('已标记为可运输（未进行内部称重）')
      goToFinalize()
    } catch (error) {
      console.error('操作失败:', error)
      alert('操作失败,请重试')
    } finally {
      submitting.value = false
    }
  } else {
    // 执行内部称重（使用与生重相同的流程）
    await addWeightEntry()
  }
}

// 完成称重
const goToFinalize = () => {
  router.push(`/finalize/${listingId}`)
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="form-page">
    <a href="#" @click.prevent="router.push('/')" class="back-link">← Back to Home</a>

    <div class="form-container">
      <!-- 页头 -->
      <header>
        <h2>Weighing Management</h2>
        <p class="desc" v-if="listing">
          Listing #{{ listing.id }} - {{ listing.race }} {{ listing.cattle_type }}
        </p>
      </header>

      <div v-if="loading">Loading...</div>

      <template v-else>
        <!-- 进度显示 -->
        <div class="progress-section">
          <div class="progress-header">
            <span>Weighing Progress</span>
            <span class="progress-numbers">
              <strong>{{ totalWeighed }}</strong> / {{ listing?.quantity || 0 }} Head
            </span>
          </div>

          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: progressPercent + '%' }"
            ></div>
          </div>

          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">Weighed</div>
              <div class="stat-value">{{ totalWeighed }} <span class="unit">head</span></div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Total Weight</div>
              <div class="stat-value">{{ totalWeight.toFixed(2) }} <span class="unit">kg</span></div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Remaining</div>
              <div class="stat-value">{{ remaining }} <span class="unit">head</span></div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Average</div>
              <div class="stat-value">{{ averageWeight }} <span class="unit">kg/head</span></div>
            </div>
          </div>
        </div>

        <!-- 死重模式：内部称重选择 -->
        <div v-if="weightType === 'dead'" class="dead-weight-section">
          <h3>Dead Weight Transaction - Internal Weighing (Optional)</h3>
          <p class="info-text">
            For dead weight transactions, the final weighing is done by the slaughterhouse after slaughter.
            You can optionally perform an internal weighing for your own tracking purposes.
          </p>
          
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="performInternalWeighing" />
              Perform internal weighing for tracking
            </label>
          </div>

          <div v-if="performInternalWeighing" class="add-weight-section">
            <h4>Internal Weight Recording</h4>
            <form @submit.prevent="handleInternalWeight">
              <div class="row">
                <div class="form-group half">
                  <label>Quantity *</label>
                  <input
                    type="number"
                    v-model.number="currentBatch.quantity"
                    required
                    min="1"
                    :max="listing?.quantity || 0"
                    placeholder="e.g. 5"
                  />
                </div>

                <div class="form-group half">
                  <label>Total Weight (kg) *</label>
                  <input
                    type="number"
                    v-model.number="currentBatch.total_weight"
                    required
                    min="0.01"
                    step="0.01"
                    placeholder="e.g. 2500.50"
                  />
                </div>
              </div>

              <button
                type="submit"
                class="btn-add-weight"
                :disabled="submitting || !canAddWeight"
              >
                {{ submitting ? 'Recording...' : 'Record Internal Weight' }}
              </button>
            </form>
          </div>

          <div v-else class="skip-section">
            <button @click="handleInternalWeight" class="btn-skip" :disabled="submitting">
              {{ submitting ? 'Processing...' : 'Skip Internal Weighing & Proceed' }}
            </button>
            <p class="hint">You can proceed directly to document upload without internal weighing.</p>
          </div>
        </div>

        <!-- 生重模式：标准称重表单 -->
        <div v-else class="add-weight-section">
          <h3>Batch #{{ nextBatchNumber }} Weighing</h3>

          <form @submit.prevent="addWeightEntry">
            <div class="row">
              <div class="form-group half">
                <label>Quantity *</label>
                <input
                  type="number"
                  v-model.number="currentBatch.quantity"
                  required
                  min="1"
                  :max="remaining"
                  placeholder="e.g. 5"
                />
                <small class="hint">Max {{ remaining }} head</small>
              </div>

              <div class="form-group half">
                <label>Total Weight (kg) *</label>
                <input
                  type="number"
                  v-model.number="currentBatch.total_weight"
                  required
                  min="0.01"
                  step="0.01"
                  placeholder="e.g. 2500.50"
                />
                <small class="hint" v-if="currentBatch.quantity && currentBatch.total_weight">
                  Avg: {{ (currentBatch.total_weight / currentBatch.quantity).toFixed(2) }} kg/head
                </small>
              </div>
            </div>

            <button
              type="submit"
              class="btn-add-weight"
              :disabled="submitting || !canAddWeight"
            >
              {{ submitting ? 'Adding...' : '+ Add Weight Record' }}
            </button>
          </form>
        </div>

        <!-- 称重记录列表 -->
        <div class="records-section">
          <h3>Weight Records ({{ weights.length }} batches)</h3>

          <div v-if="weights.length === 0" class="empty-state">
            <p>No weight records yet. Add the first batch.</p>
          </div>

          <div v-else class="records-list">
            <div
              v-for="(weight, index) in weights"
              :key="index"
              class="record-card"
            >
              <div class="record-badge">Batch #{{ weight.batch_number }}</div>

              <div class="record-details">
                <div class="record-item">
                  <span class="label">Qty:</span>
                  <span class="value">{{ weight.quantity }} head</span>
                </div>
                <div class="record-item">
                  <span class="label">Weight:</span>
                  <span class="value">{{ weight.total_weight }} kg</span>
                </div>
                <div class="record-item">
                  <span class="label">Avg:</span>
                  <span class="value">{{ (weight.total_weight / weight.quantity).toFixed(2) }} kg/head</span>
                </div>
              </div>

              <div class="record-time">
                {{ formatTime(weight.timestamp) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 完成按钮 -->
        <div v-if="isComplete" class="complete-section">
          <div class="success-msg">
            ✅ Weighing completed! You can now submit final documents.
          </div>

          <button @click="goToFinalize" class="btn-finalize">
            Submit Final Documents →
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* 复用你原有的样式变量 */
.form-page { max-width: 800px; margin: 40px auto; padding: 0 20px; font-family: 'Helvetica Neue', sans-serif; }
.back-link { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; font-size: 0.9rem; }
.form-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; }

h2 { margin-top: 0; font-weight: 300; color: #2c3e50; }
h3 { font-size: 1.1rem; color: #2c3e50; margin-bottom: 15px; }
.desc { color: #95a5a6; font-size: 0.9rem; margin-bottom: 20px; }

.progress-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; font-size: 0.9rem; }
.progress-numbers strong { font-size: 1.5rem; }

.progress-bar { width: 100%; height: 12px; background: rgba(255, 255, 255, 0.2); border-radius: 6px; overflow: hidden; margin-bottom: 20px; }
.progress-fill { height: 100%; background: white; border-radius: 6px; transition: width 0.3s ease; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
.stat-card { background: rgba(255, 255, 255, 0.15); padding: 15px; border-radius: 8px; backdrop-filter: blur(10px); }
.stat-label { font-size: 0.75rem; opacity: 0.9; margin-bottom: 5px; text-transform: uppercase; }
.stat-value { font-size: 1.5rem; font-weight: 700; }
.stat-value .unit { font-size: 0.8rem; font-weight: 400; opacity: 0.8; }

.add-weight-section { background: #f9f9f9; padding: 25px; border-radius: 12px; border: 2px dashed #ddd; margin-bottom: 30px; }
.row { display: flex; gap: 15px; margin-bottom: 15px; }
.half { flex: 1; }
.form-group { margin-bottom: 15px; }
label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.85rem; color: #34495e; }
input { width: 100%; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 1rem; background: white; box-sizing: border-box; }
.hint { font-size: 0.8rem; color: #888; margin-top: 5px; display: block; }

.btn-add-weight { width: 100%; padding: 14px; background: #9f7aea; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-add-weight:hover:not(:disabled) { background: #805ad5; }
.btn-add-weight:disabled { background: #e6b0aa; cursor: not-allowed; }

.records-section { margin-bottom: 30px; }
.empty-state { text-align: center; padding: 40px; color: #aaa; }
.records-list { display: grid; gap: 15px; }

.record-card { background: #f7fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.record-badge { background: #9f7aea; color: white; padding: 8px 15px; border-radius: 8px; font-weight: 600; white-space: nowrap; }
.record-details { flex: 1; display: flex; gap: 25px; flex-wrap: wrap; }
.record-item { display: flex; flex-direction: column; }
.record-item .label { color: #718096; font-size: 0.8rem; margin-bottom: 3px; }
.record-item .value { color: #1a202c; font-weight: 600; font-size: 1rem; }
.record-time { color: #a0aec0; font-size: 0.85rem; min-width: 150px; text-align: right; }

.complete-section { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; }
.success-msg { font-size: 1.1rem; margin-bottom: 20px; font-weight: 500; }
.btn-finalize { padding: 14px 30px; background: white; color: #38a169; border: none; border-radius: 8px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-finalize:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }

.dead-weight-section { background: #f0f4ff; padding: 25px; border-radius: 12px; border: 2px solid #9f7aea; margin-bottom: 30px; }
.dead-weight-section h3 { color: #553c9a; margin-top: 0; }
.info-text { color: #6b46c1; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.6; }
.skip-section { text-align: center; padding: 20px; }
.btn-skip { padding: 14px 30px; background: #9f7aea; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
.btn-skip:hover:not(:disabled) { background: #805ad5; }
.btn-skip:disabled { background: #c4b5fd; cursor: not-allowed; }

@media (max-width: 768px) {
  .form-page { padding: 1rem; }
  .form-container { padding: 20px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .record-card { flex-direction: column; align-items: stretch; }
  .record-details { flex-direction: column; gap: 10px; }
}
</style>