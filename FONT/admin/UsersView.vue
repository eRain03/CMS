<script setup>
import { ref, onMounted } from 'vue'

const users = ref([])
const loading = ref(true)
const selectedUser = ref(null) // 当前查看详情的用户
const showDetailModal = ref(false)

const API_BASE = 'http://43.248.188.75:38939' // 记得改为你的域名

// 加载用户列表
const loadUsers = async () => {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/admin/users`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if(res.ok) {
      const data = await res.json()
      // 为旧数据补全 is_active 字段，防止前端报错
      users.value = data.map(u => ({ ...u, is_active: u.is_active ?? true }))
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 切换状态 (激活/停用)
const toggleStatus = async (user) => {
  const action = user.is_active ? 'Deactivate' : 'Activate'
  if(!confirm(`Are you sure you want to ${action} user "${user.username}"?`)) return

  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`${API_BASE}/api/admin/user/${user.username}/toggle-status`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (res.ok) {
      // 本地更新状态，避免重新加载整个列表
      user.is_active = !user.is_active
    } else {
      const err = await res.json()
      alert(err.detail || 'Action failed')
    }
  } catch (e) {
    alert('Network error')
  }
}

// 删除用户
const deleteUser = async (username) => {
  if(!confirm(`⚠️ DANGER: Permanently delete user ${username}?`)) return
  const token = localStorage.getItem('token')
  await fetch(`${API_BASE}/api/admin/user/${username}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  })
  loadUsers()
}

// 打开详情弹窗
const openDetails = (user) => {
  selectedUser.value = user
  showDetailModal.value = true
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <h1 class="page-title">User Management</h1>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Name</th>
            <th>Role</th>
            <th>Status</th> <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.username">
            <td>
              <div class="username">{{ u.username }}</div>
              <div class="email">{{ u.email }}</div>
            </td>
            <td>{{ u.first_name }} {{ u.last_name }}</td>
            <td>
              <span class="badge" :class="u.role === 'admin' ? 'admin' : 'user'">
                {{ u.role || 'user' }}
              </span>
            </td>
            <td>
              <span class="status-dot" :class="u.is_active ? 'active' : 'inactive'">
                {{ u.is_active ? 'Active' : 'Disabled' }}
              </span>
            </td>
            <td class="text-right">
              <button class="btn-action view" @click="openDetails(u)">View</button>

              <template v-if="u.role !== 'admin'">
                <button
                  class="btn-action"
                  :class="u.is_active ? 'ban' : 'activate'"
                  @click="toggleStatus(u)"
                >
                  {{ u.is_active ? 'Block' : 'Unblock' }}
                </button>
                <button class="btn-action del" @click="deleteUser(u.username)">Del</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
      <div class="modal-card" @click.stop>
        <div class="modal-header">
          <h3>User Details</h3>
          <button class="close-btn" @click="showDetailModal = false">×</button>
        </div>

        <div class="modal-body" v-if="selectedUser">
          <div class="detail-row">
            <span class="label">Full Name:</span>
            <span class="value">{{ selectedUser.first_name }} {{ selectedUser.last_name }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Username:</span>
            <span class="value">{{ selectedUser.username }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Email:</span>
            <span class="value">{{ selectedUser.email }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Phone:</span>
            <span class="value">{{ selectedUser.phone || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Address:</span>
            <span class="value">{{ selectedUser.address || 'N/A' }}</span>
          </div>

          <hr class="divider">

          <div class="detail-row">
            <span class="label">CPF / CNPJ:</span>
            <span class="value">{{ selectedUser.tax_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">IE (State Reg):</span>
            <span class="value">{{ selectedUser.ie || '-' }}</span>
          </div>

          <div class="detail-row">
            <span class="label">Joined:</span>
            <span class="value">{{ new Date(selectedUser.created_at * 1000).toLocaleString() }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-close" @click="showDetailModal = false">Close</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.page-title { margin-bottom: 20px; font-weight: 300; color: #333; }
.table-container { background: white; padding: 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { background: #f8f9fa; color: #888; font-size: 0.8rem; text-transform: uppercase; text-align: left; padding: 15px; border-bottom: 2px solid #eee; }
td { padding: 15px; border-bottom: 1px solid #eee; vertical-align: middle; color: #333; }
tr:last-child td { border-bottom: none; }
tr:hover { background-color: #fafafa; }

.username { font-weight: 600; color: #2c3e50; }
.email { font-size: 0.8rem; color: #888; }
.text-right { text-align: right; }

/* 角色标签 */
.badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; text-transform: uppercase; font-weight: bold;}
.badge.admin { background: #2c3e50; color: white; }
.badge.user { background: #eef1f5; color: #666; }

/* 状态点 */
.status-dot { display: inline-flex; align-items: center; gap: 6px; font-size: 0.85rem; font-weight: 500; }
.status-dot::before { content: ''; width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-dot.active { color: #27ae60; }
.status-dot.active::before { background: #27ae60; }
.status-dot.inactive { color: #c0392b; }
.status-dot.inactive::before { background: #c0392b; }

/* 操作按钮 */
.btn-action { border: 1px solid transparent; background: none; cursor: pointer; padding: 4px 10px; font-size: 0.8rem; border-radius: 4px; margin-left: 5px; transition: all 0.2s; }
.btn-action.view { background: #f0f2f5; color: #333; border-color: #ddd; }
.btn-action.view:hover { border-color: #333; }
.btn-action.ban { color: #d35400; background: #fef5e7; }
.btn-action.ban:hover { background: #d35400; color: white; }
.btn-action.activate { color: #27ae60; background: #e8f8f5; }
.btn-action.activate:hover { background: #27ae60; color: white; }
.btn-action.del { color: #c0392b; }
.btn-action.del:hover { text-decoration: underline; }

/* 弹窗样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; animation: fadeIn 0.2s; }
.modal-card { background: white; width: 450px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; animation: slideUp 0.2s; }
.modal-header { padding: 20px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 1.1rem; color: #2c3e50; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999; }
.modal-body { padding: 25px; }
.detail-row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.95rem; }
.detail-row .label { color: #888; font-weight: 500; }
.detail-row .value { color: #333; font-weight: 600; text-align: right; max-width: 60%; word-break: break-word; }
.divider { border: 0; border-top: 1px dashed #eee; margin: 20px 0; }
.modal-footer { padding: 15px; text-align: right; background: #fcfcfc; border-top: 1px solid #eee; }
.btn-close { padding: 8px 20px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

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
