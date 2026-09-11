<script setup>
import { computed, onMounted } from 'vue'
import { useStatsStore, useBotStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const statsStore = useStatsStore()
const botStore = useBotStore()

const loading = computed(() => statsStore.loading && botStore.loading)

const statCards = computed(() => {
  const s = statsStore.stats || {}
  return [
    { label: '机器人', icon: 'bot', value: s.bots?.total ?? 0, unit: '', colorClass: '' },
    { label: '运行中', icon: 'play', value: s.bots?.active ?? 0, unit: '', colorClass: 'c-green' },
    { label: '插件数', icon: 'plugins', value: s.plugins?.total ?? 0, unit: '', colorClass: 'c-purple' },
    { label: 'CPU', icon: 'activity', value: s.system?.cpu_percent ?? 0, unit: '%', colorClass: 'c-orange' },
    { label: '内存', icon: 'server', value: s.system?.memory_used ?? 0, unit: 'MB', colorClass: 'c-teal' },
  ]
})

function refresh() {
  statsStore.fetchStats()
  botStore.fetchBots()
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <div>
    <h1 class="win-page-title">仪表盘</h1>
    <p class="win-page-subtitle">系统运行状态概览</p>

    <div v-if="loading" class="win-loading">
      <div class="win-ring"></div>
      <span>加载中...</span>
    </div>

    <template v-else>
      <div class="win-stat-grid">
        <div v-for="card in statCards" :key="card.label" class="win-stat">
          <div class="win-stat-icon" :class="card.colorClass">
            <SvgIcon :name="card.icon" :size="18" />
          </div>
          <div class="win-stat-label">{{ card.label }}</div>
          <div class="win-stat-value">
            {{ card.value }}
            <span v-if="card.unit" class="win-stat-unit">{{ card.unit }}</span>
          </div>
        </div>
      </div>

      <div class="win-card win-card-pad">
        <h2 class="win-section-title">运行状态</h2>
        <div v-if="botStore.bots.length" class="win-list">
          <div v-for="bot in botStore.bots" :key="bot.name" class="win-list-item">
            <div style="display:flex;align-items:center;gap:8px;">
              <div
                style="width:8px;height:8px;border-radius:50%;background:var(--success)"
                v-if="bot.running"
              ></div>
              <div
                style="width:8px;height:8px;border-radius:50%;background:var(--text-tertiary)"
                v-else
              ></div>
              <div class="win-list-item-content">
                <div class="win-list-item-title">{{ bot.name }}</div>
                <div class="win-list-item-sub">前缀: {{ bot.command_prefix }}</div>
              </div>
            </div>
            <span
              class="win-badge"
              :class="bot.running ? 'win-badge-success' : 'win-badge-danger'"
            >
              {{ bot.running ? '运行中' : '已停止' }}
            </span>
          </div>
        </div>
        <div v-else class="win-empty">
          <SvgIcon name="bot" :size="36" />
          <p>暂无机器人</p>
        </div>
      </div>
    </template>
  </div>
</template>