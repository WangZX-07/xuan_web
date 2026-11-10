<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, FileUp, Pause, Play, ShieldCheck, UploadCloud, X } from 'lucide-vue-next'
import { api } from '../api'

interface UploadJob {
  id: string
  version: string
  channel: string
  platform: string
  file_name: string
  total_size: number
  chunk_size: number
  expected_chunks: number
  received_bytes: number
  status: string
  progress: number
  bytes_per_second: number
  eta_seconds: number | null
  sha256: string | null
  error_message: string | null
}

const file = ref<File | null>(null)
const version = ref('')
const channel = ref('preview')
const platform = ref('Windows x64')
const notes = ref('')
const job = ref<UploadJob | null>(null)
const running = ref(false)
const paused = ref(false)
const error = ref('')
const dragActive = ref(false)
const canStart = computed(() => file.value && version.value && notes.value.length >= 2 && !running.value)

function choose(event: Event) {
  const selected = (event.target as HTMLInputElement).files?.[0]
  if (selected) file.value = selected
}
function drop(event: DragEvent) {
  dragActive.value = false
  const selected = event.dataTransfer?.files?.[0]
  if (selected) file.value = selected
}
function bytes(value: number) {
  if (value < 1024 * 1024) return Math.round(value / 1024) + ' KB'
  return (value / 1024 / 1024).toFixed(1) + ' MB'
}
function speed(value: number) {
  return value ? bytes(value) + '/s' : '—'
}
async function sha256(blob: Blob) {
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer())
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
async function begin() {
  if (!file.value) return
  error.value = ''
  running.value = true
  paused.value = false
  try {
    job.value = await api<UploadJob>('/api/admin/releases/uploads', {
      method: 'POST',
      body: JSON.stringify({
        version: version.value,
        channel: channel.value,
        platform: platform.value,
        release_notes: notes.value,
        file_name: file.value.name,
        total_size: file.value.size,
      }),
    })
    localStorage.setItem('lungtic-active-upload', job.value.id)
    let index = Math.floor(job.value.received_bytes / job.value.chunk_size)
    while (index < job.value.expected_chunks) {
      if (paused.value) return
      const start = index * job.value.chunk_size
      const chunk = file.value.slice(start, Math.min(start + job.value.chunk_size, file.value.size))
      const hash = await sha256(chunk)
      job.value = await api<UploadJob>('/api/admin/releases/uploads/' + job.value.id + '/chunks/' + index, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/octet-stream', 'X-Chunk-SHA256': hash },
        body: chunk,
      })
      index += 1
    }
    await api('/api/admin/releases/uploads/' + job.value.id + '/complete', { method: 'POST' })
    await followJob()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '上传失败'
  } finally {
    running.value = false
  }
}
async function followJob() {
  if (!job.value) return
  for (let attempt = 0; attempt < 180; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
    job.value = await api<UploadJob>('/api/admin/releases/uploads/' + job.value.id)
    if (['ready', 'failed', 'cancelled', 'published'].includes(job.value.status)) break
  }
}
function togglePause() {
  paused.value = !paused.value
  if (!paused.value) void begin()
}
async function cancel() {
  if (!job.value) return
  await api('/api/admin/releases/uploads/' + job.value.id + '/cancel', { method: 'POST' })
  paused.value = true
  running.value = false
  job.value.status = 'cancelled'
}
</script>

<template>
  <div class="page-heading">
    <div><p>版本交付</p><h2>上传新的 TICI Viewer</h2><span>安装包校验通过后仍是草稿，需由发布者再次确认。</span></div>
  </div>
  <div class="upload-layout">
    <form class="panel form-panel" @submit.prevent="begin">
      <div class="form-section"><span>01</span><div><h3>版本信息</h3><p>版本号与渠道一经创建不可修改。</p></div></div>
      <div class="form-grid">
        <label>版本号<input v-model="version" required placeholder="0.3.0-beta.1" /></label>
        <label>发布渠道<select v-model="channel"><option value="preview">体验版</option><option value="stable">正式版</option></select></label>
        <label>适用平台<select v-model="platform"><option>Windows x64</option><option>Windows arm64</option></select></label>
        <label class="wide">发布说明<textarea v-model="notes" required rows="4" placeholder="说明本版本变更与使用边界"></textarea></label>
      </div>
      <div class="form-section"><span>02</span><div><h3>选择安装包</h3><p>支持 EXE / MSI，单文件不超过 1 GB。</p></div></div>
      <label class="drop-zone" :class="{ active: dragActive }" @dragenter.prevent="dragActive = true" @dragover.prevent @dragleave.prevent="dragActive = false" @drop.prevent="drop">
        <input type="file" accept=".exe,.msi" @change="choose" />
        <UploadCloud :size="32" />
        <template v-if="file"><b>{{ file.name }}</b><span>{{ bytes(file.size) }}</span></template>
        <template v-else><b>拖放安装包到这里</b><span>或点击选择本地文件</span></template>
      </label>
      <div v-if="error" class="alert error">{{ error }}</div>
      <button class="primary-button" type="submit" :disabled="!canStart"><FileUp :size="18" /> 初始化并上传</button>
    </form>

    <aside class="panel upload-status">
      <div class="panel-heading"><div><span>实时状态</span><h3>上传与安全校验</h3></div><ShieldCheck :size="21" /></div>
      <template v-if="job">
        <div class="upload-file"><div class="file-icon">EXE</div><div><b>{{ job.file_name }}</b><span>v{{ job.version }} · {{ job.platform }}</span></div></div>
        <div class="upload-percent"><strong>{{ Math.round(job.progress) }}%</strong><span>{{ bytes(job.received_bytes) }} / {{ bytes(job.total_size) }}</span></div>
        <div class="progress-track large"><i :style="{ width: job.progress + '%' }"></i></div>
        <div class="upload-stats"><div><span>速度</span><b>{{ speed(job.bytes_per_second) }}</b></div><div><span>预计剩余</span><b>{{ job.eta_seconds == null ? '—' : job.eta_seconds + ' 秒' }}</b></div></div>
        <div class="phase-list">
          <div :class="{ done: job.received_bytes === job.total_size }"><Check :size="15" /> 分块上传</div>
          <div :class="{ done: ['scanning','ready','published'].includes(job.status) }"><Check :size="15" /> SHA-256 与文件头校验</div>
          <div :class="{ done: ['ready','published'].includes(job.status) }"><Check :size="15" /> ClamAV 扫描</div>
          <div :class="{ done: job.status === 'ready' || job.status === 'published' }"><Check :size="15" /> 等待发布确认</div>
        </div>
        <p v-if="job.error_message" class="alert error">{{ job.error_message }}</p>
        <div v-if="running && job.status === 'uploading'" class="inline-actions">
          <button class="secondary-button" @click="togglePause"><Play v-if="paused" :size="16" /><Pause v-else :size="16" />{{ paused ? '继续' : '暂停' }}</button>
          <button class="danger-button" @click="cancel"><X :size="16" />取消</button>
        </div>
        <RouterLink v-if="job.status === 'ready'" class="primary-button full" to="/releases">前往发布确认</RouterLink>
      </template>
      <div v-else class="empty-state tall">选择文件并开始上传后，可在此查看速度、进度、校验和扫描阶段。</div>
    </aside>
  </div>
</template>
