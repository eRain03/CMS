<template>
  <div class="terminal-container">
    <div class="proposal-list">
      <div class="list-header">
        <span class="col-id">ID</span>
        <span class="col-breed">BREED(品种)</span>
        <span class="col-weight">WEIGHT(均重)</span>
        <span class="col-price">BID(出价)</span>
        <span class="col-action">OP</span>
      </div>

      <div
        v-for="item in proposals"
        :key="item.id"
        class="proposal-row"
        :class="{ 'urgent': item.isUrgent }"
      >
        <span class="col-id">#{{ item.id }}</span>
        <span class="col-breed">{{ item.breed }}</span>
        <span class="col-weight">{{ item.weight }}kg</span>
        <span class="col-price">¥{{ item.price }}</span>

        <div class="col-action">
          <button @click="openDetails(item)" class="retro-btn">
            [ 验 货 ]
          </button>
        </div>
      </div>
    </div>

    <div v-if="currentProposal" class="retro-modal-overlay" @click.self="closeDetails">
      <div class="retro-modal">
        <div class="modal-header">
          <span>>> CATTLE_MATCH_ID: {{ currentProposal.id }}</span>
          <button class="close-btn" @click="closeDetails">[ESC]</button>
        </div>

        <div class="modal-content">
          <div class="info-grid">
            <div class="field">
              <label>SELLER:</label> <span>{{ currentProposal.seller }}</span>
            </div>
            <div class="field">
              <label>LOCATION:</label> <span>{{ currentProposal.location }}</span>
            </div>
            <div class="field">
              <label>AGE:</label> <span>{{ currentProposal.age }} months</span>
            </div>
            <div class="field">
              <label>VACCINE:</label> <span :class="currentProposal.health_status === 'Clean' ? 'status-ok' : 'status-warn'">{{ currentProposal.health_status }}</span>
            </div>
          </div>

          <hr class="dashed-line">

          <div class="field-body">
            <label>>> NOTE:</label>
            <p>{{ currentProposal.description }}</p>
            <p class="meta-data">Ear_Tag_Range: {{ currentProposal.earTags }}</p>
          </div>

          <div class="calculation-box">
             <div class="calc-row"><span>UNIT PRICE:</span> <span>{{ currentProposal.unitPrice }}/kg</span></div>
             <div class="calc-row"><span>TOTAL EST:</span> <span>¥{{ currentProposal.totalPrice }}</span></div>
           </div>
        </div>

        <div class="modal-footer">
          <button class="action-btn reject">[ 驳 回 ]</button>
          <button class="action-btn accept blink-hover">[ 确认成交 ]</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// 修正后的数据：牛只匹配专用
const proposals = ref([
  {
    id: '8921',
    seller: '牧场_North_04',
    breed: 'ANGUS(安格斯)',
    weight: '450', // 均重
    price: '18,500', // 总价预估
    unitPrice: '41.2', // 单价
    totalPrice: '18,540',
    location: 'Inner Mongolia/Tongliao',
    age: '14',
    health_status: 'Clean', // 检疫状态
    earTags: 'CN2025-09001 ~ 09005',
    isUrgent: true, // 加急单
    description: '公犊牛，已做口蹄疫疫苗，骨架大，无呼吸道疾病史。买家需自提。'
  },
  {
    id: '8925',
    seller: '散户_Li',
    breed: 'SIMMENTAL(西门塔尔)',
    weight: '620',
    price: '24,000',
    unitPrice: '38.7',
    totalPrice: '23,994',
    location: 'Hebei/Chengde',
    age: '18',
    health_status: 'Pending',
    earTags: 'Unknown',
    isUrgent: false,
    description: '育肥牛，出肉率高，建议视频看牛。'
  }
]);

const currentProposal = ref(null);

const openDetails = (item) => {
  currentProposal.value = item;
};

const closeDetails = () => {
  currentProposal.value = null;
};
</script>

<style scoped>
/* 保持你的“复古精致”风格，但针对数据展示做了微调 */

:root {
  --term-bg: #111;
  --term-main: #b89c72; /* 琥珀色/复古金 */
  --term-dim: #665c4a;
  --term-highlight: #e6d3b3;
}

.terminal-container {
  font-family: 'Courier New', monospace; /* 必须是等宽字体 */
  color: var(--term-main);
  max-width: 800px;
  margin: 0 auto; /* 中心化 */
}

/* 列表头部 */
.list-header {
  display: flex;
  border-bottom: 2px solid var(--term-main);
  padding: 5px 0;
  font-weight: bold;
  font-size: 12px;
  letter-spacing: 1px;
}

.proposal-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed var(--term-dim);
  transition: all 0.2s;
}
.proposal-row:hover {
  background: rgba(184, 156, 114, 0.1);
  cursor: crosshair; /* 复古鼠标样式 */
}

/* 列宽控制 */
.col-id { width: 60px; opacity: 0.6; }
.col-breed { width: 160px; font-weight: bold; }
.col-weight { width: 100px; }
.col-price { width: 100px; }
.col-action { flex: 1; text-align: right; }

/* 按钮风格：[ 验 货 ] */
.retro-btn {
  background: transparent;
  border: none;
  color: var(--term-main);
  cursor: pointer;
  font-family: inherit;
  font-weight: bold;
}
.retro-btn:hover {
  text-decoration: underline;
  color: var(--term-highlight);
}

/* 弹窗部分 */
.retro-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.retro-modal {
  width: 550px;
  background: #000;
  border: 3px double var(--term-main); /* 双线边框 */
  box-shadow: 12px 12px 0px #222; /* 硬阴影 */
  padding: 2px;
}

.modal-header {
  background: var(--term-main);
  color: #000;
  padding: 5px 10px;
  display: flex;
  justify-content: space-between;
  font-weight: 800;
}

.modal-content {
  padding: 20px;
  font-size: 14px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.field label {
  opacity: 0.6;
  margin-right: 10px;
  font-size: 12px;
}

.dashed-line {
  border: none;
  border-top: 1px dashed var(--term-dim);
  margin: 20px 0;
}

.field-body p {
  margin: 5px 0;
  line-height: 1.5;
}
.meta-data {
  font-size: 12px;
  opacity: 0.5;
  margin-top: 10px;
}

/* 结算框风格 */
.calculation-box {
  margin-top: 20px;
  border: 1px solid var(--term-dim);
  padding: 10px;
  text-align: right;
}
.calc-row {
  display: flex;
  justify-content: space-between;
}

.modal-footer {
  padding: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 20px;
  border-top: 1px solid var(--term-dim);
}

.action-btn {
  background: transparent;
  border: 1px solid var(--term-main);
  color: var(--term-main);
  padding: 5px 15px;
  font-family: inherit;
  cursor: pointer;
}

.accept:hover {
  background: var(--term-main);
  color: #000;
}
</style>