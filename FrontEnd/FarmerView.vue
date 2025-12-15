<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const API_BASE = 'http://43.248.188.75:38939'

// 1. 品种列表
const breeds = [
  "Aberdeen Angus", "Brahman", "Brangus", "Charolês", "Fleckvieh", "Gir",
  "Girolando", "Guzerá", "Holandês", "Illawarra", "Jersey", "Limousin",
  "Nelore", "Nelore Pintado", "Outros", "Pardo Suíço", "Red Angus",
  "Red Brahman", "Senepol", "Simental", "Sindi", "Tabapuã", "Wagyu"
]

// 2. 表单数据
const form = reactive({
  type: 'farmer',
  race: '',
  age: null,
  sex: 'Male (Bull)',
  quantity: null,
  state: '',
  city: '',
  contact: '',
  negotiable_date: '', // ✅ 新增：可谈判日期 (有效期)
  // New fields for enhanced sale listing
  category: '',
  estimated_weight: null,
  availability_start: '',
  availability_end: '',
  weight_type: 'live', // 'live' or 'dead'
})

// 3. 文件数据
const files = reactive({
  photo: null, // ✅ 新增：牛的照片
  nfe: null,
  gta: null
})

const states = ref([])
const cities = ref([])
const loading = ref(false)
const loadingCities = ref(false)
const message = ref('')

// --- 初始化与地理位置逻辑 (保持不变) ---
onMounted(async () => {
  try {
    const res = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados')
    const data = await res.json()
    states.value = data.sort((a, b) => a.sigla.localeCompare(b.sigla))
  } catch (error) {
    console.error('API Error (States):', error)
  }
})

