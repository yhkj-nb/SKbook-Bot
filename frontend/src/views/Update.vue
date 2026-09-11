<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUpdateStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const updateStore = useUpdateStore()
const mirror = ref('https://api.github.com')
const message = ref('')
const msgType = ref('')

function showMsg(type, text) {
  message.value = text
  msgType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

const statCards = computed(() => [
  {
    label: '当前版本',
    value: updateStore.currentVersion,
    icon: 'tag',
    colorClass: 'c-blue',
  },
  {
    label: '最新版本',
    value: updateStore.updateInfo?.latest_version || '—',
    icon: 'download',
    colorClass: 'c-purple',
  },
  {
    label: '更新状态',
    value: updateStore.updateInfo?.has_update ? '有新版本' : '已是最新',
    icon: updateStore.updateInfo?.has_update ? 'alert' : 'check',
    colorClass: updateStore.updateInfo?.has_update ? 'c-orange' : 'c-green',
  },
  {
    label: '更新时间',
    value: updateStore.updateInfo?.release_time || '—',
    icon: 'clock',
    colorClass: 'c-teal',
  },
])

async function handleCheck() {
  await updateStore.checkUpdate()
  if (updateStore.updateInfo?.has_update) {
    showMsg('success', `发现新版本: ${updateStore.updateInfo.latest_version}`)
  } else if (updateStore.updateInfo) {
    showMsg('success', '已是最新版本')
  } else {
    showMsg('danger', '检查更新失败')
  }
}

function handleUpdate() {
  if (!updateStore.updateInfo?.has_update) {
    showMsg('warning', '当前已是最新版本')
    return
  }
  showMsg('info', '更新功能即将推出，敬请期待')
}

onMounted(() => {
  updateStore.checkUpdate()
})
</script>

<template>
  <div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
      <div>
        <h1 class="win-page-title">框架更新</h1>
        <p class="win-page-subtitle">检查并更新框架版本</p>
      </div>
      <button
        class="win-btn win-btn-primary"
        :disabled="updateStore.checking"
        @click="handleCheck"
      >
        <SvgIcon name="refresh" :size="16" />
        {{ updateStore.checking ? '检查中...' : '检查更新' }}
      </button>
    </div>

    <div v-if="message" class="win-infobar" :class="'win-infobar-' + msgType" style="margin-bottom:16px">
      {{ message }}
    </div>

    <!-- 统计卡片 -->
    <div class="win-stat-grid">
      <div v-for="card in statCards" :key="card.label" class="win-stat">
        <div class="win-stat-icon" :class="card.colorClass">
          <SvgIcon :name="card.icon" :size="18" />
        </div>
        <div class="win-stat-label">{{ card.label }}</div>
        <div class="win-stat-value">{{ card.value }}</div>
      </div>
    </div>

    <!-- 更新状态 -->
    <div class="win-card win-card-pad" style="margin-bottom:16px">
      <h2 class="win-section-title">更新状态</h2>

      <div v-if="updateStore.checking" class="win-loading">
        <div class="win-ring"></div>
        <span>正在检查更新...</span>
      </div>

      <div v-else-if="updateStore.updateInfo">
        <div
          v-if="updateStore.updateInfo.has_update"
          class="win-infobar win-infobar-warning"
          style="margin-bottom:16px"
        >
          <div>
            <strong>发现新版本 {{ updateStore.updateInfo.latest_version }}</strong>
            <div style="font-size:13px;margin-top:4px;opacity:0.8">
              当前版本: {{ updateStore.currentVersion }}
              &nbsp;|&nbsp;
              发布时间: {{ updateStore.updateInfo.release_time || '未知' }}
            </div>
          </div>
        </div>
        <div
          v-else
          class="win-infobar win-infobar-success"
          style="margin-bottom:16px"
        >
          <strong>已是最新版本</strong>
          <span style="margin-left:8px;font-size:13px;opacity:0.8">当前版本 {{ updateStore.currentVersion }} 已是最新</span>
        </div>

        <!-- 更新日志 -->
        <div v-if="updateStore.updateInfo.release_notes" style="margin-top:12px">
          <h3 style="font-size:14px;font-weight:600;margin-bottom:8px;color:var(--text)">更新日志</h3>
          <pre
            style="background:var(--bg-deep);padding:16px;border-radius:var(--radius-card);font-size:12px;white-space:pre-wrap;line-height:1.6;color:var(--text-secondary)"
          >{{ updateStore.updateInfo.release_notes }}</pre>
        </div>

        <button
          v-if="updateStore.updateInfo.has_update"
          class="win-btn win-btn-primary"
          style="margin-top:16px"
          @click="handleUpdate"
        >
          <SvgIcon name="download" :size="16" />
          立即更新到 {{ updateStore.updateInfo.latest_version }}
        </button>
      </div>

      <div v-else class="win-empty">
        <SvgIcon name="update" :size="48" />
        <p>点击「检查更新」按钮查看最新版本</p>
      </div>
    </div>

    <!-- 镜像源设置 -->
    <div class="win-card win-card-pad">
      <h2 class="win-section-title">更新镜像源</h2>
      <div style="font-size:13px;color:var(--text-secondary);line-height:1.8">
        <p style="margin-bottom:8px">从以下镜像源检查更新：</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <span
            class="win-badge"
            :class="mirror === 'https://api.github.com' ? 'win-badge-info' : 'win-badge-ghost'"
            style="cursor:pointer"
            @click="mirror = 'https://api.github.com'"
          >GitHub</span>
          <span
            class="win-badge"
            :class="mirror === 'https://gitee.com/api' ? 'win-badge-info' : 'win-badge-ghost'"
            style="cursor:pointer"
            @click="mirror = 'https://gitee.com/api'"
          >Gitee</span>
        </div>
        <p style="margin-top:12px;font-size:12px;color:var(--text-tertiary)">
          自动更新功能即将推出，当前仅支持手动检查和下载。
        </p>
      </div>
    </div>
  </div>
</template>