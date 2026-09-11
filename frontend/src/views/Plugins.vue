<script setup>
import { ref, onMounted, computed } from 'vue'
import { usePluginStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const pluginStore = usePluginStore()
const loading = ref(true)

onMounted(async () => {
  await pluginStore.fetchPlugins()
  loading.value = false
})

const plugins = computed(() => pluginStore.plugins)

async function handleReload(name) {
  await pluginStore.reloadPlugin(name)
}
</script>

<template>
  <div>
    <h1 class="win-page-title">插件管理</h1>
    <p class="win-page-subtitle">管理已加载的插件模块</p>

    <div v-if="loading" class="win-loading">
      <div class="win-ring"></div>
      <span>加载中...</span>
    </div>

    <div v-else class="win-card win-card-pad">
      <h2 class="win-section-title">已加载插件</h2>

      <div v-if="plugins.length" class="win-list">
        <div v-for="p in plugins" :key="p.name" class="win-list-item">
          <div style="display:flex;align-items:center;gap:10px;flex:1">
            <SvgIcon name="plugins" :size="20" />
            <div class="win-list-item-content">
              <div class="win-list-item-title">{{ p.name }}</div>
              <div class="win-list-item-sub">{{ p.handlers }} 个处理器</div>
            </div>
          </div>
          <div style="display:flex;gap:6px;align-items:center">
            <span class="win-badge" :class="p.has_instance ? 'win-badge-success' : 'win-badge-warning'">
              {{ p.has_instance ? '已加载' : '未加载' }}
            </span>
            <button class="win-btn win-btn-sm win-btn-secondary" @click="handleReload(p.name)">
              重载
            </button>
          </div>
        </div>
      </div>

      <div v-else class="win-empty">
        <SvgIcon name="plugins" :size="36" />
        <p>暂无插件</p>
      </div>
    </div>
  </div>
</template>