watch(() => form.state, async (newState) => {
  form.city = ''
  cities.value = []
  if (!newState) return

  loadingCities.value = true
  try {
    const res = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${newState}/municipios`)
    const data = await res.json()
    cities.value = data.sort((a, b) => a.nome.localeCompare(b.nome))
  } catch (e) {
    console.error('API Error (Cities):', e)
  } finally {
    loadingCities.value = false
  }
})

// --- 4. 文件选择处理 ---
const handleFileUpload = (event, type) => {
  const file = event.target.files[0]
  if (file) {
    files[type] = file
  }
}

// --- 5. 提交逻辑 ---
const submitForm = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    if(confirm('Authentication required. Go to login?')) router.push('/login')
    return
  }
  
  if (!form.city || !form.race || !form.quantity) {
    alert('Please fill in all required fields.')
    return
  }

  loading.value = true
  message.value = ''
  
  try {
    // 辅助函数：上传单个文件
    const uploadFile = async (fileObj) => {
      if (!fileObj) return null
      const fd = new FormData()
      fd.append('file', fileObj)
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: fd
      })
      if (!res.ok) throw new Error('File upload failed')
      const data = await res.json()
      return data.filename
    }

    // A. 并行上传所有文件 (提升速度)
    const [photoName, nfeName, gtaName] = await Promise.all([
      uploadFile(files.photo), // ✅ 上传照片
      uploadFile(files.nfe),
      uploadFile(files.gta)
    ])

    // B. 提交表单
    const payload = {
      ...form,
      cattle_photo: photoName, // ✅ 关联照片文件名
      nfe_file: nfeName,
      gta_file: gtaName,
      status: 'OPEN'
    }

    const response = await fetch(`${API_BASE}/api/farmer`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    
    if (response.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      return
    }

    if (!response.ok) throw new Error('Submission failed')
    
    const result = await response.json()
    message.value = `Success! Listing ID: ${result.id}`

    setTimeout(() => router.push('/'), 1500)
    
  } catch (e) {
    console.error(e)
    message.value = 'Error: ' + e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="form-page">
    <a href="#" @click.prevent="router.push('/')" class="back-link">← Back to Home</a>
    
    <div class="form-container">
      <h2>Post Supply</h2>
      <p class="desc">Register your cattle for sale.</p>

      <form @submit.prevent="submitForm">
        
        <div class="form-group photo-upload">
          <label>📸 Cattle Photo (Main Image)</label>
          <div class="file-input-wrapper">
            <input type="file" @change="handleFileUpload($event, 'photo')" accept="image/*" />
            <span class="file-tip" v-if="files.photo">Selected: {{ files.photo.name }}</span>
          </div>
        </div>

        <hr class="divider">

        <div class="row">
          <div class="form-group half">
            <label>State (UF)</label>
            <select v-model="form.state" required class="location-select">
              <option disabled value="">Select State</option>
              <option v-for="s in states" :key="s.id" :value="s.sigla">{{ s.sigla }}</option>
            </select>
          </div>
          <div class="form-group half">
            <label>City</label>
            <select v-model="form.city" :disabled="!form.state" required class="location-select">
              <option disabled value="">{{ loadingCities ? 'Loading...' : 'Select City' }}</option>
              <option v-for="c in cities" :key="c.id" :value="c.nome">{{ c.nome }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Cattle Race</label>
          <select v-model="form.race" required>
            <option disabled value="">Select Race</option>
            <option v-for="b in breeds" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>

        <div class="row">
          <div class="form-group half">
            <label>Age (Months)</label>
            <input type="number" v-model.number="form.age" placeholder="24" required />
          </div>
          <div class="form-group half">
            <label>Quantity</label>
            <input type="number" v-model.number="form.quantity" placeholder="50" required />
          </div>
        </div>

        <div class="row">
          <div class="form-group half">
            <label>Sex</label>
            <select v-model="form.sex" required>
              <option>Male (Bull)</option>
              <option>Female (Cow)</option>
              <option>Castrated (Steer)</option>
            </select>
          </div>
          <div class="form-group half">
            <label>Category</label>
            <select v-model="form.category">
              <option value="">Select Category</option>
              <option>Beef Cattle</option>
              <option>Dairy Cattle</option>
              <option>Dual Purpose</option>
            </select>
          </div>
        </div>

        <div class="row">
          <div class="form-group half">
            <label>Weight Type *</label>
            <select v-model="form.weight_type" required>
              <option value="live">Live Weight</option>
              <option value="dead">Dead Weight (Carcass)</option>
            </select>
            <small class="hint">Live: weighed at loading. Dead: weighed after slaughter by buyer.</small>
          </div>
          <div class="form-group half">
            <label>Estimated Weight (kg)</label>
            <input type="number" v-model.number="form.estimated_weight" placeholder="Total estimated weight" step="0.01" />
          </div>
        </div>

        <div class="row">
          <div class="form-group half">
            <label>📅 Availability Start</label>
            <input type="date" v-model="form.availability_start" />
          </div>
          <div class="form-group half">
            <label>📅 Availability End</label>
            <input type="date" v-model="form.availability_end" />
          </div>
        </div>

        <div class="form-group">
          <label>Contact Info</label>
          <input type="text" v-model="form.contact" placeholder="Email / Phone" required />
        </div>

        <hr class="divider">

        <div class="file-section">
          <h3>Verification Docs (Optional)</h3>
          <p class="file-desc">Private documents for buyer verification.</p>

          <div class="form-group">
            <label>📄 NF-e (Invoice)</label>
            <input type="file" @change="handleFileUpload($event, 'nfe')" accept=".pdf,image/*" />
          </div>

          <div class="form-group">
            <label>🚛 GTA (Animal Transit)</label>
            <input type="file" @change="handleFileUpload($event, 'gta')" accept=".pdf,image/*" />
          </div>
        </div>

        <button type="submit" :disabled="loading" class="btn-submit">
          {{ loading ? 'Uploading & Posting...' : 'Post Supply' }}
        </button>
      </form>

      <p v-if="message" class="success-msg">{{ message }}</p>
    </div>
  </div>
</template>

<style scoped>
.form-page { max-width: 600px; margin: 30px auto; padding: 0 20px 80px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
.back-link { display: inline-block; margin-bottom: 20px; color: #666; text-decoration: none; font-size: 0.9rem; font-weight: 500; }
.form-container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #eee; }
h2 { margin-top: 0; font-weight: 600; color: #2c3e50; }
.desc { color: #888; font-size: 0.9rem; margin-bottom: 25px; }
.divider { border: 0; border-top: 1px solid #f0f0f0; margin: 30px 0; }

.form-group { margin-bottom: 20px; }
.row { display: flex; gap: 15px; }
.half { flex: 1; }
label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.85rem; color: #34495e; }
input[type="text"], input[type="number"], input[type="date"], select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; background: #fff; box-sizing: border-box; height: 48px; }
input:focus, select:focus { border-color: #2c3e50; outline: none; }

/* 照片上传特有样式 */
.photo-upload { background: #f8f9fa; padding: 20px; border-radius: 8px; border: 2px dashed #ddd; text-align: center; }
.file-input-wrapper { margin-top: 10px; }
.file-tip { display: block; margin-top: 8px; font-size: 0.8rem; color: #27ae60; font-weight: 600; }

.file-section h3 { font-size: 1rem; color: #2c3e50; margin-bottom: 5px; }
.file-desc { font-size: 0.8rem; color: #999; margin-bottom: 15px; }
input[type="file"] { font-size: 0.9rem; padding: 10px 0; width: 100%; }

.btn-submit { width: 100%; padding: 14px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; margin-top: 10px; font-weight: 600; transition: background 0.2s; }
.btn-submit:hover { background: #219150; }
.btn-submit:disabled { background: #a5d6a7; cursor: not-allowed; }

.success-msg { margin-top: 20px; padding: 12px; background: #e8f5e9; color: #2e7d32; text-align: center; border-radius: 6px; font-weight: 500; }

@media (max-width: 600px) {
  .row { flex-direction: column; gap: 0; }
  .form-container { padding: 20px; }
}
</style>