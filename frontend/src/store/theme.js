import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

function shade(hex, pct) {
  const n = parseInt(hex.slice(1), 16)
  const f = c => Math.max(0, Math.min(255, Math.round(pct >= 0 ? c + (255 - c) * pct : c * (1 + pct))))
  const [r, g, b] = [f(n >> 16 & 255), f(n >> 8 & 255), f(n & 255)]
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')
}

const THEMES = {
  discord: {
    name: '清新蓝',
    bg: '#f4f6fb', bgPanel: '#ffffff', bgDeep: '#f1f4f9', bgFloat: '#ffffff',
    text: '#1f2733', textSecondary: '#5b6675', textMuted: '#97a1b0',
    border: '#eef1f6',
    accent: '#3b7bf7', accentHover: '#2f6ae0', accentLight: '#6fa0fb',
    accentSoft: 'rgba(59, 123, 247, 0.1)',
    success: '#22c55e', danger: '#ef4444', warning: '#f59e0b', info: '#3b7bf7',
  },
  dark: {
    name: '石墨灰',
    bg: '#f5f6f8', bgPanel: '#ffffff', bgDeep: '#eef0f3', bgFloat: '#ffffff',
    text: '#1c2128', textSecondary: '#57606a', textMuted: '#8a93a0',
    border: '#eceef1',
    accent: '#2f6feb', accentHover: '#1f5fd8', accentLight: '#6398f5',
    accentSoft: 'rgba(47, 111, 235, 0.1)',
    success: '#2ea043', danger: '#e5484d', warning: '#d29922', info: '#2f6feb',
  },
  midnight: {
    name: '梦幻紫',
    bg: '#f8f6fe', bgPanel: '#ffffff', bgDeep: '#f3effb', bgFloat: '#ffffff',
    text: '#2a2150', textSecondary: '#6b5f93', textMuted: '#a094c0',
    border: '#efeafa',
    accent: '#7c5cf6', accentHover: '#6a49ee', accentLight: '#a48ff9',
    accentSoft: 'rgba(124, 92, 246, 0.1)',
    success: '#22c55e', danger: '#ef4444', warning: '#f59e0b', info: '#7c5cf6',
  },
  sakura: { name: '樱花粉', ...shadeTheme('#f472b6') },
  rose: { name: '玫瑰红', ...shadeTheme('#e11d48') },
  forest: { name: '森林绿', ...shadeTheme('#16a34a') },
  emerald: { name: '翡翠绿', ...shadeTheme('#10b981') },
  teal: { name: '青碧', ...shadeTheme('#0d9488') },
  cyan: { name: '湖水青', ...shadeTheme('#06b6d4') },
  sky: { name: '天空蓝', ...shadeTheme('#0ea5e9') },
  indigo: { name: '深靛蓝', ...shadeTheme('#4f46e5') },
  grape: { name: '葡萄紫', ...shadeTheme('#9333ea') },
  orange: { name: '活力橙', ...shadeTheme('#f97316') },
}

function shadeTheme(accent) {
  const n = parseInt(accent.slice(1), 16)
  return {
    bg: '#f5f6f9', bgPanel: '#ffffff', bgDeep: '#eef0f5', bgFloat: '#ffffff',
    text: '#1f2733', textSecondary: '#5b6675', textMuted: '#97a1b0',
    border: '#eef1f6',
    accent, accentHover: shade(accent, -0.15), accentLight: shade(accent, 0.25),
    accentSoft: `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, 0.1)`,
    success: '#22c55e', danger: '#ef4444', warning: '#f59e0b', info: accent,
  }
}

function darkVariant(t) {
  return {
    ...t,
    bg: '#14161b', bgPanel: '#1c1f26', bgDeep: '#181b21', bgFloat: '#242832',
    text: '#e6e9ef', textSecondary: '#a3adbd', textMuted: '#6b7484',
    border: '#2a2f3a',
    accentSoft: t.accentSoft.replace('0.1)', '0.18)'),
  }
}

