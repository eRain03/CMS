<script setup>
import { reactive, ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ✅ 1. 更新品种列表 (按字母顺序排序)
const breeds = [
  "Aberdeen Angus", "Brahman", "Brangus", "Charolês", "Fleckvieh", "Gir",
  "Girolando", "Guzerá", "Holandês", "Illawarra", "Jersey", "Limousin",
  "Nelore", "Nelore Pintado", "Outros", "Pardo Suíço", "Red Angus",
  "Red Brahman", "Senepol", "Simental", "Sindi", "Tabapuã", "Wagyu"
]

const form = reactive({
  type: 'slaughterhouse',
  targets: [],
  race: [], // 实际上存储的是字符串，但为了兼容 select v-model
  ageMin: null,
  ageMax: null,
  sex: 'Any',
  quantity: null,
  contact: ''
})

// 临时选择器
const tempState = ref('')
const tempCity = ref('ANY') // 默认 ANY 代表全州

const states = ref([])
const cities = ref([])
const loading = ref(false)
const loadingCities = ref(false)
const message = ref('')



// 2. 修改 onMounted，从后端获取
onMounted(async () => {
  // 并行加载：IBGE 州列表 + 我们的参考数据
  try {
    const [resIBGE, resRefs] = await Promise.all([
      fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados'),
      fetch('http://43.248.188.75:38939/api/system/references') // 你的API
    ])

    const dataIBGE = await resIBGE.json()
    states.value = dataIBGE.sort((a, b) => a.sigla.localeCompare(b.sigla))

    const dataRefs = await resRefs.json()
    breeds.value = dataRefs.breeds // ✅ 注入动态品种列表

    // 如果你想合并自定义城市到 cities 列表，逻辑会稍微复杂点
    // 这里暂时只做品种的动态化，这是最优先的

  } catch (error) {
    console.error('API Error:', error)
  }
})

// 级联加载
watch(tempState, async (newVal) => {
  tempCity.value = 'ANY'
  cities.value = []
  if (newVal) {
    loadingCities.value = true
    try {
      const res = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${newVal}/municipios`)
      const data = await res.json()
      cities.value = data.sort((a, b) => a.nome.localeCompare(b.nome))
    } catch (e) {
      console.error(e)
    } finally {
      loadingCities.value = false
    }
  }
})

// 添加区域
const addRegion = () => {
  if (!tempState.value) return

  // 防重复
  const exists = form.targets.some(t => t.state === tempState.value && t.city === tempCity.value)
  if (exists) return

  const label = tempCity.value === 'ANY'
    ? `${tempState.value} - Whole State`
    : `${tempState.value} - ${tempCity.value}`

  form.targets.push({
    state: tempState.value,
    city: tempCity.value,
    label: label
  })

  // 不重置 tempState，方便连续添加同州城市
  tempCity.value = 'ANY'
}

const removeTarget = (index) => {
  form.targets.splice(index, 1)
}

const submitForm = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    if(confirm('Authentication required. Please login first.')) router.push('/login')
    return
  }

  if (form.targets.length === 0) {
    alert('Please add at least one region.')
    return
  }

  loading.value = true

  try {
    const payload = {
      targets: form.targets.map(t => ({
        state: t.state,
        city: t.city
      })),
      race: form.race,
      ageMin: form.ageMin || 0,
      ageMax: form.ageMax || 100,
      sex: form.sex || 'Any',
      quantity: form.quantity,
      contact: form.contact
    }

    const response = await fetch('http://43.248.188.75:38939/api/buyer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })

    if (response.status === 401) {
      alert('Session expired.')
      localStorage.removeItem('token')
      router.push('/login')
      return
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      console.error('Backend validation error:', err)
      throw new Error('Submission rejected by server. Check console for details.')
    }

    const result = await response.json()
    message.value = `Request Active! Matches: ${result.matches_found}`

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
      <header>
        <h2>Slaughterhouse Request</h2>
        <p class="desc">Define specific cities or entire states.</p>
      </header>

      <form @submit.prevent="submitForm">

        <div class="form-group region-box">
          <label>Target Regions</label>
          <div class="controls">
            <select v-model="tempState" class="small-select">
              <option value="" disabled>State</option>
              <option v-for="s in states" :key="s.id" :value="s.sigla">{{ s.sigla }}</option>
            </select>
            <select v-model="tempCity" class="big-select" :disabled="!tempState">
              <option value="ANY">Whole State (All Cities)</option>
              <option v-if="loadingCities" disabled>Loading...</option>
              <option v-for="c in cities" :key="c.id" :value="c.nome">{{ c.nome }}</option>
            </select>
            <button type="button" @click="addRegion" class="btn-add" :disabled="!tempState">+</button>
          </div>

          <div class="tags-area">
            <div v-for="(t, i) in form.targets" :key="i" class="tag">
              {{ t.label }}
              <span class="remove-btn" @click="removeTarget(i)">×</span>
            </div>
          </div>
          <p class="hint" v-if="form.targets.length === 0">Add at least one region.</p>
        </div>

        <hr class="divider">

        <div class="form-group">
          <label>Required Race</label>
          <select v-model="form.race" required>
            <option disabled value="">Select Race</option>
            <option value="Any">Any Race</option>
            <option v-for="b in breeds" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>

        <div class="row">
          <div class="form-group half">
            <label>Min Age (Mo)</label>
            <input type="number" v-model.number="form.ageMin" placeholder="12" />
          </div>
          <div class="form-group half">
            <label>Max Age (Mo)</label>
            <input type="number" v-model.number="form.ageMax" placeholder="36" />
          </div>
        </div>

        <div class="row">
           <div class="form-group half">
            <label>Sex</label>
            <select v-model="form.sex">
              <option>Any</option><option>Male</option><option>Female</option><option>Steer</option>
            </select>
          </div>
          <div class="form-group half">
            <label>Min Qty</label>
            <input type="number" v-model.number="form.quantity" placeholder="100" required />
          </div>
        </div>

        <div class="form-group">
          <label>Contact</label>
          <input type="text" v-model="form.contact" placeholder="Email / Telegram" required />
        </div>

        <button type="submit" :disabled="loading" class="btn-buy">
          {{ loading ? 'Processing...' : 'Post Buy Request' }}
        </button>
      </form>

      <p v-if="message" class="success-msg">{{ message }}</p>
    </div>
  </div>
</template>

<style scoped>
/* 保持原有样式 */
.form-page { max-width: 600px; margin: 40px auto; padding: 0 20px; font-family: 'Helvetica Neue', sans-serif; }
.back-link { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; font-size: 0.9rem; }
.form-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; }
h2 { margin-top: 0; font-weight: 300; color: #2c3e50; }
.desc { color: #95a5a6; font-size: 0.9rem; margin-bottom: 20px; }
.divider { border: 0; border-top: 1px solid #f0f0f0; margin: 20px 0 30px 0; }
.form-group { margin-bottom: 25px; }
.row { display: flex; gap: 15px; }
.half { flex: 1; }
label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.85rem; color: #34495e; letter-spacing: 0.5px; }
input, select { width: 100%; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 1rem; background: #fafafa; box-sizing: border-box; }
.hint { font-size: 0.8rem; color: #bdc3c7; margin-top: 5px; }

/* 区域选择器样式 */
.region-box { background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px dashed #ddd; }
.controls { display: flex; gap: 10px; margin-bottom: 10px; }
.small-select { width: 100px; }
.big-select { flex: 1; }
.btn-add { width: 40px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1.2rem; line-height: 1; }
.btn-add:disabled { background: #e0e0e0; cursor: not-allowed; }

.tags-area { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { background: #ffebee; color: #c62828; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #ffcdd2; display: flex; align-items: center; gap: 8px; }
.remove-btn { cursor: pointer; font-weight: bold; opacity: 0.6; font-size: 1.1rem; line-height: 1; }
.remove-btn:hover { opacity: 1; }

.btn-buy { width: 100%; padding: 14px; background: #c0392b; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 10px; font-weight: 500; transition: background 0.2s; }
.btn-buy:hover { background: #e74c3c; }
.btn-buy:disabled { background: #e6b0aa; cursor: not-allowed; }
.success-msg { margin-top: 20px; padding: 12px; background: #ffebee; color: #c62828; text-align: center; border-radius: 6px; font-size: 0.9rem; }
</style>