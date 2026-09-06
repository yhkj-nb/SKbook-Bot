<template>
  <div>
    <div class="topbar">
      <h2>系统设置</h2>
    </div>

    <div class="card">
      <div class="card-title">服务器配置</div>
      <div v-if="configLoading" class="loading">加载中...</div>
      <form v-else @submit.prevent="handleSave">
        <div class="form-group">
          <label class="form-label">服务器地址</label>
          <input v-model="config.server.host" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label class="form-label">服务器端口</label>
          <input v-model.number="config.server.port" type="number" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label class="form-label">日志级别</label>
          <select v-model="config.logging.level" class="form-input">
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">消息保留天数</label>
          <input v-model.number="config.services.message_cleanup_days" type="number" class="form-input" />
        </div>
        <div class="form-group">
          <label class="form-label">配置热重载</label>
          <select v-model="config.services.config_watcher" class="form-input">
            <option :value="true">开启</option>
            <option :value="false">关闭</option>
          </select>
        </div>
        <p v-if="saveMsg" :style="{ color: saveSuccess ? '#22C55E' : '#EF4444', fontSize: '14px', marginBottom: '12px' }">
          {{ saveMsg }}
        </p>
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </form>
    </div>

    <div class="card">
      <div class="card-title">OAuth2 配置</div>
      <div style="font-size: 14px; color: #475569; line-height: 1.8;">
        <p>OAuth2 用于绑定 SkBook 社区账号登录管理面板。</p>
        <p>配置步骤：</p>
        <ol style="padding-left: 20px; margin-top: 8px;">
          <li>在 SkBook 应用设置页中开启 OAuth2</li>
          <li>填写回调地址为：<code>{{ callbackUrl }}</code></li>
          <li>将 CLIENT_ID 和 CLIENT_SECRET 配置到 <code>.env</code> 文件中</li>
        </ol>
        <div class="form-group" style="margin-top: 16px;">
          <label class="form-label">CLIENT_ID</label>
          <input :value="config.oauth2?.client_id || '(未配置)'" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label class="form-label">回调地址</label>
          <input :value="config.oauth2?.redirect_uri || '(未配置)'" class="form-input" disabled />
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">关于</div>
      <div style="font-size: 14px; color: #475569; line-height: 1.8;">
        <p><strong>SkBookBot</strong> v1.0.0</p>
        <p>SkBook 开放平台机器人框架</p>
        <p style="margin-top: 8px;">
          基于 SkBook 开放平台 API 的多机器人管理框架，支持插件热加载、Web 管理面板。
        </p>
        <p style="margin-top: 8px; font-size: 12px; color: #94A3B8;">
          API 文档：<a href="https://skbook.sk26.cn" target="_blank">https://skbook.sk26.cn</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/api'

const config = ref({
  server: { host: '', port: 5200 },
  logging: { level: 'INFO' },
  web: { enabled: true },
  oauth2: { client_id: '', redirect_uri: '' },
  services: { config_watcher: true, message_cleanup_days: 30 },
})
const configLoading = ref(true)
const saving = ref(false)
const saveMsg = ref('')
const saveSuccess = ref(false)

const callbackUrl = computed(() => {
  const host = config.value.server.host || 'localhost'
  const port = config.value.server.port || 5200
  return `http://${host}:${port}/api/auth/oauth2/callback`
})

onMounted(async () => {
  try {
    const res = await api.getConfig()
    if (res.success) {
      config.value = res.data
    }
  } catch (e) {
    console.error('加载配置失败', e)
  } finally {
    configLoading.value = false
  }
})

async function handleSave() {
  saving.value = true
  saveMsg.value = ''
  saveSuccess.value = false
  try {
    const res = await api.updateConfig({
      'logging.level': config.value.logging.level,
      'services.message_cleanup_days': config.value.services.message_cleanup_days,
      'services.config_watcher': config.value.services.config_watcher,
    })
    if (res.success) {
      saveMsg.value = '设置已保存'
      saveSuccess.value = true
    } else {
      saveMsg.value = res.message || '保存失败'
    }
  } catch (e) {
    saveMsg.value = '保存失败: ' + (e.response?.data?.message || e.message)
  } finally {
    saving.value = false
  }
}
</script>