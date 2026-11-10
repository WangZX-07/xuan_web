<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { LockKeyhole, Search } from 'lucide-vue-next'
import { api } from '../api'

interface Audit { id: string; actor_id: string | null; action: string; entity_type: string; entity_id: string | null; payload: Record<string, unknown>; created_at: string }
const items = ref<Audit[]>([])
const total = ref(0)
const error = ref('')
async function load() {
  try {
    const result = await api<{ total: number; items: Audit[] }>('/api/admin/audit-events?page_size=100')
    total.value = result.total
    items.value = result.items
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '审计日志加载失败' }
}
onMounted(() => void load())
</script>

<template>
  <div class="page-heading"><div><p>安全审计</p><h2>不可修改的操作记录</h2><span>记录角色操作与对象，不长期保存下载者原始 IP。</span></div></div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <section class="panel table-panel">
    <div class="table-toolbar"><div><h3>操作日志</h3><span>共 {{ total }} 条</span></div><span class="immutable"><LockKeyhole :size="15" />SQLite 触发器保护</span></div>
    <div class="data-table audit-table">
      <div class="table-row table-head"><span>时间</span><span>操作</span><span>对象</span><span>操作者</span><span>摘要</span></div>
      <div v-for="item in items" :key="item.id" class="table-row">
        <span>{{ new Date(item.created_at).toLocaleString('zh-CN') }}</span>
        <span><b>{{ item.action }}</b></span>
        <span>{{ item.entity_type }}<small>{{ item.entity_id || '—' }}</small></span>
        <span class="mono">{{ item.actor_id?.slice(0, 8) || '系统' }}</span>
        <span class="mono payload">{{ JSON.stringify(item.payload) }}</span>
      </div>
      <div v-if="!items.length" class="empty-state tall">尚无操作记录。</div>
    </div>
  </section>
</template>
