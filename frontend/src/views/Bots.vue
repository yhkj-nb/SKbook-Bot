<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBotStore } from '@/store'
import SvgIcon from '@/components/SvgIcon.vue'

const botStore = useBotStore()

const loading = ref(true)
const showCreate = ref(false)
const showDelete = ref(false)
const creating = ref(false)
const deleting = ref(false)
const deletingBot = ref(null)
const form = ref({
  name: '',
  token: '',
  command_prefix: '/',
  poll_interval: 3,
})

const bots = computed(() => botStore.bots)

async function fetchData() {
  await botStore.fetchBots()
  loading.value = false
}

function handleShowCreate() {
  form.value = { name: '', token: '', command_prefix: '/', poll_interval: 3 }
  showCreate.value = true
}

async function handleCreate() {
  creating.value = true
  await botStore.createBot(form.value)
  showCreate.value = false
  creating.value = false
}

function handleShowDelete(bot) {
  deletingBot.value = bot
  showDelete.value = true
}

async function handleDelete() {
  deleting.value = true
  await botStore.deleteBot(deletingBot.value.name)
  showDelete.value = false
  deleting.value = false
  deletingBot.value = null
}

async function handleRestart(name) {
  await botStore.restartBot(name)
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
      <div>
        <h1 class="win-page-title">机器人管理</h1>
        <p class="win-page-subtitle">管理已配置的机器人</p>
      </div>
    </div>

    <div v-if="loading" class="win-loading">
      <div class="win-ring"></div>
      <span>加载中...</span>
    </div>

    <template v-else>
      <div class="win-card win-card-pad">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h2 class="win-section-title" style="margin-bottom:0">机器人列表</h2>
          <button class="win-btn win-btn-secondary win-btn-sm" @click="handleShowCreate">
            <SvgIcon name="add" :size="14" />
            添加
          </button>
        </div>

        <div v-if="bots.length" class="win-list">
          <div v-for="bot in bots" :key="bot.name" class="win-list-item">
            <div style="display:flex;align-items:center;gap:12px;flex:1">
              <SvgIcon name="bot" :size="20" />
              <div class="win-list-item-content">
                <div class="win-list-item-title">{{ bot.name }}</div>
                <div class="win-list-item-sub">Token: {{ bot.token_masked }} · 前缀: {{ bot.command_prefix }}</div>
              </div>
            </div>
            <div style="display:flex;gap:6px">
              <span
                class="win-badge"
                :class="bot.running ? 'win-badge-success' : 'win-badge-danger'"
              >
                {{ bot.running ? '运行中' : '已停止' }}
              </span>
              <button class="win-btn win-btn-sm win-btn-secondary" @click="handleRestart(bot.name)">重启</button>
              <button class="win-btn win-btn-sm win-btn-danger" @click="handleShowDelete(bot)">删除</button>
            </div>
          </div>
        </div>
        <div v-else class="win-empty">
          <SvgIcon name="bot" :size="48" />
          <p>暂无机器人</p>
        </div>
      </div>

      <!-- 创建对话框 -->
      <div v-if="showCreate" class="win-dialog-overlay" @click="showCreate = false">
        <div class="win-dialog" @click.stop>
          <div class="win-dialog-title">添加机器人</div>
          <div class="win-dialog-body">
            <div style="display:flex;flex-direction:column;gap:12px">
              <input v-model="form.name" class="win-textbox" placeholder="机器人名称" />
              <input v-model="form.token" class="win-textbox" type="password" placeholder="机器人 Token" />
              <input v-model="form.command_prefix" class="win-textbox" placeholder="命令前缀（如 /）" />
              <input v-model="form.poll_interval" class="win-textbox" type="number" placeholder="轮询间隔（秒）" />
            </div>
          </div>
          <div class="win-dialog-actions">
            <button class="win-btn win-btn-secondary" @click="showCreate = false">取消</button>
            <button class="win-btn win-btn-primary" :disabled="creating" @click="handleCreate">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 删除确认对话框 -->
      <div v-if="showDelete" class="win-dialog-overlay" @click="showDelete = false">
        <div class="win-dialog" @click.stop>
          <div class="win-dialog-title">确认删除</div>
          <div class="win-dialog-body">
            确定要删除机器人「{{ deletingBot?.name }}」吗？此操作不可恢复。
          </div>
          <div class="win-dialog-actions">
            <button class="win-btn win-btn-secondary" @click="showDelete = false">取消</button>
            <button class="win-btn win-btn-danger" @click="handleDelete">
              {{ deleting ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>