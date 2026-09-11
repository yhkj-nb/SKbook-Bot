<script setup>
import { ref } from 'vue'
import { api } from '@/api'
import SvgIcon from '@/components/SvgIcon.vue'

const send = ref({ community_id: '', channel_id: '', content: '' })
const sending = ref(false)
const sendError = ref('')

const query = ref({ community_id: '', channel_id: '', limit: 20 })
const messages = ref([])
const messagesLoading = ref(false)

async function handleSend() {
  if (!send.value.community_id || !send.value.channel_id || !send.value.content) {
    sendError.value = '请填写完整信息'
    return
  }
  sending.value = true
  sendError.value = ''
  try {
    const res = await api.sendMessage({
      community_id: send.value.community_id,
      channel_id: Number(send.value.channel_id),
      content: send.value.content,
    })
    if (res.success) {
      send.value.content = ''
      sendError.value = ''
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
  if (!query.value.community_id) {
    return
  }
  messagesLoading.value = true
  try {
    const res = await api.getMessages({
      community_id: query.value.community_id,
      channel_id: Number(query.value.channel_id) || undefined,
      limit: Number(query.value.limit) || 20,
    })
    if (res.success) {
      messages.value = res.data.messages || []
    }
  } catch (e) {
    // ignore
  } finally {
    messagesLoading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="win-page-title">消息记录</h1>
    <p class="win-page-subtitle">发送和查询消息</p>

    <!-- 发送消息卡片 -->
    <div class="win-card win-card-pad" style="margin-bottom:16px">
      <h2 class="win-section-title">发送消息</h2>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div class="win-textbox-group">
          <label class="win-textbox-label">社区 ID</label>
          <input class="win-textbox" v-model="send.community_id" placeholder="社区长ID" />
        </div>
        <div class="win-textbox-group">
          <label class="win-textbox-label">频道 ID</label>
          <input class="win-textbox" v-model="send.channel_id" type="number" placeholder="频道ID" />
        </div>
      </div>

      <div class="win-textbox-group" style="margin-bottom:12px">
        <label class="win-textbox-label">消息内容</label>
        <div style="font-size:12px;color:var(--text-tertiary);margin-bottom:4px">支持纯文本或JSON卡片</div>
        <textarea class="win-textarea" v-model="send.content" rows="3" placeholder="输入消息内容"></textarea>
      </div>

      <p v-if="sendError" style="color:var(--danger);font-size:13px;margin-bottom:8px">{{ sendError }}</p>

      <button class="win-btn win-btn-primary" :disabled="sending" @click="handleSend">
        {{ sending ? '发送中...' : '发送消息' }}
      </button>
    </div>

    <!-- 查询消息卡片 -->
    <div class="win-card win-card-pad">
      <h2 class="win-section-title">查询消息</h2>

      <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:flex-end">
        <div class="win-textbox-group" style="flex:1;min-width:150px">
          <label class="win-textbox-label">社区 ID</label>
          <input class="win-textbox" v-model="query.community_id" placeholder="社区长ID" />
        </div>
        <div class="win-textbox-group" style="flex:1;min-width:150px">
          <label class="win-textbox-label">频道 ID</label>
          <input class="win-textbox" v-model="query.channel_id" type="number" placeholder="频道ID" />
        </div>
        <div class="win-textbox-group" style="width:100px">
          <label class="win-textbox-label">数量</label>
          <input class="win-textbox" v-model="query.limit" type="number" placeholder="20" />
        </div>
        <button class="win-btn win-btn-secondary" @click="fetchMessages">
          查询
        </button>
      </div>

      <div v-if="messagesLoading" class="win-loading">
        <div class="win-ring"></div>
      </div>

      <template v-else>
        <div v-if="messages.length" class="win-list">
          <div v-for="m in messages" :key="m.message_id" class="win-list-item">
            <div style="display:flex;align-items:center;gap:10px;flex:1">
              <SvgIcon name="messages" :size="18" />
              <div class="win-list-item-content">
                <div class="win-list-item-title">发送者: {{ m.sender_id }}</div>
                <div class="win-list-item-sub">{{ m.content?.substring(0, 100) }}{{ m.content?.length > 100 ? '...' : '' }}</div>
              </div>
            </div>
            <div style="font-size:12px;color:var(--text-tertiary);flex-shrink:0">{{ m.created_at }}</div>
          </div>
        </div>

        <div v-else class="win-empty">
          <SvgIcon name="chat" :size="36" />
          <p>输入社区和频道ID查询消息</p>
        </div>
      </template>
    </div>
  </div>
</template>