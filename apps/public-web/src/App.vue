<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  CircleDot,
  Eye,
  Film,
  Layers3,
  Menu,
  ScanLine,
  ShieldCheck,
  X,
} from 'lucide-vue-next'
import logo from './assets/lungtic-logo.jpg'
import { fallbackContent } from './content/fallback'
import type { ReleaseSummary, SiteContent } from './content/types'

const content = ref<SiteContent>(fallbackContent)
const release = ref<ReleaseSummary | null>(null)
const menuOpen = ref(false)
const capabilityIcons = { phases: Layers3, mask: ScanLine, cine: Film, igtv: CircleDot, motion: Activity, review: Eye }

const sectionMeta = computed(() =>
  Object.fromEntries(content.value.section_order.map((item, index) => [item.key, { ...item, order: index + 1 }])),
)
const isVisible = (key: keyof typeof sectionMeta.value) => sectionMeta.value[key]?.visible !== false
const orderOf = (key: keyof typeof sectionMeta.value) => sectionMeta.value[key]?.order ?? 10

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

async function loadPublishedContent() {
  try {
    const response = await fetch('/api/public/site', { headers: { Accept: 'application/json' } })
    if (response.ok) {
      const payload = await response.json()
      content.value = payload.content
      document.title = content.value.seo.title
      document.querySelector('meta[name="description"]')?.setAttribute('content', content.value.seo.description)
    }
  } catch {
    // The build-time snapshot intentionally remains active when the API is unavailable.
  }
}

async function loadRelease() {
  try {
    const response = await fetch('/api/public/releases/latest', { headers: { Accept: 'application/json' } })
    if (response.status === 204) return
    if (response.ok) release.value = await response.json()
  } catch {
    release.value = null
  }
}

onMounted(() => {
  void Promise.all([loadPublishedContent(), loadRelease()])
})
</script>

