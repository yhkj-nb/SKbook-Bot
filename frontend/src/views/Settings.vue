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
  web: { has_admin_password: false },
  logging: { level: 'INFO' },
  oauth2: { client_id: '', client_secret: false, redirect_uri: '' },
  services: { config_watcher: true, message_cleanup_days: 30 },
  bots: [],
})
const configLoading = ref(true)
const saving = ref(false)
const showPasswordForm = ref(false)
const passwordForm = ref({ current: '', new: '', confirm: '' })
const savingPassword = ref(false)

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
      'server.port': config.value.server.port,
      'oauth2.client_id': config.value.oauth2.client_id,
      'oauth2.redirect_uri': config.value.oauth2.redirect_uri,
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

async function handleSavePassword() {
  if (!passwordForm.value.current) {
    msg.warning('请输入当前密码')
    return
  }
  if (passwordForm.value.new.length < 6) {
    msg.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    msg.warning('两次密码输入不一致')
    return
  }
  savingPassword.value = true
  try {
    const res = await api.updateConfig({
      'web.admin_password': passwordForm.value.new,
    })
    if (res.success) {
      msg.success('密码已更新')
      showPasswordForm.value = false
      passwordForm.value = { current: '', new: '', confirm: '' }
      config.value.web.has_admin_password = true
    } else {
      msg.error(res.message || '更新失败')
    }
  } catch (e) {
    msg.error('更新失败: ' + (e.response?.data?.message || e.message))
  } finally {
    savingPassword.value = false
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
          <p class="ui-page-sub">管理框架配置，修改后会自动保存到配置文件</p>
        </div>
      </div>
      <div class="ui-page-actions">
        <button class="ui-btn" :disabled="saving || configLoading" @click="handleSave">
          <SvgIcon name="save" :size="16" />
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>

    <div v-if="configLoading" class="ui-loading">加载中...</div>

    <template v-else>
      <!-- 服务器配置 -->
      <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="server" :size="16" />
          </div>
          <span class="ui-sec-title">服务器</span>
          <span class="ui-sec-extra">需要重启生效</span>
        </div>
        <div class="ui-config-grid">
          <div class="ui-input-group">
            <label class="ui-input-label">服务器地址</label>
            <input class="ui-input" :value="config.server.host" disabled />
            <span class="ui-input-hint">当前监听地址</span>
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">端口</label>
            <input class="ui-input" v-model.number="config.server.port" type="number" min="1024" max="65535" />
            <span class="ui-input-hint">Web 管理面板访问端口</span>
          </div>
        </div>
      </div>

      <!-- 管理员密码 -->
      <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="lock" :size="16" />
          </div>
          <span class="ui-sec-title">管理员密码</span>
          <span class="ui-sec-extra">
            <span v-if="config.web.has_admin_password" class="ui-badge ui-badge-success">已设置</span>
            <span v-else class="ui-badge ui-badge-danger">未设置</span>
          </span>
        </div>
        <div style="margin-bottom: 12px;">
          <button class="ui-btn ui-btn-ghost" @click="showPasswordForm = !showPasswordForm">
            <SvgIcon :name="showPasswordForm ? 'chevron_up' : 'edit'" :size="16" />
            {{ showPasswordForm ? '收起' : (config.web.has_admin_password ? '修改密码' : '设置密码') }}
          </button>
        </div>
        <div v-if="showPasswordForm" class="ui-config-grid">
          <div v-if="config.web.has_admin_password" class="ui-input-group">
            <label class="ui-input-label">当前密码</label>
            <input class="ui-input" v-model="passwordForm.current" type="password" placeholder="输入当前密码" />
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">新密码</label>
            <input class="ui-input" v-model="passwordForm.new" type="password" placeholder="至少 6 位" />
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">确认新密码</label>
            <input class="ui-input" v-model="passwordForm.confirm" type="password" placeholder="再次输入新密码" />
          </div>
          <div style="display: flex; align-items: end;">
            <button class="ui-btn" :disabled="savingPassword" @click="handleSavePassword">
              {{ savingPassword ? '保存中...' : '更新密码' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 机器人配置 -->
      <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="bot" :size="16" />
          </div>
          <span class="ui-sec-title">机器人配置</span>
          <span class="ui-sec-extra">需在配置文件中修改 Token</span>
        </div>
        <div v-if="!config.bots.length" class="ui-empty" style="padding: 24px;">
          <p>暂无机器人配置，请在 settings.yaml 中配置</p>
        </div>
        <div v-else class="ui-config-grid">
          <div v-for="bot in config.bots" :key="bot.name" class="ui-config-card">
            <div class="ui-config-card-label">{{ bot.name }}</div>
            <div class="ui-input-group" style="margin-bottom: 8px;">
              <label class="ui-input-label" style="text-transform: none; font-size: 11px;">Token</label>
              <input class="ui-input" :value="bot.token" disabled style="font-family: monospace; font-size: 12px;" />
            </div>
            <div class="ui-input-group" style="margin-bottom: 8px;">
              <label class="ui-input-label" style="text-transform: none; font-size: 11px;">命令前缀</label>
              <input class="ui-input" :value="bot.command_prefix" disabled />
            </div>
            <div class="ui-input-group">
              <label class="ui-input-label" style="text-transform: none; font-size: 11px;">轮询间隔</label>
              <input class="ui-input" :value="bot.poll_interval + 's'" disabled />
            </div>
          </div>
        </div>
      </div>

      <!-- OAuth2 配置 -->
      <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="link" :size="16" />
          </div>
          <span class="ui-sec-title">OAuth2 认证</span>
        </div>
        <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.8; margin-bottom: 16px;">
          <p>OAuth2 用于绑定 SkBook 社区账号登录管理面板。</p>
          <p>填写回调地址为：<code style="background: var(--bg-deep); padding: 2px 6px; border-radius: 4px;">{{ callbackUrl }}</code></p>
        </div>
        <div class="ui-config-grid">
          <div class="ui-input-group">
            <label class="ui-input-label">CLIENT_ID</label>
            <input class="ui-input" v-model="config.oauth2.client_id" placeholder="输入 SkBook 应用的 Client ID" />
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">CLIENT_SECRET</label>
            <input class="ui-input" :value="config.oauth2.client_secret ? '••••••••' : ''" type="password" placeholder="需在 .env 文件中配置" disabled />
            <span class="ui-input-hint">CLIENT_SECRET 需在 .env 文件中配置</span>
          </div>
          <div class="ui-input-group ui-config-full">
            <label class="ui-input-label">回调地址</label>
            <input class="ui-input" v-model="config.oauth2.redirect_uri" placeholder="如 http://localhost:5200/api/auth/oauth2/callback" />
          </div>
        </div>
      </div>

      <!-- 日志与维护 -->
      <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="activity" :size="16" />
          </div>
          <span class="ui-sec-title">日志与维护</span>
        </div>
        <div class="ui-config-grid">
          <div class="ui-input-group">
            <label class="ui-input-label">日志级别</label>
            <select class="ui-input" v-model="config.logging.level">
              <option value="DEBUG">DEBUG - 调试</option>
              <option value="INFO">INFO - 信息</option>
              <option value="WARNING">WARNING - 警告</option>
              <option value="ERROR">ERROR - 错误</option>
            </select>
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">消息保留天数</label>
            <input class="ui-input" v-model.number="config.services.message_cleanup_days" type="number" min="1" max="365" />
            <span class="ui-input-hint">超过此天数的消息记录将自动清理</span>
          </div>
          <div class="ui-input-group">
            <label class="ui-input-label">配置热重载</label>
            <label class="ui-toggle">
              <input type="checkbox" v-model="config.services.config_watcher" />
              <div class="ui-toggle-track"></div>
              <span class="ui-toggle-label">{{ config.services.config_watcher ? '已开启' : '已关闭' }}</span>
            </label>
            <span class="ui-input-hint">开启后修改配置文件将自动生效</span>
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
        <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.8;">
          <p><strong>SkBookBot</strong> {{ updateStore.currentVersion }}</p>
          <p>SkBook 开放平台机器人框架</p>
          <p style="margin-top: 8px;">基于 SkBook 开放平台 API 的多机器人管理框架，支持插件热加载、Web 管理面板。</p>
          <div style="display: flex; gap: 16px; margin-top: 12px;">
            <div v-if="updateStore.updateInfo">
              <span v-if="updateStore.updateInfo.has_update" class="ui-badge ui-badge-warning">
                有新版本: {{ updateStore.updateInfo.latest_version }}
              </span>
              <span v-else class="ui-badge ui-badge-success">已是最新版本</span>
            </div>
          </div>
          <p style="margin-top: 8px; font-size: 12px; color: var(--text-muted);">
            API 文档：<a href="https://skbook.sk26.cn" target="_blank">https://skbook.sk26.cn</a>
          </p>
        </div>
      </div>
    </template>
  </div>
</template>