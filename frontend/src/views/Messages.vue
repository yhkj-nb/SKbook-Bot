<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useBotStore } from '@/store'
import { api } from '@/api'
import SvgIcon from '@/components/SvgIcon.vue'

const msg = useMessage()
const botStore = useBotStore()

// 发送消息
const sendForm = ref({ community_id: '', channel_id: '', content: '', bot_name: '' })
const sending = ref(false)
const sendError = ref('')

// 查询消息
const queryForm = ref({ community_id: '', channel_id: '', limit: 20 })
const messages = ref([])
const messagesLoading = ref(false)

onMounted(() => { botStore.fetchBots() })

async function handleSend() {
  if (!sendForm.value.community_id || !sendForm.value.channel_id || !sendForm.value.content) {
    msg.warning('请填写完整信息')
    return
  }
  sending.value = true
  sendError.value = ''
  try {
    const res = await api.sendMessage({
      community_id: sendForm.value.community_id,
      channel_id: Number(sendForm.value.channel_id),
      content: sendForm.value.content,
      bot_name: sendForm.value.bot_name,
    })
    if (res.success) {
      msg.success('消息发送成功')
      sendForm.value.content = ''
    } else {
      sendError.value = res.message || '发送失败'
    }
  } catch (e) {
    sendError.value = e.response?.data?.message || e.message
  } finally {
    sending.value = false
  }
}

async function fetchMessages() {
  if (!queryForm.value.community_id) {
    msg.warning('请输入社区 ID')
    return
  }
  messagesLoading.value = true
  try {
    const res = await api.getMessages({
      community_id: queryForm.value.community_id,
      channel_id: Number(queryForm.value.channel_id) || undefined,
      limit: Number(queryForm.value.limit) || 20,
    })
    if (res.success) {
      messages.value = res.data.messages || []
      if (!messages.value.length) msg.info('暂无消息记录')
    }
  } catch (e) {
    msg.error('获取消息失败')
  } finally {
    messagesLoading.value = false
  }
}
</script>

<template>
  <div>
    <div class="ui-page-head">
      <div class="ui-page-head-main">
        <div class="ui-page-icon">
          <SvgIcon name="chat" :size="22" />
        </div>
        <div>
          <h1 class="ui-page-title">消息记录</h1>
          <p class="ui-page-sub">发送和查询消息</p>
        </div>
      </div>
    </div>

    <!-- 发送消息 -->
    <div class="ui-card ui-card-pad" style="margin-bottom: 16px;">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="send" :size="16" />
        </div>
        <span class="ui-sec-title">发送消息</span>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">社区 ID</label>
          <n-input v-model:value="sendForm.community_id" placeholder="10位数字社区长ID" />
        </div>
        <div>
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">频道 ID</label>
          <n-input v-model:value="sendForm.channel_id" type="number" placeholder="频道ID" />
        </div>
      </div>

      <div style="margin-bottom: 12px;">
        <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">
          消息内容
          <span style="font-weight: normal; color: var(--text3);">（支持纯文本或 JSON 卡片）</span>
        </label>
        <n-input
          v-model:value="sendForm.content"
          type="textarea"
          :rows="3"
          placeholder="输入消息内容，例如：你好"
        />
      </div>

      <div style="margin-bottom: 12px;">
        <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">机器人</label>
        <n-select
          v-model:value="sendForm.bot_name"
          :options="[{ label: '默认机器人', value: '' }, ...botStore.bots.map(b => ({ label: b.name, value: b.name }))]"
          placeholder="选择机器人"
        />
      </div>

      <p v-if="sendError" style="color: var(--danger); font-size: 13px; margin-bottom: 8px;">{{ sendError }}</p>

      <button class="ui-btn" :disabled="sending" @click="handleSend">
        <SvgIcon name="send" :size="16" />
        {{ sending ? '发送中...' : '发送消息' }}
      </button>
    </div>

    <!-- 查询消息 -->
    <div class="ui-card ui-card-pad">
      <div class="ui-sec-head">
        <div class="ui-sec-icon">
          <SvgIcon name="search" :size="16" />
        </div>
        <span class="ui-sec-title">查询消息</span>
      </div>

      <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: flex-end;">
        <div style="flex: 1; min-width: 150px;">
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">社区 ID</label>
          <n-input v-model:value="queryForm.community_id" placeholder="社区长ID" />
        </div>
        <div style="flex: 1; min-width: 150px;">
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">频道 ID</label>
          <n-input v-model:value="queryForm.channel_id" type="number" placeholder="频道ID" />
        </div>
        <div style="width: 100px;">
          <label style="font-size: 13px; font-weight: 500; color: var(--text2); display: block; margin-bottom: 4px;">数量</label>
          <n-input v-model:value="queryForm.limit" type="number" placeholder="20" />
        </div>
        <button class="ui-btn" :disabled="messagesLoading" @click="fetchMessages">
          <SvgIcon name="search" :size="16" />
          {{ messagesLoading ? '查询中...' : '查询' }}
        </button>
      </div>

      <div v-if="messagesLoading" class="ui-loading">加载中...</div>

      <div v-else-if="messages.length">
        <div
          v-for="m in messages"
          :key="m.message_id"
          style="padding: 12px 0; border-bottom: 1px solid var(--border);"
        >
          <div style="display: flex; gap: 12px; font-size: 12px; color: var(--text3); margin-bottom: 4px;">
            <span>#{{ m.message_id }}</span>
            <span>发送者: {{ m.sender_id }}</span>
            <span>{{ m.created_at }}</span>
          </div>
          <div style="font-size: 14px; word-break: break-all;">{{ m.content }}</div>
        </div>
      </div>

      <div v-else class="ui-empty">
        <SvgIcon name="chat" :size="40" />
        <p>输入社区和频道 ID 查询消息</p>
      </div>
    </div>
  </div>
</template>