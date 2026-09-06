<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useUpdateStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const msg = useMessage()
const updateStore = useUpdateStore()
const mirror = ref('https://api.github.com')

const statCards = computed(() => [
  { label: '当前版本', value: updateStore.currentVersion, icon: 'tag', color: 'c-blue' },
  { label: '最新版本', value: updateStore.updateInfo?.latest_version || '—', icon: 'download', color: 'c-purple' },
  { label: '更新状态', value: updateStore.updateInfo?.has_update ? '有新版本' : '已是最新', icon: updateStore.updateInfo?.has_update ? 'alert' : 'check', color: updateStore.updateInfo?.has_update ? 'c-orange' : 'c-green' },
  { label: '更新时间', value: updateStore.updateInfo?.release_time || '—', icon: 'clock', color: 'c-teal' },
])

async function handleCheck() {
  await updateStore.checkUpdate()
  if (updateStore.updateInfo?.has_update) {
    msg.success(`发现新版本: ${updateStore.updateInfo.latest_version}`)
  } else if (updateStore.updateInfo) {
    msg.success('已是最新版本')
  } else {
    msg.error('检查更新失败')
  }
}

async function handleUpdate() {
  if (!updateStore.updateInfo?.has_update) {
    msg.warning('当前已是最新版本')
    return
  }
  msg.info('更新功能即将推出，敬请期待')
}
</script>

<template>
  <div>
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="update" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">框架更新</h1>
          <p class="ui-page-sub">检查并更新框架版本</p>
        </div>
      </div>
      <div class="ui-page-actions">
        <button class="ui-btn" :disabled="updateStore.checking" @click="handleCheck">
          <SvgIcon name="refresh" :size="16" />
          {{ updateStore.checking ? '检查中...' : '检查更新' }}
        </button>
      </div>
    </div>

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

    <!-- 更新状态 -->
    <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="update" :size="16" />
        </div>
        <span class="ui-sec-title">更新状态</span>
      </div>

      <div v-if="updateStore.checking" class="ui-loading">正在检查更新...</div>

      <div v-else-if="updateStore.updateInfo">
        <div v-if="updateStore.updateInfo.has_update" style="display: flex; align-items: center; gap: 16px; padding: 16px; background: var(--accent-soft); border-radius: 10px; margin-bottom: 16px;">
          <SvgIcon name="alert" :size="32" color="var(--warning)" />
          <div>
            <div style="font-weight: 700; font-size: 15px;">发现新版本 {{ updateStore.updateInfo.latest_version }}</div>
            <div style="font-size: 13px; color: var(--text2); margin-top: 4px;">
              当前版本: {{ updateStore.currentVersion }} &nbsp;|&nbsp; 发布时间: {{ updateStore.updateInfo.release_time || '未知' }}
            </div>
          </div>
        </div>
        <div v-else style="display: flex; align-items: center; gap: 16px; padding: 16px; background: rgba(34,197,94,0.1); border-radius: 10px; margin-bottom: 16px;">
          <SvgIcon name="check" :size="32" color="var(--success)" />
          <div>
            <div style="font-weight: 700; font-size: 15px;">已是最新版本</div>
            <div style="font-size: 13px; color: var(--text2); margin-top: 4px;">当前版本 {{ updateStore.currentVersion }} 已是最新</div>
          </div>
        </div>

        <!-- 更新日志 -->
        <div v-if="updateStore.updateInfo.release_notes" style="margin-top: 12px;">
          <div class="ui-sec-head" style="margin-bottom: 8px;">
            <div class="ui-sec-icon">
              <SvgIcon name="file" :size="14" />
            </div>
            <span class="ui-sec-title" style="font-size: 14px;">更新日志</span>
          </div>
          <pre style="background: var(--bg3); padding: 16px; border-radius: 8px; font-size: 12px; white-space: pre-wrap; line-height: 1.6; color: var(--text2);">{{ updateStore.updateInfo.release_notes }}</pre>
        </div>

        <button
          v-if="updateStore.updateInfo.has_update"
          class="ui-btn"
          style="margin-top: 16px;"
          @click="handleUpdate"
        >
          <SvgIcon name="download" :size="16" />
          立即更新到 {{ updateStore.updateInfo.latest_version }}
        </button>
      </div>

      <div v-else class="ui-empty">
        <SvgIcon name="update" :size="48" />
        <p>点击「检查更新」按钮查看最新版本</p>
      </div>
    </div>

    <!-- 镜像源设置 -->
    <div class="ui-card ui-card-pad">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="server" :size="16" />
        </div>
        <span class="ui-sec-title">更新镜像源</span>
      </div>
      <div style="font-size: 13px; color: var(--text2); line-height: 1.8;">
        <p style="margin-bottom: 8px;">从以下镜像源检查更新：</p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <span
            class="ui-pill"
            :class="{ active: mirror === 'https://api.github.com' }"
            @click="mirror = 'https://api.github.com'"
          >GitHub</span>
          <span
            class="ui-pill"
            :class="{ active: mirror === 'https://gitee.com/api' }"
            @click="mirror = 'https://gitee.com/api'"
          >Gitee</span>
        </div>
        <p style="margin-top: 12px; font-size: 12px; color: var(--text3);">
          自动更新功能即将推出，当前仅支持手动检查和下载。
        </p>
      </div>
    </div>
  </div>
</template>