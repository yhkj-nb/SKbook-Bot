import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

function applyCSS(darkMode) {
  const root = document.documentElement
  if (darkMode) {
    root.style.setProperty('--bg', '#14161b')
    root.style.setProperty('--bg2', '#1c1f26')
    root.style.setProperty('--bg3', '#181b21')
    root.style.setProperty('--bg-float', '#242832')
    root.style.setProperty('--text', '#e6e9ef')
    root.style.setProperty('--text2', '#a3adbd')
    root.style.setProperty('--text3', '#6b7484')
    root.style.setProperty('--border', 'rgba(255,255,255,0.08)')
    root.style.setProperty('--shadow', '0 1px 2px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.35)')
    root.style.setProperty('--shadow-sm', '0 1px 2px rgba(0,0,0,0.3), 0 1px 3px rgba(0,0,0,0.35)')
    root.style.setProperty('--shadow-hover', '0 4px 10px rgba(0,0,0,0.35), 0 10px 24px rgba(0,0,0,0.4)')
    root.style.setProperty('--accent-soft', 'rgba(59,123,247,0.18)')
  } else {
    root.style.setProperty('--bg', '#f5f6f9')
    root.style.setProperty('--bg2', '#ffffff')
    root.style.setProperty('--bg3', '#eef0f5')
    root.style.setProperty('--bg-float', '#ffffff')
    root.style.setProperty('--text', '#1f2733')
    root.style.setProperty('--text2', '#5b6675')
    root.style.setProperty('--text3', '#97a1b0')
    root.style.setProperty('--border', 'rgba(0,0,0,0.08)')
    root.style.setProperty('--shadow', '0 1px 2px rgba(16,24,40,0.04), 0 4px 12px rgba(16,24,40,0.05)')
    root.style.setProperty('--shadow-sm', '0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)')
    root.style.setProperty('--shadow-hover', '0 4px 10px rgba(16,24,40,0.06), 0 10px 24px rgba(16,24,40,0.08)')
    root.style.setProperty('--accent-soft', 'rgba(59,123,247,0.1)')
  }
  root.style.colorScheme = darkMode ? 'dark' : 'light'
}

export const useThemeStore = defineStore('theme', () => {
  const darkMode = ref(false)
  const theme = ref('blue')

  const naiveOverrides = computed(() => ({
    common: {
      primaryColor: '#3B82F6',
      primaryColorHover: '#2563EB',
      primaryColorPressed: '#1D4ED8',
      primaryColorSuppl: '#3B82F6',
      borderRadius: '12px',
      borderRadiusSmall: '8px',
      bodyColor: 'var(--bg)',
      cardColor: 'var(--bg2)',
      borderColor: 'var(--border)',
      dividerColor: 'var(--border)',
      textColorBase: 'var(--text)',
      textColor1: 'var(--text)',
      textColor2: 'var(--text2)',
      textColor3: 'var(--text3)',
      placeholderColor: 'var(--text3)',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    },
    Card: {
      borderRadius: '12px',
    },
    Button: {
      borderRadius: '10px',
      borderRadiusSmall: '8px',
    },
    Input: {
      borderRadius: '10px',
    },
    Menu: {
      borderRadius: '8px',
    },
  }))

  function toggleDark() {
    darkMode.value = !darkMode.value
    localStorage.setItem('skbook_theme_dark', darkMode.value ? '1' : '0')
    applyCSS(darkMode.value)
  }

  function init() {
    const saved = localStorage.getItem('skbook_theme_dark')
    if (saved === '1') darkMode.value = true
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (saved === null && prefersDark) darkMode.value = true
    applyCSS(darkMode.value)
  }

  return { darkMode, theme, naiveOverrides, toggleDark, init }
})