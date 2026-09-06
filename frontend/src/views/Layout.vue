<script setup>
import { computed, ref, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useThemeStore } from '@/store/theme'
import { useAuthStore } from '@/store'

const router = useRouter()
const route = useRoute()
const themeStore = useThemeStore()
const auth = useAuthStore()
const collapsed = ref(false)

themeStore.init()

const menuOptions = computed(() => [
  { label: '仪表盘', key: '/', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' }),
    h('polyline', { points: '9 22 9 12 15 12 15 22' }),
  ]) },
  { label: '机器人管理', key: '/bots', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('rect', { x: 3, y: 11, width: 18, height: 10, rx: 2 }),
    h('circle', { cx: 12, cy: 5, r: 2 }),
    h('path', { d: 'M12 7v4' }),
    h('line', { x1: 8, y1: 16, x2: 8, y2: 16 }),
    h('line', { x1: 16, y1: 16, x2: 16, y2: 16 }),
  ]) },
  { label: '插件管理', key: '/plugins', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M12 2L2 7l10 5 10-5-10-5z' }),
    h('path', { d: 'M2 17l10 5 10-5' }),
    h('path', { d: 'M2 12l10 5 10-5' }),
  ]) },
  { label: '消息记录', key: '/messages', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' }),
  ]) },
  { label: '系统设置', key: '/settings', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('circle', { cx: 12, cy: 12, r: 3 }),
    h('path', { d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z' }),
  ]) },
  { label: '框架更新', key: '/update', icon: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' }),
    h('polyline', { points: '7 10 12 15 17 10' }),
    h('line', { x1: 12, y1: 15, x2: 12, y2: 3 }),
  ]) },
])

const activeKey = computed(() => route.path || '/')

function handleMenuUpdate(key) {
  router.push(key)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <n-layout class="app-layout" has-sider position="absolute">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      :collapsed="collapsed"
      :collapsed-width="64"
      :width="240"
      :native-scrollbar="false"
      class="app-sider"
      collapse-mode="width"
    >
      <div class="sider-header">
        <div class="sider-logo" v-if="!collapsed">
          <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#sg1)"/>
            <path d="M14 18C14 14.6863 16.6863 12 20 12H28C31.3137 12 34 14.6863 34 18V30C34 33.3137 31.3137 36 28 36H20C16.6863 36 14 33.3137 14 30V18Z" fill="white" fill-opacity="0.9"/>
            <path d="M20 20C20 18.8954 20.8954 18 22 18H26C27.1046 18 28 18.8954 28 20V22C28 23.1046 27.1046 24 26 24H22C20.8954 24 20 23.1046 20 22V20Z" fill="#3B82F6"/>
            <circle cx="24" cy="29" r="3" fill="#3B82F6"/>
            <defs>
              <linearGradient id="sg1" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="#3B82F6"/><stop offset="1" stop-color="#1D4ED8"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="sider-title">SkBookBot</span>
        </div>
        <div class="sider-logo collapsed-logo" v-else>
          <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#sg2)"/>
            <path d="M14 18C14 14.6863 16.6863 12 20 12H28C31.3137 12 34 14.6863 34 18V30C34 33.3137 31.3137 36 28 36H20C16.6863 36 14 33.3137 14 30V18Z" fill="white" fill-opacity="0.9"/>
            <circle cx="24" cy="29" r="3" fill="#3B82F6"/>
            <defs>
              <linearGradient id="sg2" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="#3B82F6"/><stop offset="1" stop-color="#1D4ED8"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <n-menu
        :value="activeKey"
        :options="menuOptions"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        @update:value="handleMenuUpdate"
      />

      <div class="sider-footer">
        <n-button
          quaternary
          :style="{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start' }"
          @click="handleLogout"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </template>
          <template v-if="!collapsed">退出登录</template>
        </n-button>
      </div>
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout class="app-main">
      <n-layout-header class="app-topbar" bordered>
        <div class="topbar-left">
          <n-button quaternary size="small" @click="collapsed = !collapsed" class="collapse-btn">
            <template #icon>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </template>
          </n-button>
          <n-breadcrumb>
            <n-breadcrumb-item>{{ menuOptions.find(m => m.key === activeKey)?.label || '页面' }}</n-breadcrumb-item>
          </n-breadcrumb>
        </div>
        <div class="topbar-right">
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button quaternary circle size="small" @click="themeStore.toggleDark()">
                <template #icon>
                  <svg v-if="!themeStore.darkMode" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                  </svg>
                  <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="5"/>
                    <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                    <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                  </svg>
                </template>
              </n-button>
            </template>
            {{ themeStore.darkMode ? '切换亮色模式' : '切换暗色模式' }}
          </n-tooltip>
        </div>
      </n-layout-header>

      <n-layout-content class="app-content" :native-scrollbar="false">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-sider {
  background: var(--sider-bg);
  display: flex;
  flex-direction: column;
}

.sider-header {
  padding: 16px;
  border-bottom: 1px solid var(--divider-color);
  display: flex;
  align-items: center;
}

.sider-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sider-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-color);
  letter-spacing: -0.3px;
}

.collapsed-logo {
  justify-content: center;
  width: 100%;
}

.sider-footer {
  margin-top: auto;
  padding: 12px;
  border-top: 1px solid var(--divider-color);
}

.app-main {
  display: flex;
  flex-direction: column;
}

.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 24px;
  height: 56px;
  background: var(--topbar-bg);
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

.collapse-btn {
  margin-right: 4px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-content {
  padding: 24px;
  background: transparent;
}

/* CSS 变量主题适配 */
:deep(body) {
  --sider-bg: var(--n-color);
  --divider-color: var(--n-border-color);
  --text-color: var(--n-text-color);
  --topbar-bg: var(--n-color);
}
</style>