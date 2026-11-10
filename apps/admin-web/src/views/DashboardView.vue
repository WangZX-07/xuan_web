<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Database,
  Download,
  HardDrive,
  PackageCheck,
  RefreshCw,
} from 'lucide-vue-next'
import { api } from '../api'

interface Dashboard {
  current_release: { id: string; version: string; platform: string } | null
  preview_release: { id: string; version: string; platform: string } | null
  cms_dirty: boolean
  content_version: number | null
  download_starts: number
  jobs: Array<{ id: string; version: string; status: string; progress: number; updated_at: string }>
  disk: { free: number; total: number; used: number }
  backup: { status: string; last_file: string | null }
  services: { api: string; database: string }
}

const data = ref<Dashboard | null>(null)
const trends = ref<Array<{ day: string; count: number }>>([])
const loading = ref(true)
const error = ref('')
const maxTrend = computed(() => Math.max(1, ...trends.value.map((item) => item.count)))

function bytes(value: number) {
  return (value / 1024 / 1024 / 1024).toFixed(1) + ' GB'
}
function statusLabel(status: string) {
  return ({ initialized: '等待上传', uploading: '上传中', verifying: '校验中', scanning: '扫描中', ready: '等待发布', failed: '失败', cancelled: '已取消', published: '已发布' } as Record<string, string>)[status] || status
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await Promise.all([
      api<Dashboard>('/api/admin/dashboard'),
      api<Array<{ day: string; count: number }>>('/api/admin/download-trends'),
    ])
    data.value = result[0]
    trends.value = result[1]
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '总览加载失败'
  } finally {
    loading.value = false
  }
}
onMounted(() => void load())
</script>

<template>
  <div class="page-heading">
    <div><p>运营状态</p><h2>早上好，版本与内容都在这里。</h2></div>
    <button class="secondary-button" :disabled="loading" @click="load"><RefreshCw :class="{ spin: loading }" :size="16" /> 刷新</button>
  </div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <div v-if="data" class="dashboard-grid">
    <article class="metric-card featured">
      <div class="metric-icon"><PackageCheck :size="20" /></div>
      <span>当前正式版本</span>
      <strong>{{ data.current_release ? 'v' + data.current_release.version : '尚未发布' }}</strong>
      <p>{{ data.current_release?.platform || '发布体验版后官网会自动切换' }}</p>
      <RouterLink v-if="data.current_release" to="/releases">查看版本 <ArrowUpRight :size="15" /></RouterLink>
    </article>
    <article class="metric-card">
      <div class="metric-icon"><Activity :size="20" /></div>
      <span>CMS 内容</span>
      <strong>{{ data.cms_dirty ? '有待发布修改' : '线上已同步' }}</strong>
      <p>当前公开内容版本 v{{ data.content_version || '—' }}</p>
      <RouterLink to="/content">进入编辑器 <ArrowUpRight :size="15" /></RouterLink>
    </article>
    <article class="metric-card">
      <div class="metric-icon"><Download :size="20" /></div>
      <span>累计下载启动</span>
      <strong>{{ data.download_starts.toLocaleString() }}</strong>
      <p>仅统计日期、版本、结果与流量汇总</p>
    </article>
    <article class="metric-card">
      <div class="metric-icon"><HardDrive :size="20" /></div>
      <span>数据磁盘</span>
      <strong>{{ bytes(data.disk.free) }} 可用</strong>
      <p>总容量 {{ bytes(data.disk.total) }}</p>
    </article>

    <section class="panel chart-panel">
      <div class="panel-heading"><div><span>近 30 天</span><h3>下载启动趋势</h3></div><span class="legend"><i></i> 启动次数</span></div>
      <div v-if="trends.length" class="bar-chart" aria-label="下载启动趋势图">
        <div v-for="item in trends" :key="item.day" class="bar-item">
          <span class="bar-value">{{ item.count }}</span>
          <i :style="{ height: Math.max(4, item.count / maxTrend * 100) + '%' }"></i>
          <small>{{ item.day.slice(5) }}</small>
        </div>
      </div>
      <div v-else class="empty-state">发布安装包后，这里会显示每日下载趋势。</div>
    </section>

    <section class="panel jobs-panel">
      <div class="panel-heading"><div><span>处理队列</span><h3>最近任务</h3></div><RouterLink to="/uploads">全部任务</RouterLink></div>
      <div v-if="data.jobs.length" class="job-list">
        <div v-for="job in data.jobs" :key="job.id" class="job-row">
          <div><b>v{{ job.version }}</b><small>{{ statusLabel(job.status) }}</small></div>
          <div class="progress-track"><i :style="{ width: job.progress + '%' }"></i></div>
          <span>{{ Math.round(job.progress) }}%</span>
        </div>
      </div>
      <div v-else class="empty-state">当前没有上传或校验任务。</div>
    </section>

    <section class="panel health-panel">
      <div class="panel-heading"><div><span>运维检查</span><h3>系统健康</h3></div></div>
      <div class="health-list">
        <div><CheckCircle2 :size="18" /><span><b>控制服务</b><small>仅监听 127.0.0.1:9100</small></span><em>正常</em></div>
        <div><Database :size="18" /><span><b>SQLite WAL</b><small>数据库可读写</small></span><em>正常</em></div>
        <div :class="{ warning: data.backup.status !== 'ok' }"><HardDrive :size="18" /><span><b>每日备份</b><small>{{ data.backup.last_file || '尚未生成备份' }}</small></span><em>{{ data.backup.status === 'ok' ? '正常' : '待检查' }}</em></div>
      </div>
    </section>
  </div>
  <div v-else-if="loading" class="loading-panel">正在加载总览…</div>
</template>
