<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const API_BASE = 'http://43.248.188.75:38939'

const listingId = route.params.id
const listing = ref(null)
const proposal = ref(null)
const weights = ref([])
const loading = ref(false)
const submitting = ref(false)
const uploading = ref(false)
const weightType = ref('live')

const formData = ref({
  yield_rate: 0.52,
  transport_fee: 0,
  funrural_tax: 0,
  nfe_document: '',
  gta_document: '',
  nfe_file: null,  // File object
  gta_file: null   // File object
})

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  loading.value = true
  const token = localStorage.getItem('token')

  try {
    // 加载列表
    const resListings = await fetch(`${API_BASE}/api/my-listings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const dataListings = await resListings.json()
    listing.value = dataListings.supply.find(l => l.id === listingId)
    if (listing.value) {
      weightType.value = listing.value.weight_type || 'live'
    }

    // 加载称重记录
    const resWeights = await fetch(`${API_BASE}/api/listings/${listingId}/weights`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const dataWeights = await resWeights.json()
    weights.value = dataWeights.data || []

    // 加载提案（从你的 proposals 系统）
    const resProposals = await fetch(`${API_BASE}/api/my-proposals`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const dataProposals = await resProposals.json()
    proposal.value = dataProposals.find(p => p.supply_id === listingId && p.status === 'PAID')

  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 计算属性
const totalWeight = computed(() => {
  return weights.value.reduce((sum, w) => sum + w.total_weight, 0)
})

const atQuantity = computed(() => {
  return totalWeight.value / 15
})

const grossAmount = computed(() => {
  if (!proposal.value) return 0
  return atQuantity.value * formData.value.yield_rate * proposal.value.price_offer
})

const finalAmount = computed(() => {
  return grossAmount.value - formData.value.transport_fee - formData.value.funrural_tax
})

// 自动计算 Funrural (0.2%)
const autoCalculateFunrural = () => {
  formData.value.funrural_tax = grossAmount.value * 0.002
}

// 文件上传处理
const handleFileUpload = (event, type) => {
  const file = event.target.files[0]
  if (file) {
    formData.value[type] = file
  }
}

// 上传文件到服务器
const uploadFile = async (fileObj) => {
  if (!fileObj) return null
  const fd = new FormData()
  fd.append('file', fileObj)
  const token = localStorage.getItem('token')
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: fd
  })
  if (!res.ok) throw new Error('File upload failed')
  const data = await res.json()
  return data.filename
}

// 提交
const handleSubmit = async () => {
  if (!formData.value.nfe_document && !formData.value.nfe_file) {
    alert('Please provide NFe document (number or file)')
    return
  }
  if (!formData.value.gta_document && !formData.value.gta_file) {
    alert('Please provide GTA document (number or file)')
    return
  }

  submitting.value = true
  uploading.value = true
  const token = localStorage.getItem('token')

  try {
    // 上传文件（如果有）
    const [nfeFileName, gtaFileName] = await Promise.all([
      formData.value.nfe_file ? uploadFile(formData.value.nfe_file) : Promise.resolve(null),
      formData.value.gta_file ? uploadFile(formData.value.gta_file) : Promise.resolve(null)
    ])

    // 准备提交数据
    const payload = {
      ...formData.value,
      nfe_file: nfeFileName,
      gta_file: gtaFileName,
      nfe_document: formData.value.nfe_document || nfeFileName,
      gta_document: formData.value.gta_document || gtaFileName
    }
    delete payload.nfe_file  // Remove file objects
    delete payload.gta_file

    const res = await fetch(`${API_BASE}/api/listings/${listingId}/finalize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '提交失败')
    }

    const result = await res.json()
    alert('✅ Documents submitted. Final amount calculated.\n\nNext: Buyer must pay final amount. We will notify them now.')
    router.push('/')

  } catch (error) {
    console.error('提交失败:', error)
    alert('提交失败: ' + error.message)
  } finally {
    submitting.value = false
    uploading.value = false
  }
}
</script>

