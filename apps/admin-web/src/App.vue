<script setup lang="ts">
import { onMounted } from 'vue'
import { Building2, LoaderCircle, ShieldCheck } from 'lucide-vue-next'
import { authState, loadSession } from './api'
import AppShell from './components/AppShell.vue'
import logo from './assets/lungtic-logo.jpg'

onMounted(() => void loadSession())
</script>

<template>
  <div v-if="authState.loading" class="auth-screen">
    <LoaderCircle class="spin" :size="30" />
    <p>正在核验管理会话…</p>
  </div>
  <main v-else-if="!authState.identity" class="login-page">
    <section class="login-panel">
      <div class="login-brand"><img :src="logo" alt="" /><div><b>朗泰 LungTic</b><span>内容与版本管理平台</span></div></div>
      <div class="login-copy">
        <span class="eyebrow">ADMIN CONSOLE</span>
        <h1>安全进入管理工作台</h1>
        <p>使用企业飞书身份登录。系统会再次核验租户、部门与分配角色。</p>
      </div>
      <a class="primary-button login-button" href="/auth/feishu/start"><Building2 :size="18" /> 使用飞书登录</a>
      <p class="security-note"><ShieldCheck :size="15" /> 不提供默认账号或绕过登录入口</p>
    </section>
    <aside class="login-aside" aria-hidden="true">
      <div><span>结构化内容</span><b>编辑、校验、预览与回滚</b></div>
      <div><span>安装包发布</span><b>续传、扫描、原子切换</b></div>
      <div><span>操作审计</span><b>不可修改的发布记录</b></div>
    </aside>
  </main>
  <AppShell v-else />
</template>
