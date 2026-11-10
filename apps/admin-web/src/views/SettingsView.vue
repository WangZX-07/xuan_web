<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { KeyRound, Save, Shield, Users } from 'lucide-vue-next'
import { api, authState } from '../api'

interface Identity { id: string; display_name: string; role: 'editor' | 'publisher' | 'owner'; is_active: boolean; last_login_at: string | null }
const identities = ref<Identity[]>([])
const error = ref('')
async function load() {
  try { identities.value = await api<Identity[]>('/api/admin/identities') }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '成员列表加载失败' }
}
async function update(item: Identity) {
  try { await api('/api/admin/identities/' + item.id + '/role', { method: 'PUT', body: JSON.stringify({ role: item.role }) }) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : '角色更新失败'; await load() }
}
onMounted(() => void load())
</script>

<template>
  <div class="page-heading"><div><p>所有者设置</p><h2>成员角色与系统边界</h2><span>飞书部门成员只获得登录资格，具体能力仍由这里的角色决定。</span></div></div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <div class="settings-grid">
    <section class="panel settings-panel">
      <div class="panel-heading"><div><span>访问控制</span><h3>管理成员</h3></div><Users :size="21" /></div>
      <div v-for="item in identities" :key="item.id" class="member-row">
        <span class="avatar">{{ item.display_name.slice(0, 1) }}</span>
        <div><b>{{ item.display_name }}</b><small>{{ item.last_login_at ? '最近登录 ' + new Date(item.last_login_at).toLocaleString('zh-CN') : '尚未登录' }}</small></div>
        <select v-model="item.role" :disabled="item.id === authState.identity?.id" @change="update(item)"><option value="editor">编辑者</option><option value="publisher">发布者</option><option value="owner">所有者</option></select>
      </div>
    </section>
    <aside class="panel boundary-panel">
      <Shield :size="25" /><h3>安全边界</h3>
      <ul><li>飞书密钥仅由服务器环境注入</li><li>9100 只监听回环地址</li><li>发布与删除均写入审计日志</li><li>ClamAV 不可用时禁止发布</li></ul>
      <div class="info-row"><KeyRound :size="17" /><span><b>初始所有者</b><small>由飞书 open_id 环境配置绑定</small></span></div>
    </aside>
  </div>
</template>
