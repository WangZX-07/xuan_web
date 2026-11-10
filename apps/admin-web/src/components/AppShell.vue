<script setup lang="ts">
import {
  Archive,
  Boxes,
  ChevronDown,
  ClipboardList,
  FileClock,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  UploadCloud,
  X,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, authState } from '../api'
import logo from '../assets/lungtic-logo.jpg'

const route = useRoute()
const sidebarOpen = ref(false)
const roleLabel = { editor: '编辑者', publisher: '发布者', owner: '所有者' }
const canPublish = computed(() => authState.identity?.role !== 'editor')
const items = computed(() => [
  { to: '/', label: '总览', icon: LayoutDashboard, show: true },
  { to: '/uploads', label: '安装包上传', icon: UploadCloud, show: canPublish.value },
  { to: '/releases', label: '版本列表', icon: Boxes, show: canPublish.value },
  { to: '/content', label: 'CMS 编辑器', icon: ClipboardList, show: true },
  { to: '/content/history', label: '发布记录', icon: FileClock, show: true },
  { to: '/audit', label: '审计日志', icon: Archive, show: true },
  { to: '/settings', label: '系统设置', icon: Settings, show: authState.identity?.role === 'owner' },
])

const pageTitle = computed(() => items.value.find((item) => item.to === route.path)?.label || '管理台')
async function logout() {
  try { await api('/auth/logout', { method: 'POST' }) } finally { window.location.href = '/' }
}
</script>

<template>
  <div class="admin-shell">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <img :src="logo" alt="" />
        <div><b>朗泰 LungTic</b><span>管理控制台</span></div>
        <button class="icon-button sidebar-close" aria-label="关闭导航" @click="sidebarOpen = false"><X :size="20" /></button>
      </div>
      <nav aria-label="管理功能">
        <RouterLink v-for="item in items.filter((entry) => entry.show)" :key="item.to" :to="item.to" @click="sidebarOpen = false">
          <component :is="item.icon" :size="18" />
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="sidebar-foot">
        <span class="status-dot"></span>
        <div><b>控制服务</b><small>127.0.0.1:9100</small></div>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <button class="icon-button mobile-menu" aria-label="打开导航" @click="sidebarOpen = true"><Menu :size="20" /></button>
        <div><span class="breadcrumb">LungTic / 管理</span><h1>{{ pageTitle }}</h1></div>
        <div class="identity">
          <span class="avatar">{{ authState.identity?.display_name.slice(0, 1) }}</span>
          <div><b>{{ authState.identity?.display_name }}</b><small>{{ roleLabel[authState.identity!.role] }}</small></div>
          <ChevronDown :size="16" />
        </div>
        <form @submit.prevent="logout">
          <button class="icon-button" title="退出登录" type="submit"><LogOut :size="18" /></button>
        </form>
      </header>
      <div class="page"><RouterView /></div>
    </div>
  </div>
</template>