function applyCSS(t) {
  const s = document.documentElement.style
  Object.entries(t).forEach(([k, v]) => {
    if (['name'].includes(k)) return
    s.setProperty('--' + k.replace(/[A-Z]/g, c => '-' + c.toLowerCase()), v)
  })
  s.setProperty('--radius', '16px')
  s.setProperty('--radius-sm', '10px')
  const isDark = parseInt(t.bg.slice(1, 3), 16) < 30
  if (isDark) {
    s.setProperty('--shadow', '0 1px 2px rgba(0,0,0,.3), 0 4px 12px rgba(0,0,0,.35)')
    s.setProperty('--shadow-sm', '0 1px 2px rgba(0,0,0,.3), 0 1px 3px rgba(0,0,0,.35)')
    s.setProperty('--shadow-hover', '0 4px 10px rgba(0,0,0,.35), 0 10px 24px rgba(0,0,0,.4)')
  } else {
    s.setProperty('--shadow', '0 1px 2px rgba(16,24,40,.04), 0 4px 12px rgba(16,24,40,.05)')
    s.setProperty('--shadow-sm', '0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06)')
    s.setProperty('--shadow-hover', '0 4px 10px rgba(16,24,40,.06), 0 10px 24px rgba(16,24,40,.08)')
  }
  document.documentElement.style.colorScheme = isDark ? 'dark' : 'light'
}

export const useThemeStore = defineStore('theme', () => {
  const themeName = ref(localStorage.getItem('skbook_theme') || 'discord')
  const darkMode = ref(localStorage.getItem('skbook_dark') === '1')

  const theme = computed(() => {
    const t = THEMES[themeName.value] || THEMES.discord
    return darkMode.value ? darkVariant(t) : t
  })

  const naiveOverrides = computed(() => {
    const t = theme.value
    return {
      common: {
        primaryColor: t.accent, primaryColorHover: t.accentLight,
        primaryColorPressed: t.accentHover, primaryColorSuppl: t.accentLight,
        bodyColor: t.bg, baseColor: t.bgPanel, cardColor: t.bgPanel,
        modalColor: t.bgPanel, popoverColor: t.bgFloat,
        tableColor: t.bgPanel, tableColorHover: t.bgDeep,
        inputColor: t.bgPanel, inputColorDisabled: t.bgDeep,
        actionColor: t.bgDeep, tagColor: t.bgDeep,
        borderColor: t.border, dividerColor: t.border, hoverColor: t.bgDeep,
        textColorBase: t.text, textColor1: t.text,
        textColor2: t.textSecondary, textColor3: t.textMuted,
        placeholderColor: t.textMuted,
        successColor: t.success, errorColor: t.danger,
        warningColor: t.warning, infoColor: t.info,
        borderRadius: '12px', borderRadiusSmall: '8px',
      },
      Card: { colorEmbedded: t.bgDeep },
      DataTable: { thColor: t.bgDeep, tdColorHover: t.bgDeep },
      Menu: { itemTextColor: t.text, itemTextColorHover: t.accent, itemColorActive: t.bgDeep },
      Input: { color: t.bgPanel, colorFocus: t.bgFloat, textColor: t.text },
      Tag: { textColor: t.textSecondary },
    }
  })

  function toggleDark(event) {
    darkMode.value = !darkMode.value
    localStorage.setItem('skbook_dark', darkMode.value ? '1' : '0')
    applyCSS(theme.value)
  }

  function setTheme(name) {
    themeName.value = name
    localStorage.setItem('skbook_theme', name)
    applyCSS(theme.value)
  }

  function init() {
    const saved = localStorage.getItem('skbook_dark')
    if (saved === '1') darkMode.value = true
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (saved === null && prefersDark) darkMode.value = true
    applyCSS(theme.value)
  }

  return { themeName, darkMode, theme, naiveOverrides, toggleDark, setTheme, init, THEMES }
})