<template>
  <div class="form-page">
    <a href="#" @click.prevent="router.push('/')" class="back-link">← Back to Home</a>

    <div class="form-container">
      <header>
        <h2>Final Settlement</h2>
        <p class="desc">Complete the transaction by submitting documents and calculating final payment.</p>
      </header>

      <div v-if="loading">Loading...</div>

      <template v-else>
        <!-- 计算摘要 -->
        <div class="calculation-box">
          <h3>💰 Payment Calculation</h3>

          <div class="calc-row">
            <span class="label">Total Weight:</span>
            <span class="value">{{ totalWeight.toFixed(2) }} kg</span>
          </div>

          <div class="calc-row">
            <span class="label">@ Quantity (÷15):</span>
            <span class="value">{{ atQuantity.toFixed(2) }} @</span>
          </div>

          <div class="calc-row">
            <span class="label">Yield Rate:</span>
            <span class="value">{{ (formData.yield_rate * 100).toFixed(0) }}%</span>
          </div>

          <div class="calc-row">
            <span class="label">Price per @:</span>
            <span class="value">R$ {{ proposal?.price_offer.toFixed(2) || '0.00' }}</span>
          </div>

          <div class="calc-row total">
            <span class="label">Gross Amount:</span>
            <span class="value">R$ {{ grossAmount.toFixed(2) }}</span>
          </div>

          <div class="calc-row deduction">
            <span class="label">- Transport Fee:</span>
            <span class="value">R$ {{ formData.transport_fee.toFixed(2) }}</span>
          </div>

          <div class="calc-row deduction">
            <span class="label">- Funrural Tax:</span>
            <span class="value">R$ {{ formData.funrural_tax.toFixed(2) }}</span>
          </div>

          <div class="calc-row final">
            <span class="label">Final Amount:</span>
            <span class="value">R$ {{ finalAmount.toFixed(2) }}</span>
          </div>
        </div>

        <hr class="divider">

        <!-- 表单 -->
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>Yield Rate (48-55%) *</label>
            <input
              type="number"
              v-model.number="formData.yield_rate"
              step="0.01"
              min="0.48"
              max="0.55"
              required
            />
            <small class="hint">Standard range: 48% - 55%</small>
          </div>

          <div class="row">
            <div class="form-group half">
              <label>Transport Fee (Optional)</label>
              <input
                type="number"
                v-model.number="formData.transport_fee"
                step="0.01"
                min="0"
                placeholder="0.00"
              />
            </div>

            <div class="form-group half">
              <label>Funrural Tax (0.2%)</label>
              <input
                type="number"
                v-model.number="formData.funrural_tax"
                step="0.01"
                min="0"
                placeholder="Auto-calculated"
              />
              <button
                type="button"
                @click="autoCalculateFunrural"
                class="btn-auto"
              >
                Auto Calculate
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>NFe Invoice *</label>
            <div class="file-upload-section">
              <input
                type="text"
                v-model="formData.nfe_document"
                placeholder="NFe-123456789 (or upload file)"
                :required="!formData.nfe_file"
              />
              <div class="file-upload-wrapper">
                <label class="file-upload-label">
                  <input
                    type="file"
                    @change="handleFileUpload($event, 'nfe_file')"
                    accept=".pdf,image/*"
                    style="display: none"
                  />
                  📄 Upload NFe File
                </label>
                <span v-if="formData.nfe_file" class="file-name">{{ formData.nfe_file.name }}</span>
              </div>
            </div>
            <small class="hint">Provide either document number or upload file (or both)</small>
          </div>

          <div class="form-group">
            <label>GTA Document *</label>
            <div class="file-upload-section">
              <input
                type="text"
                v-model="formData.gta_document"
                placeholder="GTA-987654321 (or upload file)"
                :required="!formData.gta_file"
              />
              <div class="file-upload-wrapper">
                <label class="file-upload-label">
                  <input
                    type="file"
                    @change="handleFileUpload($event, 'gta_file')"
                    accept=".pdf,image/*"
                    style="display: none"
                  />
                  📄 Upload GTA File
                </label>
                <span v-if="formData.gta_file" class="file-name">{{ formData.gta_file.name }}</span>
              </div>
            </div>
            <small class="hint">Provide either document number or upload file (or both)</small>
          </div>

          <div v-if="weightType === 'dead'" class="alert-box info">
            <p>ℹ️ <strong>Dead Weight Transaction:</strong> The final value will be calculated by the slaughterhouse after slaughter. You must still provide NF-e and GTA documents for transport.</p>
          </div>

          <div class="alert-box">
            <p>⚠️ By submitting, you confirm all information is correct.</p>
            <p>The buyer's deposit will be automatically refunded upon completion.</p>
          </div>

          <button
            type="submit"
            class="btn-submit"
            :disabled="submitting || uploading"
          >
            {{ uploading ? 'Uploading files...' : submitting ? 'Processing...' : '✅ Finalize Transaction' }}
          </button>
        </form>
      </template>
    </div>
  </div>
