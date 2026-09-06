<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStatsStore, useBotStore, usePluginStore, useUpdateStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const statsStore = useStatsStore()
const botStore = useBotStore()
const pluginStore = usePluginStore()
const updateStore = useUpdateStore()

const loading = ref(true)
let refreshTimer = null

// 模拟消息趋势数据（实际可从后端获取）
const messageTrend = ref([
  { time: '00:00', count: 12 }, { time: '02:00', count: 8 }, { time: '04:00', count: 5 },
  { time: '06:00', count: 3 }, { time: '08:00', count: 15 }, { time: '10:00', count: 28 },
  { time: '12:00', count: 35 }, { time: '14:00', count: 30 }, { time: '16:00', count: 22 },
  { time: '18:00', count: 18 }, { time: '20:00', count: 25 }, { time: '22:00', count: 20 },
])

const statCards = computed(() => {
  const s = statsStore.stats || {}
  return [
    { label: '机器人总数', value: s.bots?.total ?? 0, icon: 'bot', color: 'c-blue' },
    { label: '运行中', value: s.bots?.active ?? 0, icon: 'activity', color: 'c-green' },
    { label: '插件数', value: s.plugins?.total ?? 0, icon: 'plugin', color: 'c-purple' },
    { label: 'CPU 使用率', value: (s.system?.cpu_percent ?? 0) + '%', icon: 'cpu', color: 'c-orange' },
    { label: '内存使用', value: (s.system?.memory_used ?? 0) + 'MB', icon: 'memory', color: 'c-teal' },
  ]
})

const maxMsgCount = computed(() => Math.max(...messageTrend.value.map(m => m.count), 1))

function init() {
  refresh()
  refreshTimer = setInterval(refresh, 15000)
}

function refresh() {
  Promise.all([
    statsStore.fetchStats(),
    botStore.fetchBots(),
    pluginStore.fetchPlugins(),
  ]).finally(() => { loading.value = false })
}

onMounted(init)
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div>
    <!-- 页面头部 -->
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
        <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="refresh">
          <SvgIcon name="refresh" :size="16" />
          刷新
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
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
            <SvgIcon :name="card.icon" :size="64" />
          </div>
        </div>
      </div>

      <!-- 机器人状态 + 消息趋势 -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 22px;">
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
              style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border);"
            >
              <div style="display: flex; align-items: center; gap: 10px;">
                <SvgIcon name="bot" :size="18" :color="bot.running ? 'var(--success)' : 'var(--text3)'" />
                <div>
                  <div style="font-weight: 600; font-size: 14px;">{{ bot.name }}</div>
                  <div style="font-size: 12px; color: var(--text3);">前缀: {{ bot.command_prefix }}</div>
                </div>
              </div>
              <span class="ui-badge" :class="bot.running ? 'ui-badge-success' : 'ui-badge-danger'">
                {{ bot.running ? '运行中' : '已停止' }}
              </span>
            </div>
          </div>
          <div v-else class="ui-empty" style="padding: 20px;">
            <SvgIcon name="bot" :size="32" />
            <p>暂无机器人，请在设置中配置</p>
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
          <div style="height: 180px; display: flex; align-items: flex-end; gap: 6px; padding: 10px 0;">
            <div
              v-for="(item, idx) in messageTrend"
              :key="idx"
              style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;"
            >
              <div
                :style="{
                  height: (item.count / maxMsgCount * 120) + 'px',
                  width: '100%',
                  background: 'var(--accent)',
                  borderRadius: '4px 4px 0 0',
                  opacity: 0.6 + (item.count / maxMsgCount) * 0.4,
                  transition: 'height .3s',
                }"
              ></div>
              <span style="font-size: 10px; color: var(--text3); transform: rotate(-45deg); white-space: nowrap;">
                {{ item.time }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="ui-card ui-card-pad">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="info" :size="16" />
          </div>
          <span class="ui-sec-title">系统信息</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; font-size: 13px;">
          <div>
            <span style="color: var(--text3);">框架版本</span>
            <div style="font-weight: 600; margin-top: 2px;">{{ updateStore.currentVersion }}</div>
          </div>
          <div>
            <span style="color: var(--text3);">运行时间</span>
            <div style="font-weight: 600; margin-top: 2px;">{{ statsStore.stats?.system?.uptime || '—' }}</div>
          </div>
          <div>
            <span style="color: var(--text3);">内存总量</span>
            <div style="font-weight: 600; margin-top: 2px;">{{ (statsStore.stats?.system?.memory_total || 0) + 'MB' }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>