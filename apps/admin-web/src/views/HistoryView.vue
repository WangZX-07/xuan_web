<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Clock3, CornerUpLeft, Eye, GitCommitHorizontal } from 'lucide-vue-next'
import { api, authState } from '../api'

interface Version { id: string; version_number: number; release_note: string; created_by: string | null; rolled_back_from_id: string | null; created_at: string }
const items = ref<Version[]>([])
const error = ref('')
const selected = ref<any>(null)
const note = ref('')
const busy = ref(false)
const canPublish = authState.identity?.role !== 'editor'
async function load() {
  try { items.value = await api<Version[]>('/api/admin/content/versions') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '发布记录加载失败' }
}
async function inspect(item: Version) {
  selected.value = await api('/api/admin/content/versions/' + item.id)
}
async function rollback(item: Version) {
  if (!note.value.trim()) return
  busy.value = true
  try {
    await api('/api/admin/content/versions/' + item.id + '/rollback', { method: 'POST', body: JSON.stringify({ release_note: note.value }) })
    note.value = ''
    await load()
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '回滚失败' }
  finally { busy.value = false }
}
onMounted(() => void load())
</script>

<template>
  <div class="page-heading"><div><p>不可变记录</p><h2>CMS 发布历史</h2><span>每次发布与回滚都会生成新的内容版本，不覆盖历史记录。</span></div></div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <div class="history-layout">
    <section class="panel timeline">
      <article v-for="(item, index) in items" :key="item.id">
        <div class="timeline-dot"><GitCommitHorizontal :size="16" /></div>
        <div class="timeline-card">
          <div><span>内容 v{{ item.version_number }}</span><em v-if="index === 0">当前线上</em></div>
          <h3>{{ item.release_note }}</h3>
          <p><Clock3 :size="14" />{{ new Date(item.created_at).toLocaleString('zh-CN') }}</p>
          <div class="inline-actions">
            <button class="small-button" @click="inspect(item)"><Eye :size="14" />查看内容</button>
            <button v-if="canPublish && index !== 0" class="small-button" @click="selected = { rollback: item }"><CornerUpLeft :size="14" />回滚到此版本</button>
          </div>
        </div>
      </article>
      <div v-if="!items.length" class="empty-state tall">尚无发布记录。</div>
    </section>
    <aside v-if="selected" class="panel version-detail">
      <template v-if="selected.rollback">
        <span>创建新的回滚版本</span><h3>回滚到内容 v{{ selected.rollback.version_number }}</h3>
        <p>线上内容会原子切换，当前版本仍保留在历史中。</p>
        <label>回滚说明<input v-model="note" placeholder="说明本次回滚原因" /></label>
        <button class="primary-button full" :disabled="busy || !note" @click="rollback(selected.rollback)"><CornerUpLeft :size="16" />确认回滚</button>
      </template>
      <template v-else>
        <span>版本快照</span><h3>内容 v{{ selected.version_number }}</h3>
        <p>{{ selected.release_note }}</p>
        <dl><dt>首屏标题</dt><dd>{{ selected.content.hero.title }}</dd><dt>TICI 标题</dt><dd>{{ selected.content.tici.title }}</dd><dt>下载区</dt><dd>{{ selected.content.download.title }}</dd></dl>
      </template>
    </aside>
  </div>
</template>