</template>

<style scoped>
.form-page { max-width: 700px; margin: 40px auto; padding: 0 20px; font-family: 'Helvetica Neue', sans-serif; }
.back-link { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; font-size: 0.9rem; }
.form-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; }

h2 { margin-top: 0; font-weight: 300; color: #2c3e50; }
h3 { font-size: 1.1rem; color: #2c3e50; margin-bottom: 15px; }
.desc { color: #95a5a6; font-size: 0.9rem; margin-bottom: 25px; }
.divider { border: 0; border-top: 1px solid #f0f0f0; margin: 30px 0; }

.calculation-box { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 25px; border-radius: 12px; margin-bottom: 30px; border: 2px solid #a5d6a7; }
.calculation-box h3 { margin: 0 0 20px 0; color: #2e7d32; }

.calc-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed #c8e6c9; }
.calc-row:last-child { border-bottom: none; }
.calc-row .label { color: #555; font-size: 0.95rem; }
.calc-row .value { font-weight: 600; color: #2c3e50; font-size: 1rem; }

.calc-row.total { margin-top: 10px; padding-top: 15px; border-top: 2px solid #81c784; }
.calc-row.total .value { font-size: 1.2rem; color: #2e7d32; }

.calc-row.deduction .label { color: #d32f2f; }
.calc-row.deduction .value { color: #d32f2f; }

.calc-row.final { margin-top: 10px; padding-top: 15px; border-top: 2px solid #388e3c; background: rgba(255, 255, 255, 0.5); padding: 15px 10px; border-radius: 8px; }
.calc-row.final .label { font-weight: 700; font-size: 1.1rem; color: #1b5e20; }
.calc-row.final .value { font-weight: 700; font-size: 1.5rem; color: #1b5e20; }

.row { display: flex; gap: 15px; }
.half { flex: 1; }
.form-group { margin-bottom: 20px; }
label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.85rem; color: #34495e; }
input { width: 100%; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 1rem; background: white; box-sizing: border-box; }
input:focus { border-color: #2c3e50; outline: none; }
.hint { font-size: 0.8rem; color: #888; margin-top: 5px; display: block; }

.btn-auto { margin-top: 8px; padding: 8px 12px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 6px; font-size: 0.85rem; cursor: pointer; width: 100%; }
.btn-auto:hover { background: #e0e0e0; }

.alert-box { background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 15px; margin-bottom: 25px; }
.alert-box p { margin: 5px 0; font-size: 0.9rem; color: #e65100; }
.alert-box.info { background: #e3f2fd; border-color: #64b5f6; }
.alert-box.info p { color: #1565c0; }

.file-upload-section { display: flex; flex-direction: column; gap: 10px; }
.file-upload-wrapper { display: flex; align-items: center; gap: 10px; }
.file-upload-label { padding: 8px 15px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 0.9rem; color: #555; transition: background 0.2s; }
.file-upload-label:hover { background: #e0e0e0; }
.file-name { font-size: 0.85rem; color: #27ae60; font-weight: 500; }

.btn-submit { width: 100%; padding: 16px; background: #27ae60; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-submit:hover:not(:disabled) { background: #219150; }
.btn-submit:disabled { background: #a5d6a7; cursor: not-allowed; }

@media (max-width: 768px) {
  .form-page { padding: 1rem; }
  .form-container { padding: 20px; }
  .row { flex-direction: column; gap: 0; }
}
</style>