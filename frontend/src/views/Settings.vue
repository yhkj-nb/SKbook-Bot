<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUpdateStore } from '@/store'
import { api } from '@/api'
import SvgIcon from '@/components/SvgIcon.vue'

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
const saveMessage = ref('')
const saveError = ref('')

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
  saveMessage.value = ''
  saveError.value = ''
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
      saveMessage.value = '设置已保存'
    } else {
      saveError.value = res.message || '保存失败'
    }
  } catch (e) {
    saveError.value = '保存失败: ' + (e.response?.data?.message || e.message)
  } finally {
    saving.value = false
  }
}

async function handleSavePassword() {
  if (!passwordForm.value.current) {
    saveError.value = '请输入当前密码'
    return
  }
  if (passwordForm.value.new.length < 6) {
    saveError.value = '新密码至少 6 位'
    return
  }
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    saveError.value = '两次密码输入不一致'
    return
  }
  savingPassword.value = true
  saveError.value = ''
  saveMessage.value = ''
  try {
    const res = await api.updatePassword({
      old_password: passwordForm.value.current,
      new_password: passwordForm.value.new,
    })
    if (res.success) {
      saveMessage.value = '密码已更新'
      showPasswordForm.value = false
      passwordForm.value = { current: '', new: '', confirm: '' }
      config.value.web.has_admin_password = true
    } else {
      saveError.value = res.message || '更新失败'
    }
  } catch (e) {
    saveError.value = '更新失败: ' + (e.response?.data?.message || e.message)
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="win-page-title">系统设置</h1>
    <p class="win-page-subtitle">管理框架配置</p>

    <div style="display:flex;gap:8px;margin-bottom:16px;align-items:center">
      <button class="win-btn win-btn-primary" :disabled="saving || configLoading" @click="handleSave">
        <SvgIcon name="save" :size="16" />
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>

    <div v-if="saveMessage" class="win-infobar win-infobar-success" style="margin-bottom:16px">{{ saveMessage }}</div>
    <div v-if="saveError" class="win-infobar win-infobar-danger" style="margin-bottom:16px">{{ saveError }}</div>

    <div v-if="configLoading" class="win-loading">
      <div class="win-ring"></div>
      <span>加载中...</span>
    </div>

    <template v-else>
      <!-- 服务器配置 -->
      <div class="win-card win-card-pad" style="margin-bottom:16px">
        <h2 class="win-section-title">服务器</h2>
        <div style="font-size:12px;color:var(--text-tertiary);margin-bottom:12px">需要重启生效</div>
        <div class="win-config-grid">
          <div class="win-textbox-group">
            <label class="win-textbox-label">服务器地址</label>
            <input class="win-textbox" :value="config.server.host" disabled />
            <div class="win-textbox-hint">当前监听地址</div>
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">端口</label>
            <input class="win-textbox" v-model.number="config.server.port" type="number" min="1024" max="65535" />
            <div class="win-textbox-hint">Web 管理面板访问端口</div>
          </div>
        </div>
      </div>

      <!-- 管理员密码 -->
      <div class="win-card win-card-pad" style="margin-bottom:16px">
        <h2 class="win-section-title">管理员密码</h2>
        <div style="margin-bottom:12px">
          <span v-if="config.web.has_admin_password" class="win-badge win-badge-success">已设置</span>
          <span v-else class="win-badge win-badge-danger">未设置</span>
        </div>
        <div style="margin-bottom:12px">
          <button class="win-btn win-btn-secondary win-btn-sm" @click="showPasswordForm = !showPasswordForm">
            <SvgIcon :name="showPasswordForm ? 'expand_less' : 'edit'" :size="14" />
            {{ showPasswordForm ? '收起' : (config.web.has_admin_password ? '修改密码' : '设置密码') }}
          </button>
        </div>
        <div v-if="showPasswordForm" class="win-config-grid">
          <div v-if="config.web.has_admin_password" class="win-textbox-group">
            <label class="win-textbox-label">当前密码</label>
            <input class="win-textbox" v-model="passwordForm.current" type="password" placeholder="输入当前密码" />
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">新密码</label>
            <input class="win-textbox" v-model="passwordForm.new" type="password" placeholder="至少 6 位" />
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">确认新密码</label>
            <input class="win-textbox" v-model="passwordForm.confirm" type="password" placeholder="再次输入新密码" />
          </div>
          <div style="display:flex;align-items:end">
            <button class="win-btn win-btn-primary" :disabled="savingPassword" @click="handleSavePassword">
              {{ savingPassword ? '保存中...' : '更新密码' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 机器人配置 -->
      <div class="win-card win-card-pad" style="margin-bottom:16px">
        <h2 class="win-section-title">机器人配置</h2>
        <div style="font-size:12px;color:var(--text-tertiary);margin-bottom:12px">需在配置文件中修改 Token</div>
        <div v-if="!config.bots.length" class="win-empty" style="padding:24px">
          <p>暂无机器人配置，请在 settings.yaml 中配置</p>
        </div>
        <div v-else class="win-config-grid">
          <div v-for="bot in config.bots" :key="bot.name" style="border:1px solid var(--border);border-radius:8px;padding:12px">
            <div style="font-weight:600;font-size:14px;margin-bottom:8px">{{ bot.name }}</div>
            <div class="win-textbox-group" style="margin-bottom:8px">
              <label class="win-textbox-label" style="font-size:11px">Token</label>
              <input class="win-textbox" :value="bot.token" disabled style="font-family:monospace;font-size:12px" />
            </div>
            <div class="win-textbox-group" style="margin-bottom:8px">
              <label class="win-textbox-label" style="font-size:11px">命令前缀</label>
              <input class="win-textbox" :value="bot.command_prefix" disabled />
            </div>
            <div class="win-textbox-group">
              <label class="win-textbox-label" style="font-size:11px">轮询间隔</label>
              <input class="win-textbox" :value="bot.poll_interval + 's'" disabled />
            </div>
          </div>
        </div>
      </div>

      <!-- OAuth2 配置 -->
      <div class="win-card win-card-pad" style="margin-bottom:16px">
        <h2 class="win-section-title">OAuth2 认证</h2>
        <div style="font-size:13px;color:var(--text-secondary);line-height:1.8;margin-bottom:16px">
          <p>OAuth2 用于绑定 SkBook 社区账号登录管理面板。</p>
          <p>填写回调地址为：<code style="background:var(--bg-deep);padding:2px 6px;border-radius:4px">{{ callbackUrl }}</code></p>
        </div>
        <div class="win-config-grid">
          <div class="win-textbox-group">
            <label class="win-textbox-label">CLIENT_ID</label>
            <input class="win-textbox" v-model="config.oauth2.client_id" placeholder="输入 SkBook 应用的 Client ID" />
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">CLIENT_SECRET</label>
            <input class="win-textbox" :value="config.oauth2.client_secret ? '••••••••' : ''" type="password" placeholder="需在 .env 文件中配置" disabled />
            <div class="win-textbox-hint">CLIENT_SECRET 需在 .env 文件中配置</div>
          </div>
          <div class="win-textbox-group win-config-full">
            <label class="win-textbox-label">回调地址</label>
            <input class="win-textbox" v-model="config.oauth2.redirect_uri" placeholder="如 http://localhost:5200/api/auth/oauth2/callback" />
          </div>
        </div>
      </div>

      <!-- 日志与维护 -->
      <div class="win-card win-card-pad" style="margin-bottom:16px">
        <h2 class="win-section-title">日志与维护</h2>
        <div class="win-config-grid">
          <div class="win-textbox-group">
            <label class="win-textbox-label">日志级别</label>
            <select class="win-select" v-model="config.logging.level">
              <option value="DEBUG">DEBUG - 调试</option>
              <option value="INFO">INFO - 信息</option>
              <option value="WARNING">WARNING - 警告</option>
              <option value="ERROR">ERROR - 错误</option>
            </select>
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">消息保留天数</label>
            <input class="win-textbox" v-model.number="config.services.message_cleanup_days" type="number" min="1" max="365" />
            <div class="win-textbox-hint">超过此天数的消息记录将自动清理</div>
          </div>
          <div class="win-textbox-group">
            <label class="win-textbox-label">配置热重载</label>
            <label class="win-toggle">
              <input type="checkbox" v-model="config.services.config_watcher" />
              <div class="ui-toggle-track"></div>
              <span>{{ config.services.config_watcher ? '已开启' : '已关闭' }}</span>
            </label>
            <div class="win-textbox-hint">开启后修改配置文件将自动生效</div>
          </div>
        </div>
      </div>

      <!-- 关于 -->
      <div class="win-card win-card-pad">
        <h2 class="win-section-title">关于</h2>
        <div style="font-size:13px;color:var(--text-secondary);line-height:1.8">
          <p><strong>SkBookBot</strong> {{ updateStore.currentVersion }}</p>
          <p>SkBook 开放平台机器人框架</p>
          <p style="margin-top:8px">基于 SkBook 开放平台 API 的多机器人管理框架，支持插件热加载、Web 管理面板。</p>
          <div style="display:flex;gap:16px;margin-top:12px">
            <div v-if="updateStore.updateInfo">
              <span v-if="updateStore.updateInfo.has_update" class="win-badge win-badge-warning">
                有新版本: {{ updateStore.updateInfo.latest_version }}
              </span>
              <span v-else class="win-badge win-badge-success">已是最新版本</span>
            </div>
          </div>
          <p style="margin-top:8px;font-size:12px;color:var(--text-muted)">
            API 文档：<a href="https://skbook.sk26.cn" target="_blank">https://skbook.sk26.cn</a>
          </p>
        </div>
      </div>
    </template>
  </div>
</template>