<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useThemeStore } from '@/store/theme'
import { useAuthStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const router = useRouter()
const route = useRoute()
const themeStore = useThemeStore()
const auth = useAuthStore()
const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const showThemePicker = ref(false)

themeStore.init()

const NAV_ITEMS = [
  { label: '仪表盘', key: '/', icon: 'dashboard' },
  { label: '机器人管理', key: '/bots', icon: 'bot' },
  { label: '插件管理', key: '/plugins', icon: 'plugin' },
  { label: '消息记录', key: '/messages', icon: 'chat' },
  { label: '系统设置', key: '/settings', icon: 'settings' },
  { label: '框架更新', key: '/update', icon: 'update' },
]

const currentRoute = computed(() => route.path || '/')

function navigate(key) {
  router.push(key)
  mobileMenuOpen.value = false
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

const themeList = computed(() => Object.entries(themeStore.THEMES).map(([k, v]) => ({ key: k, name: v.name })))
</script>

<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed }">
      <div class="sidebar-header">
        <div class="logo" :class="{ 'logo-collapsed': collapsed }">
          <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#lg1)"/>
            <path d="M14 18C14 14.6863 16.6863 12 20 12H28C31.3137 12 34 14.6863 34 18V30C34 33.3137 31.3137 36 28 36H20C16.6863 36 14 33.3137 14 30V18Z" fill="white" fill-opacity="0.9"/>
            <circle cx="24" cy="29" r="3" fill="var(--accent)"/>
            <defs>
              <linearGradient id="lg1" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="var(--accent)"/><stop offset="1" stop-color="var(--accent-hover)"/>
              </linearGradient>
            </defs>
          </svg>
          <span v-if="!collapsed" class="logo-text">SkBookBot</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="item in NAV_ITEMS"
          :key="item.key"
          class="nav-item"
          :class="{ active: currentRoute === item.key }"
          @click="navigate(item.key)"
        >
          <div class="nav-icon">
            <SvgIcon :name="item.icon" :size="20" />
          </div>
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="nav-item" @click="handleLogout">
          <div class="nav-icon">
            <SvgIcon name="power" :size="20" />
          </div>
          <span v-if="!collapsed" class="nav-label">退出登录</span>
        </div>
      </div>
    </aside>

    <!-- 手机遮罩 -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>

    <!-- 主内容 -->
    <main class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <button class="menu-btn" @click="collapsed = !collapsed">
            <SvgIcon name="menu" :size="20" />
          </button>
          <span class="page-title">{{ NAV_ITEMS.find(i => i.key === currentRoute)?.label || '页面' }}</span>
        </div>
        <div class="topbar-right">
          <div class="theme-selector" @click="showThemePicker = !showThemePicker">
            <div class="color-dot" :style="{ background: themeStore.theme.accent }"></div>
            <span v-if="!collapsed" class="theme-name">{{ themeStore.themeName }}</span>
          </div>
          <button class="icon-btn" @click="themeStore.toggleDark()">
            <SvgIcon :name="themeStore.darkMode ? 'sun' : 'moon'" :size="18" />
          </button>
        </div>
      </header>

      <div class="content">
        <router-view />
      </div>
    </main>

    <!-- 主题选择器 -->
    <Teleport to="body">
      <div v-if="showThemePicker" class="theme-picker-overlay" @click="showThemePicker = false"></div>
      <div v-if="showThemePicker" class="theme-picker" @click.stop>
        <div class="theme-picker-header">选择主题</div>
        <div class="theme-picker-grid">
          <div
            v-for="t in themeList"
            :key="t.key"
            class="theme-option"
            :class="{ active: themeStore.themeName === t.key }"
            @click="themeStore.setTheme(t.key); showThemePicker = false"
          >
            <div class="theme-swatch" :style="{ background: themeStore.THEMES[t.key]?.accent || '#3b7bf7' }"></div>
            <span class="theme-option-name">{{ t.name }}</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background: var(--bg);
  color: var(--text);
}

/* ---- 侧边栏 ---- */
.sidebar {
  width: 220px;
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width .2s, margin-left .2s;
  z-index: 20;
}
.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-collapsed {
  justify-content: center;
}
.logo-text {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -.3px;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background .12s, color .12s;
  white-space: nowrap;
}
.nav-item:hover {
  background: var(--bg-deep);
  color: var(--text);
}
.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
}
.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}
.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--border);
}

/* ---- 主内容 ---- */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-btn, .icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: background .12s;
}
.menu-btn:hover, .icon-btn:hover {
  background: var(--bg-deep);
  color: var(--text);
}

.theme-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background .12s;
  font-size: 13px;
  color: var(--text-secondary);
}
.theme-selector:hover {
  background: var(--bg-deep);
}
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.theme-name {
  text-transform: capitalize;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--bg);
}

/* ---- 手机端 ---- */
.mobile-overlay {
  display: none;
}

/* ---- 主题选择器 ---- */
.theme-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0,0,0,0.3);
}
.theme-picker {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 101;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-hover);
  padding: 20px;
  width: 320px;
  max-height: 80vh;
  overflow-y: auto;
}
.theme-picker-header {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}
.theme-picker-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: background .12s;
  border: 1px solid transparent;
}
.theme-option:hover {
  background: var(--bg-deep);
}
.theme-option.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.theme-swatch {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
}
.theme-option-name {
  font-size: 13px;
  font-weight: 500;
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 30;
    margin-left: calc(-220px);
  }
  .sidebar.collapsed {
    margin-left: -60px;
  }
  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 25;
    background: rgba(0,0,0,0.3);
  }
  .content {
    padding: 16px;
  }
  .topbar {
    padding: 0 16px;
  }
}
</style>