<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Archive, CheckCircle2, Download, MoreHorizontal, Package, RefreshCw, Rocket } from 'lucide-vue-next'
import { api } from '../api'

interface Release {
  id: string
  version: string
  channel: string
  platform: string
  release_notes: string
  file_name: string
  byte_size: number
  sha256: string
  status: string
  is_current: boolean
  created_at: string
  published_at: string | null
}
const items = ref<Release[]>([])
const loading = ref(true)
const error = ref('')
const busy = ref('')
function bytes(value: number) { return (value / 1024 / 1024).toFixed(1) + ' MB' }
function date(value: string | null) { return value ? new Date(value).toLocaleString('zh-CN') : '尚未发布' }
function statusLabel(item: Release) {
  if (item.is_current) return '当前版本'
  return ({ draft: '待发布', published: '已发布', archived: '已归档' } as Record<string, string>)[item.status] || item.status
}
async function load() {
  loading.value = true
  try { items.value = await api<Release[]>('/api/admin/releases') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '版本加载失败' }
  finally { loading.value = false }
}
async function action(item: Release, kind: 'publish' | 'set-current' | 'archive') {
  busy.value = item.id
  error.value = ''
  try {
    await api('/api/admin/releases/' + item.id + '/' + kind, {
      method: 'POST',
      body: kind === 'publish' ? JSON.stringify({ make_current: true }) : undefined,
    })
    await load()
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '操作失败' }
  finally { busy.value = '' }
}
onMounted(() => void load())
</script>

<template>
  <div class="page-heading">
    <div><p>版本管理</p><h2>安装包发布与回滚</h2><span>重新设为当前版本即可快速回滚；已发布文件默认只归档。</span></div>
    <RouterLink class="primary-button" to="/uploads"><Package :size="17" /> 上传安装包</RouterLink>
  </div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <section class="panel table-panel">
    <div class="table-toolbar">
      <div><h3>全部版本</h3><span>{{ items.length }} 个版本</span></div>
      <button class="icon-button" title="刷新" @click="load"><RefreshCw :class="{ spin: loading }" :size="17" /></button>
    </div>
    <div class="data-table releases-table">
      <div class="table-row table-head"><span>版本</span><span>状态</span><span>平台与文件</span><span>校验值</span><span>发布时间</span><span>操作</span></div>
      <div v-for="item in items" :key="item.id" class="table-row">
        <span><b>v{{ item.version }}</b><small>{{ item.channel }}</small></span>
        <span><em class="status-pill" :class="{ current: item.is_current, draft: item.status === 'draft', archived: item.status === 'archived' }">{{ statusLabel(item) }}</em></span>
        <span><b>{{ item.platform }}</b><small>{{ item.file_name }} · {{ bytes(item.byte_size) }}</small></span>
        <span class="mono">{{ item.sha256.slice(0, 12) }}…</span>
        <span>{{ date(item.published_at) }}</span>
        <span class="row-actions">
          <button v-if="item.status === 'draft'" class="small-button" :disabled="busy === item.id" @click="action(item, 'publish')"><Rocket :size="14" />发布</button>
          <button v-else-if="item.status === 'published' && !item.is_current" class="small-button" :disabled="busy === item.id" @click="action(item, 'set-current')"><CheckCircle2 :size="14" />设为当前</button>
          <button v-if="item.status !== 'archived' && !item.is_current" class="icon-button" title="归档" :disabled="busy === item.id" @click="action(item, 'archive')"><Archive :size="16" /></button>
        </span>
      </div>
      <div v-if="!loading && !items.length" class="empty-state tall">尚无已通过扫描的安装包。</div>
    </div>
  </section>
</template>
