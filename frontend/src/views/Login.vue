<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '@/store'
import { useThemeStore } from '@/store/theme'

const router = useRouter()
const route = useRoute()
const msg = useMessage()
const auth = useAuthStore()
const themeStore = useThemeStore()

const loading = ref(false)
const password = ref('')
const currentYear = new Date().getFullYear()

// 背景粒子
const canvasRef = ref(null)
let animId = null

onMounted(() => {
  document.documentElement.classList.add('login-locked')
  themeStore.init()
  initParticles()
})

onBeforeUnmount(() => {
  document.documentElement.classList.remove('login-locked')
  if (animId) cancelAnimationFrame(animId)
})

function initParticles() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles = Array.from({ length: 60 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
    r: Math.random() * 2 + 1,
  }))

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    particles.forEach((p) => {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255,255,255,0.3)'
      ctx.fill()
    })
    // 连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(255,255,255,${0.1 * (1 - dist / 150)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }
    }
    animId = requestAnimationFrame(draw)
  }
  draw()
}

async function handleLogin() {
  if (!password.value) { msg.warning('请输入管理员密码'); return }
  loading.value = true
  try {
    const success = await auth.login(password.value)
    if (success) {
      msg.success('登录成功')
      router.push(route.query.redirect || '/')
    } else {
      msg.error('密码错误')
    }
  } catch (e) {
    msg.error(e.response?.data?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <canvas ref="canvasRef" class="login-canvas"></canvas>
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="12" fill="url(#g1)"/>
              <path d="M14 18C14 14.6863 16.6863 12 20 12H28C31.3137 12 34 14.6863 34 18V30C34 33.3137 31.3137 36 28 36H20C16.6863 36 14 33.3137 14 30V18Z" fill="white" fill-opacity="0.9"/>
              <path d="M20 20C20 18.8954 20.8954 18 22 18H26C27.1046 18 28 18.8954 28 20V22C28 23.1046 27.1046 24 26 24H22C20.8954 24 20 23.1046 20 22V20Z" fill="#3B82F6"/>
              <circle cx="24" cy="29" r="3" fill="#3B82F6"/>
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#3B82F6"/>
                  <stop offset="1" stop-color="#1D4ED8"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 class="login-title">SkBookBot</h1>
          <p class="login-subtitle">管理面板</p>
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <div class="input-group">
            <label class="input-label">管理员密码</label>
            <n-input
              v-model:value="password"
              type="password"
              placeholder="请输入管理员密码"
              size="large"
              :disabled="loading"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0110 0v4"/>
                </svg>
              </template>
            </n-input>
          </div>

          <n-button
            type="primary"
            size="large"
            block
            :loading="loading"
            :disabled="loading"
            @click="handleLogin"
            class="login-btn"
          >
            登 录
          </n-button>
        </form>

        <div class="login-footer">
          <span class="version">v1.0.0</span>
          <span class="copyright">&copy; {{ currentYear }} SkBookBot</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
  overflow: hidden;
}

.login-canvas {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 1;
}

.login-bg-shapes {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.shape-1 {
  width: 400px; height: 400px;
  background: #3B82F6;
  top: -100px; right: -100px;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 300px; height: 300px;
  background: #8B5CF6;
  bottom: -50px; left: -50px;
  animation: float 10s ease-in-out infinite reverse;
}

.shape-3 {
  width: 200px; height: 200px;
  background: #3B82F6;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: float 12s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

.login-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 40px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  margin-bottom: 16px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
  letter-spacing: -0.5px;
}

.login-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

.input-group {
  margin-bottom: 20px;
}

.input-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.login-btn {
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 10px;
  margin-top: 4px;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}

:deep(.n-input) {
  --n-border-radius: 10px;
}

:deep(.n-input .n-input__input-el) {
  color: #fff !important;
}

:deep(.n-input .n-input__prefix) {
  color: rgba(255, 255, 255, 0.4);
}
</style>