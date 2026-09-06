<script setup>
import { computed } from 'vue'
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
const naiveTheme = computed(() => themeStore.darkMode ? darkTheme : null)
const themeOverrides = computed(() => themeStore.naiveOverrides)
</script>

<template>
  <n-config-provider
    :theme="naiveTheme"
    :theme-overrides="themeOverrides"
    :locale="zhCN"
    :date-locale="dateZhCN"
    :inline-theme-disabled="true"
  >
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <router-view />
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
@media (max-width: 767px) {
  html, body { overflow-x: hidden; }
  input, select, textarea { font-size: 16px !important; }
}
</style>