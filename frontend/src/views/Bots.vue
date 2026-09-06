<script setup>
import { ref, onMounted } from 'vue'
import { useBotStore } from '@/store'
import { useMessage, useDialog } from 'naive-ui'
import SvgIcon from '@/components/SvgIcon.vue'

const botStore = useBotStore()
const msg = useMessage()
const dialog = useDialog()
const loading = ref(true)

onMounted(async () => {
  await botStore.fetchBots()
  loading.value = false
})

async function handleRestart(name) {
  const res = await botStore.restartBot(name)
  if (res.success) {
    msg.success(`机器人「${name}」已重启`)
  } else {
    msg.error(res.message || '重启失败')
  }
}

function handleDelete(name) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除机器人「${name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      const res = await botStore.deleteBot(name)
      if (res.success) {
        msg.success(`机器人「${name}」已删除`)
      } else {
        msg.error(res.message || '删除失败')
      }
    },
  })
}
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="bot" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">机器人管理</h1>
          <p class="ui-page-sub">管理已配置的 SkBook 机器人</p>
        </div>
      </div>
      <div class="ui-page-actions">
        <button class="ui-btn ui-btn-ghost ui-btn-sm" @click="botStore.fetchBots()">
          <SvgIcon name="refresh" :size="16" />
          刷新
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="ui-loading">加载中...</div>

    <template v-else>
      <!-- 机器人列表 -->
      <div class="ui-card ui-card-pad">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="bot" :size="16" />
          </div>
          <span class="ui-sec-title">机器人列表</span>
        </div>

        <div v-if="botStore.bots.length">
          <div
            v-for="bot in botStore.bots"
            :key="bot.name"
            style="display: flex; align-items: center; justify-content: space-between; padding: 16px; border-bottom: 1px solid var(--border);"
            :style="{ background: bot.running ? 'var(--accent-soft)' : 'transparent' }"
          >
            <div style="display: flex; align-items: center; gap: 14px;">
              <!-- 状态指示灯 -->
              <div
                :style="{
                  width: 10, height: 10, borderRadius: '50%',
                  background: bot.running ? 'var(--success)' : 'var(--text3)',
                  boxShadow: bot.running ? '0 0 8px var(--success)' : 'none',
                  flexShrink: 0,
                }"
              ></div>
              <div>
                <div style="font-weight: 600; font-size: 15px;">{{ bot.name }}</div>
                <div style="font-size: 12px; color: var(--text3); margin-top: 2px;">
                  Token: {{ bot.token_masked }}
                </div>
              </div>
            </div>

            <div style="display: flex; align-items: center; gap: 12px;">
              <!-- 详细信息 -->
              <div style="text-align: right; font-size: 12px; color: var(--text3);">
                <div>前缀: {{ bot.command_prefix }}</div>
                <div>轮询: {{ bot.poll_interval }}s</div>
              </div>

              <!-- 操作按钮 -->
              <div style="display: flex; gap: 6px;">
                <button
                  class="ui-btn ui-btn-ghost ui-btn-sm"
                  :disabled="!bot.running"
                  @click="handleRestart(bot.name)"
                >
                  <SvgIcon name="restart" :size="14" />
                  重启
                </button>
                <button
                  class="ui-btn ui-btn-sm"
                  :class="bot.running ? 'ui-btn-danger' : 'ui-btn-success'"
                  @click="handleRestart(bot.name)"
                >
                  {{ bot.running ? '停止' : '启动' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="ui-empty">
          <SvgIcon name="bot" :size="48" />
          <p>暂无机器人</p>
          <p style="font-size: 12px; margin-top: 8px;">
            请先在配置文件 <code>bots.yaml</code> 中配置机器人信息，然后重启框架
          </p>
        </div>
      </div>

      <!-- 配置说明 -->
      <div class="ui-card ui-card-pad" style="margin-top: 16px;">
        <div class="ui-sec-head">
          <div class="ui-sec-icon">
            <SvgIcon name="info" :size="16" />
          </div>
          <span class="ui-sec-title">配置说明</span>
        </div>
        <div style="font-size: 13px; color: var(--text2); line-height: 1.8;">
          <p>机器人从 <code>bots.yaml</code> 配置文件自动加载，无需手动添加。</p>
          <p style="margin-top: 4px;">配置示例：</p>
          <pre style="background: var(--bg3); padding: 16px; border-radius: 8px; margin-top: 8px; font-size: 12px; overflow-x: auto;">
<code>bots:
  - name: my_bot
    token: "your_bot_token_here"
    command_prefix: "/"
    poll_interval: 3
    communities: []</code></pre>
        </div>
      </div>
    </template>
  </div>
</template>