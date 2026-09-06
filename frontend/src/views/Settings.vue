<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useUpdateStore } from '@/store'
import { api } from '@/api'
import SvgIcon from '@/components/SvgIcon.vue'

const msg = useMessage()
const updateStore = useUpdateStore()

const config = ref({
  server: { host: '', port: 5200 },
  logging: { level: 'INFO' },
  oauth2: { client_id: '', redirect_uri: '' },
  services: { config_watcher: true, message_cleanup_days: 30 },
})
const configLoading = ref(true)
const saving = ref(false)

const callbackUrl = computed(() => {
  const host = config.value.server.host || 'localhost'
  const port = config.value.server.port || 5200
  return `http://${host}:${port}/api/auth/oauth2/callback`
})

onMounted(async () => {
  try {
    const res = await api.getConfig()
    if (res.success) config.value = res.data
  } catch (e) {
    console.error('加载配置失败', e)
  } finally {
    configLoading.value = false
  }
  updateStore.checkUpdate()
})

async function handleSave() {
  saving.value = true
  try {
    const res = await api.updateConfig({
      'logging.level': config.value.logging.level,
      'services.message_cleanup_days': config.value.services.message_cleanup_days,
      'services.config_watcher': config.value.services.config_watcher,
    })
    if (res.success) {
      msg.success('设置已保存')
    } else {
      msg.error(res.message || '保存失败')
    }
  } catch (e) {
    msg.error('保存失败: ' + (e.response?.data?.message || e.message))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="settings" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">系统设置</h1>
          <p class="ui-page-sub">管理框架配置</p>
        </div>
      </div>
    </div>

    <!-- 服务器配置 -->
    <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="server" :size="16" />
        </div>
        <span class="ui-sec-title">服务器配置</span>
      </div>

      <div v-if="configLoading" class="ui-loading">加载中...</div>
      <div v-else style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">服务器地址</label>
          <n-input v-model:value="config.server.host" disabled />
        </div>
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">服务器端口</label>
          <n-input v-model:value="config.server.port" type="number" disabled />
        </div>
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">日志级别</label>
          <n-select
            v-model:value="config.logging.level"
            :options="[
              { label: 'DEBUG', value: 'DEBUG' },
              { label: 'INFO', value: 'INFO' },
              { label: 'WARNING', value: 'WARNING' },
              { label: 'ERROR', value: 'ERROR' },
            ]"
          />
        </div>
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">消息保留天数</label>
          <n-input v-model:value="config.services.message_cleanup_days" type="number" />
        </div>
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">配置热重载</label>
          <n-switch v-model:value="config.services.config_watcher" />
        </div>
      </div>

      <div style="margin-top: 16px;">
        <button class="ui-btn" :disabled="saving || configLoading" @click="handleSave">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>

    <!-- OAuth2 配置 -->
    <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="link" :size="16" />
        </div>
        <span class="ui-sec-title">OAuth2 配置</span>
      </div>
      <div style="font-size: 13px; color: var(--text2); line-height: 1.8;">
        <p>OAuth2 用于绑定 SkBook 社区账号登录管理面板。</p>
        <p style="margin-top: 4px;">配置步骤：</p>
        <ol style="padding-left: 20px; margin: 8px 0;">
          <li>在 SkBook 应用设置页中开启 OAuth2</li>
          <li>填写回调地址为：<code>{{ callbackUrl }}</code></li>
          <li>将 CLIENT_ID 和 CLIENT_SECRET 配置到 <code>.env</code> 文件中</li>
        </ol>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px;">
          <div>
            <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">CLIENT_ID</label>
            <n-input :value="config.oauth2?.client_id || '(未配置)'" disabled />
          </div>
          <div>
            <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">回调地址</label>
            <n-input :value="config.oauth2?.redirect_uri || '(未配置)'" disabled />
          </div>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div class="ui-card ui-card-pad">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="info" :size="16" />
        </div>
        <span class="ui-sec-title">关于</span>
      </div>
      <div style="font-size: 13px; color: var(--text2); line-height: 1.8;">
        <p><strong>SkBookBot</strong> {{ updateStore.currentVersion }}</p>
        <p>SkBook 开放平台机器人框架</p>
        <p style="margin-top: 8px;">
          基于 SkBook 开放平台 API 的多机器人管理框架，支持插件热加载、Web 管理面板。
        </p>
        <div style="display: flex; gap: 16px; margin-top: 12px;">
          <div v-if="updateStore.updateInfo">
            <span v-if="updateStore.updateInfo.has_update" class="ui-badge ui-badge-warning">
              有新版本: {{ updateStore.updateInfo.latest_version }}
            </span>
            <span v-else class="ui-badge ui-badge-success">已是最新版本</span>
          </div>
        </div>
        <p style="margin-top: 8px; font-size: 12px; color: var(--text3);">
          API 文档：<a href="https://skbook.sk26.cn" target="_blank">https://skbook.sk26.cn</a>
        </p>
      </div>
    </div>
  </div>
</template>