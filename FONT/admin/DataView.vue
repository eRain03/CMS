<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const breeds = ref([])
const customCities = ref([])
const newBreed = ref('')
const newCity = ref({ state: '', name: '' })

// 巴西州列表 (硬编码即可，州通常不会变)
const states = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

const API_BASE = 'http://43.248.188.75:38939'

// 加载数据
const loadData = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/system/references`)
    const data = await res.json()
    breeds.value = data.breeds
    customCities.value = data.custom_cities
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 添加品种
const addBreed = async () => {
  if (!newBreed.value) return
  const token = localStorage.getItem('token')

  await fetch(`${API_BASE}/api/admin/breed?name=${encodeURIComponent(newBreed.value)}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  })
  newBreed.value = ''
  loadData()
}

// 删除品种
const removeBreed = async (name) => {
  if(!confirm(`Remove ${name}?`)) return
  const token = localStorage.getItem('token')
  await fetch(`${API_BASE}/api/admin/breed/${encodeURIComponent(name)}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  })
  loadData()
}

// 添加城市
const addCity = async () => {
  if (!newCity.value.state || !newCity.value.name) return
  const token = localStorage.getItem('token')

  await fetch(`${API_BASE}/api/admin/location/city`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(newCity.value)
  })
  newCity.value.name = '' // 重置名字，保留州
  loadData()
}

// 删除城市
const removeCity = async (c) => {
  if(!confirm(`Remove ${c.name}?`)) return
  const token = localStorage.getItem('token')
  await fetch(`${API_BASE}/api/admin/location/city/${c.state}/${encodeURIComponent(c.name)}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  })
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div>
    <h1 class="page-title">Data Management</h1>

    <div class="grid-layout">

      <div class="panel">
        <div class="panel-header">
          <h3>🐂 Cattle Breeds Reference</h3>
        </div>
        <div class="panel-body">
          <div class="add-box">
            <input v-model="newBreed" placeholder="New Breed Name..." @keyup.enter="addBreed" />
            <button class="btn-add" @click="addBreed">Add</button>
          </div>

          <div class="list-container">
            <div v-for="b in breeds" :key="b" class="list-item">
              <span>{{ b }}</span>
              <button class="btn-icon" @click="removeBreed(b)">×</button>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h3>🏙️ Custom Cities / Regions</h3>
          <p class="desc">Add cities missing from IBGE data.</p>
        </div>
        <div class="panel-body">
          <div class="add-box">
            <select v-model="newCity.state" class="state-select">
              <option value="" disabled>UF</option>
              <option v-for="s in states" :key="s">{{ s }}</option>
            </select>
            <input v-model="newCity.name" placeholder="City Name" @keyup.enter="addCity" />
            <button class="btn-add" @click="addCity">Add</button>
          </div>

          <div class="list-container">
            <div v-if="customCities.length === 0" class="empty">No custom cities added.</div>
            <div v-for="(c, i) in customCities" :key="i" class="list-item">
              <span><b>{{ c.state }}</b> - {{ c.name }}</span>
              <button class="btn-icon" @click="removeCity(c)">×</button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.page-title { margin-bottom: 20px; font-weight: 300; color: #333; }
.grid-layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; }

.panel { background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden; display: flex; flex-direction: column; height: 500px; }
.panel-header { background: #f8f9fa; padding: 20px; border-bottom: 1px solid #eee; }
.panel-header h3 { margin: 0; font-size: 1.1rem; color: #2c3e50; }
.desc { margin: 5px 0 0 0; font-size: 0.8rem; color: #888; }

.panel-body { padding: 20px; flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* Add Box */
.add-box { display: flex; gap: 10px; margin-bottom: 20px; }
.add-box input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
.state-select { width: 70px; padding: 10px; border: 1px solid #ddd; border-radius: 6px; background: white; }
.btn-add { background: #2c3e50; color: white; border: none; padding: 0 20px; border-radius: 6px; cursor: pointer; font-weight: 600; }

/* List */
.list-container { flex: 1; overflow-y: auto; border: 1px solid #f0f0f0; border-radius: 6px; }
.list-item { padding: 10px 15px; border-bottom: 1px solid #f9f9f9; display: flex; justify-content: space-between; align-items: center; font-size: 0.95rem; }
.list-item:last-child { border-bottom: none; }
.list-item:hover { background: #fcfcfc; }

.btn-icon { background: none; border: none; color: #c0392b; font-size: 1.2rem; cursor: pointer; font-weight: bold; line-height: 1; opacity: 0.6; }
.btn-icon:hover { opacity: 1; }
.empty { padding: 20px; text-align: center; color: #ccc; font-style: italic; }
</style>