<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { usePluginStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const msg = useMessage()
const pluginStore = usePluginStore()
const loading = ref(true)

onMounted(async () => {
  await pluginStore.fetchPlugins()
  loading.value = false
})

async function handleReload(name) {
  const res = await pluginStore.reloadPlugin(name)
  if (res.success) {
    msg.success(`插件「${name}」已重载`)
  } else {
    msg.error(res.message || '重载失败')
  }
}
</script>

<template>
  <div>
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="plugin" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">插件管理</h1>
          <p class="ui-page-sub">管理已加载的插件模块</p>
        </div>
      </div>
      <div class="ui-page-actions">
        <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="pluginStore.fetchPlugins()">
          <SvgIcon name="refresh" :size="16" />
          刷新
        </button>
      </div>
    </div>

    <div v-if="loading" class="ui-loading">加载中...</div>

    <template v-else>
      <div class="ui-card ui-card-pad">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="plugin" :size="16" />
          </div>
          <span class="ui-sec-title">已加载插件</span>
        </div>

        <div v-if="pluginStore.plugins.length">
          <div
            v-for="plugin in pluginStore.plugins"
            :key="plugin.name"
            style="display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid var(--border);"
          >
            <div style="display: flex; align-items: center; gap: 12px;">
              <SvgIcon name="code" :size="18" color="var(--accent)" />
              <div>
                <div style="font-weight: 600; font-size: 14px;">{{ plugin.name }}</div>
                <div style="font-size: 12px; color: var(--text3);">
                  {{ plugin.handlers }} 个处理器
                  <span v-if="plugin.has_instance" class="ui-badge ui-badge-success" style="margin-left: 6px;">有实例</span>
                  <span v-else class="ui-badge ui-badge-warning" style="margin-left: 6px;">无实例</span>
                </div>
              </div>
            </div>
            <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="handleReload(plugin.name)">
              <SvgIcon name="restart" :size="14" />
              重载
            </button>
          </div>
        </div>

        <div v-else class="ui-empty">
          <SvgIcon name="plugin" :size="48" />
          <p>暂无插件</p>
          <p style="font-size: 12px; margin-top: 8px;">将插件放置在 plugins/ 目录下即可自动加载</p>
        </div>
      </div>

      <!-- 插件开发指南 -->
      <div class="ui-card ui-card-pad" style="margin-top: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="code" :size="16" />
          </div>
          <span class="ui-sec-title">插件开发指南</span>
        </div>
        <div style="font-size: 13px; color: var(--text2); line-height: 1.8;">
          <p>创建插件文件 <code>plugins/my_plugin.py</code>：</p>
          <pre style="background: var(--bg3); padding: 16px; border-radius: 8px; margin: 8px 0; overflow-x: auto; font-size: 12px;">
<code>from core.plugin.decorators import on_command, on_message

class MyPlugin:
    _skbook_handlers = [
        {"type": "command", "name": "hello", "aliases": ["你好"]},
    ]

    def __init__(self):
        self.ctx = None

    async def on_load(self):
        self.ctx.log.info("插件已加载")

    async def hello(self, event):
        await event.reply(f"你好！你的用户ID是 {event.sender_id}")</code></pre>
        </div>
      </div>
    </template>
  </div>
</template>