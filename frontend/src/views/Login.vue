<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!password.value) {
    error.value = '请输入密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const ok = await auth.login(password.value)
    if (ok) {
      router.push(route.query.redirect || '/')
    } else {
      error.value = '密码错误'
    }
  } catch (e) {
    error.value = e.response?.data?.message || '登录失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (route.query.code) {
    // redirect to oauth2 callback handler
  }
})
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <SvgIcon name="bot" :size="48" class="login-icon" />
        <h1 class="login-title">SkBookBot</h1>
        <p class="login-subtitle">管理面板</p>
      </div>

      <button class="win-btn win-btn-secondary oauth-btn">
        <SvgIcon name="link" :size="16" />
        使用 SkBook 账号登录
      </button>

      <div class="divider">
        <span class="divider-text">或</span>
      </div>

      <div class="win-textbox-group">
        <label class="win-textbox-label">管理员密码</label>
        <input
          v-model="password"
          type="password"
          class="win-textbox"
          placeholder="请输入管理员密码"
          @keyup.enter="handleLogin"
        />
        <span class="win-textbox-hint">用于本地管理操作验证</span>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>

      <button
        class="win-btn win-btn-primary login-submit"
        :disabled="loading"
        @click="handleLogin"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="login-footer">
        <span class="version">v1.0.0</span>
        <span class="copyright">Copyright &copy; 2026</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}

.login-card {
  width: 380px;
  padding: 32px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-icon {
  color: var(--accent);
  margin-bottom: 12px;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 4px 0;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.oauth-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.divider-text {
  padding: 0 12px;
}

.win-textbox-group {
  margin-bottom: 16px;
}

.error-text {
  color: #C42B1C;
  font-size: 13px;
  margin: 0 0 12px 0;
}

.login-submit {
  width: 100%;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>