<template>
  <a class="skip-link" href="#main">跳至主要内容</a>
  <header class="site-header">
    <a class="brand" href="#top" aria-label="朗泰 LungTic 首页">
      <img :src="logo" alt="" width="40" height="40" />
      <span><b>朗泰</b><small>LungTic</small></span>
    </a>
    <button class="menu-button" type="button" :aria-expanded="menuOpen" aria-label="打开导航" @click="menuOpen = !menuOpen">
      <X v-if="menuOpen" :size="22" />
      <Menu v-else :size="22" />
    </button>
    <nav :class="{ open: menuOpen }" aria-label="主导航">
      <a v-for="item in content.navigation" :key="item.anchor" :href="item.anchor" @click="menuOpen = false">{{ item.label }}</a>
    </nav>
    <a class="header-download" href="#download">下载体验版 <ArrowDownToLine :size="16" /></a>
  </header>

  <main id="main">
    <section id="top" class="hero">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-copy">
        <p class="eyebrow">{{ content.hero.eyebrow }}</p>
        <h1>{{ content.hero.title }}</h1>
        <p class="hero-intro">{{ content.hero.description }}</p>
        <div class="hero-actions">
          <a class="button primary" href="#download">{{ content.hero.primary_label }} <ArrowDownToLine :size="18" /></a>
          <a class="button secondary" href="#workflow">{{ content.hero.secondary_label }} <ArrowRight :size="18" /></a>
        </div>
        <p class="research-note"><ShieldCheck :size="16" /> 科研原型 · 不用于患者治疗决策</p>
      </div>
      <figure class="workbench">
        <div class="window-bar"><span></span><span></span><span></span><b>LungTic · TICI Viewer</b></div>
        <img
          v-if="content.hero.image_asset_id"
          :src="'/api/public/assets/' + content.hero.image_asset_id"
          :alt="content.hero.image_alt"
          width="1384"
          height="771"
          fetchpriority="high"
          decoding="async"
        />
        <img
          v-else
          src="/media/real-tici-workbench-v1.webp"
          srcset="/media/real-tici-workbench-v1-720.webp 720w, /media/real-tici-workbench-v1.webp 1384w"
          sizes="(max-width: 980px) calc(100vw - 40px), 760px"
          :alt="content.hero.image_alt"
          width="1384"
          height="771"
          fetchpriority="high"
          decoding="async"
        />
        <figcaption>真实 LungTic 工作台界面，经脱敏处理</figcaption>
      </figure>
    </section>

    <div class="ordered-sections">
      <section v-if="isVisible('capabilities')" id="capabilities" class="section capabilities" :style="{ order: orderOf('capabilities') }">
        <div class="section-heading">
          <p class="eyebrow blue">CORE CAPABILITIES</p>
          <h2>{{ content.capabilities_title }}</h2>
          <p>{{ content.capabilities_intro }}</p>
        </div>
        <div class="capability-grid">
          <article v-for="(item, index) in content.capabilities" :key="item.key">
            <div class="icon-box">
              <component :is="capabilityIcons[item.key as keyof typeof capabilityIcons] || CircleDot" :size="23" />
            </div>
            <span class="card-index">0{{ index + 1 }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>

      <section v-if="isVisible('workflow')" id="workflow" class="section workflow" :style="{ order: orderOf('workflow') }">
        <div class="section-heading compact">
          <p class="eyebrow blue">REVIEWABLE WORKFLOW</p>
          <h2>{{ content.workflow_title }}</h2>
        </div>
        <ol class="workflow-list">
          <li v-for="item in content.workflow" :key="item.step">
            <span>{{ item.step }}</span>
            <div><h3>{{ item.title }}</h3><p>{{ item.description }}</p></div>
          </li>
        </ol>
      </section>

      <section v-if="isVisible('tici')" id="tici" class="section tici" :style="{ order: orderOf('tici') }">
        <div class="tici-copy">
          <p class="eyebrow">{{ content.tici.eyebrow }}</p>
          <h2>{{ content.tici.title }}</h2>
          <p>{{ content.tici.description }}</p>
          <ul>
            <li v-for="point in content.tici.points" :key="point"><Check :size="17" />{{ point }}</li>
          </ul>
        </div>
        <figure>
          <img
            v-if="content.tici.image_asset_id"
            :src="'/api/public/assets/' + content.tici.image_asset_id"
            :alt="content.tici.image_alt"
            width="1024"
            height="1132"
            loading="lazy"
            decoding="async"
          />
          <img
            v-else
            src="/media/synthetic-tici-preview-v1.webp"
            :alt="content.tici.image_alt"
            width="1024"
            height="1132"
            loading="lazy"
            decoding="async"
          />
          <figcaption>合成示例，仅用于解释数据表达</figcaption>
        </figure>
      </section>

      <section v-if="isVisible('progress')" id="progress" class="section progress" :style="{ order: orderOf('progress') }">
        <div class="section-heading compact">
          <p class="eyebrow blue">PROJECT STATUS</p>
          <h2>{{ content.progress_title }}</h2>
        </div>
        <div class="progress-grid">
          <article v-for="item in content.progress" :key="item.title" :class="item.status">
            <span>{{ item.label }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>

      <section v-if="isVisible('safety')" class="section safety" :style="{ order: orderOf('safety') }">
        <div><ShieldCheck :size="30" /><h2>{{ content.safety.title }}</h2></div>
        <ul><li v-for="statement in content.safety.statements" :key="statement"><Check :size="16" />{{ statement }}</li></ul>
      </section>

      <section v-if="isVisible('background')" class="section background" :style="{ order: orderOf('background') }">
        <p class="eyebrow blue">PROJECT ORIGIN</p>
        <h2>{{ content.background.title }}</h2>
        <p>{{ content.background.description }}</p>
        <strong>{{ content.background.affiliation }}</strong>
      </section>

      <section v-if="isVisible('download')" id="download" class="section download" :style="{ order: orderOf('download') }">
        <div>
          <p class="eyebrow">{{ content.download.eyebrow }}</p>
          <h2>{{ content.download.title }}</h2>
          <p>{{ content.download.description }}</p>
        </div>
        <div class="release-panel">
          <template v-if="release">
            <span class="release-version">v{{ release.version }} · {{ release.platform }}</span>
            <p>{{ formatBytes(release.byte_size) }} · SHA-256 {{ release.sha256.slice(0, 12) }}…</p>
            <a class="button light" :href="release.download_url">{{ content.download.button_label }} <ArrowDownToLine :size="18" /></a>
          </template>
          <template v-else>
            <span class="release-version">体验版准备中</span>
            <p>{{ content.download.fallback_note }}</p>
            <button class="button light" disabled>{{ content.download.button_label }}</button>
          </template>
        </div>
      </section>
    </div>
  </main>

  <footer>
    <div class="brand footer-brand"><img :src="logo" alt="" width="36" height="36" /><span><b>朗泰</b><small>LungTic</small></span></div>
    <p>{{ content.footer.summary }}</p>
    <div>
      <span>{{ content.footer.copyright }}</span>
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">{{ content.footer.icp_number }}</a>
    </div>
  </footer>
</template>
