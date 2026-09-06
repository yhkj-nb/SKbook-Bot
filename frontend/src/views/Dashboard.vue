<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js'
import { useStatsStore, useBotStore, usePluginStore, useUpdateStore } from '@/store'
import { useThemeStore } from '@/store/theme'
import SvgIcon from '@/components/SvgIcon.vue'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const statsStore = useStatsStore()
const botStore = useBotStore()
const pluginStore = usePluginStore()
const updateStore = useUpdateStore()
const themeStore = useThemeStore()

const loading = ref(true)
let refreshTimer = null

const messageTrend = ref([
  12, 8, 5, 3, 15, 28, 35, 30, 22, 18, 25, 20,
])

const statCards = computed(() => {
  const s = statsStore.stats || {}
  return [
    { label: '机器人总数', value: s.bots?.total ?? 0, icon: 'bot', color: 'c-blue', bg: 'bot' },
    { label: '运行中', value: s.bots?.active ?? 0, icon: 'activity', color: 'c-green', bg: 'activity' },
    { label: '插件数', value: s.plugins?.total ?? 0, icon: 'plugin', color: 'c-purple', bg: 'plugin' },
    { label: 'CPU 使用率', value: (s.system?.cpu_percent ?? 0) + '%', icon: 'cpu', color: 'c-orange', bg: 'cpu' },
    { label: '内存使用', value: (s.system?.memory_used ?? 0) + 'MB', icon: 'memory', color: 'c-teal', bg: 'memory' },
  ]
})

const chartData = computed(() => ({
  labels: ['00:00','02:00','04:00','06:00','08:00','10:00','12:00','14:00','16:00','18:00','20:00','22:00'],
  datasets: [{
    label: '消息数',
    data: messageTrend.value,
    borderColor: themeStore.theme.accent,
    backgroundColor: themeStore.theme.accentSoft,
    borderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 5,
    pointBackgroundColor: themeStore.theme.accent,
    tension: 0.3,
    fill: true,
  }],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: {
      grid: { color: 'rgba(128,128,128,.1)' },
      ticks: { color: 'var(--text-muted)', font: { size: 10 } },
    },
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(128,128,128,.1)' },
      ticks: { color: 'var(--text-muted)', font: { size: 11 }, precision: 0 },
    },
  },
}

function refresh() {
  Promise.all([
    statsStore.fetchStats(),
    botStore.fetchBots(),
    pluginStore.fetchPlugins(),
  ]).finally(() => { loading.value = false })
}

onMounted(() => {
  refresh()
  refreshTimer = setInterval(refresh, 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div>
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="dashboard" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">仪表盘</h1>
          <p class="ui-page-sub">系统运行状态概览</p>
        </div>
      </div>
      <div class="ui-page-actions">
        <button class="ui-btn ui-btn-ghost" @click="refresh">
          <SvgIcon name="refresh" :size="16" />
          刷新
        </button>
      </div>
    </div>

    <div v-if="loading" class="ui-loading">加载中...</div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="ui-stat-grid">
        <div v-for="card in statCards" :key="card.label" class="ui-stat" :class="card.color">
          <div class="ui-stat-top">
            <div class="ui-stat-ic">
              <SvgIcon :name="card.icon" :size="18" />
            </div>
            <span class="ui-stat-label">{{ card.label }}</span>
          </div>
          <div class="ui-stat-val">{{ card.value }}</div>
          <div class="ui-stat-bg">
            <SvgIcon :name="card.bg" :size="64" />
          </div>
        </div>
      </div>

      <!-- 机器人状态 + 消息趋势 -->
      <div class="grid-2col">
        <!-- 机器人状态 -->
        <div class="ui-card ui-card-pad">
          <div class="ui-sec-head">
            <div class="ui-sec-icon">
              <SvgIcon name="bot" :size="16" />
            </div>
            <span class="ui-sec-title">机器人状态</span>
          </div>
          <div v-if="botStore.bots.length">
            <div
              v-for="bot in botStore.bots"
              :key="bot.name"
              class="bot-item"
            >
              <div class="bot-info">
                <div class="bot-dot" :class="bot.running ? 'dot-on' : 'dot-off'"></div>
                <div>
                  <div class="bot-name">{{ bot.name }}</div>
                  <div class="bot-meta">前缀: {{ bot.command_prefix }}</div>
                </div>
              </div>
              <span class="ui-badge" :class="bot.running ? 'ui-badge-success' : 'ui-badge-danger'">
                {{ bot.running ? '运行中' : '已停止' }}
              </span>
            </div>
          </div>
          <div v-else class="ui-empty">
            <SvgIcon name="bot" :size="36" />
            <p>暂无机器人，请先在配置文件中设置</p>
          </div>
        </div>

        <!-- 消息趋势图 -->
        <div class="ui-card ui-card-pad">
          <div class="ui-sec-head">
            <div class="ui-sec-icon">
              <SvgIcon name="line_chart" :size="16" />
            </div>
            <span class="ui-sec-title">消息趋势</span>
          </div>
          <div class="chart-wrap">
            <Line v-if="!loading" :data="chartData" :options="chartOptions" />
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="ui-card ui-card-pad" style="margin-top: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="info" :size="16" />
          </div>
          <span class="ui-sec-title">系统信息</span>
        </div>
        <div class="sys-grid">
          <div>
            <span class="sys-label">框架版本</span>
            <div class="sys-value">{{ updateStore.currentVersion }}</div>
          </div>
          <div>
            <span class="sys-label">运行时间</span>
            <div class="sys-value">{{ statsStore.stats?.system?.uptime || '—' }}</div>
          </div>
          <div>
            <span class="sys-label">内存总量</span>
            <div class="sys-value">{{ (statsStore.stats?.system?.memory_total || 0) + 'MB' }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 0;
}

.bot-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.bot-item:last-child { border-bottom: none; }

.bot-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.bot-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-on {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}
.dot-off {
  background: var(--text-muted);
}
.bot-name {
  font-weight: 600;
  font-size: 14px;
}
.bot-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.chart-wrap {
  height: 180px;
  position: relative;
}

.sys-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  font-size: 13px;
}
.sys-label {
  color: var(--text-muted);
  display: block;
  margin-bottom: 2px;
}
.sys-value {
  font-weight: 600;
}

@media (max-width: 767px) {
  .grid-2col {
    grid-template-columns: 1fr;
  }
  .sys-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
</style>