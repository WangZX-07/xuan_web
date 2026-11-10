<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  ChevronRight,
  Cloud,
  Eye,
  ImagePlus,
  Monitor,
  Save,
  Send,
  Smartphone,
} from 'lucide-vue-next'
import { api, authState } from '../api'
import workbench from '../assets/real-tici-workbench.webp'

interface DraftResponse { revision: number; updated_at: string; content: any }
interface Check { level: 'pass' | 'warning' | 'error'; message: string }
interface AssetResponse { id: string; url: string; alt_text: string }

const content = ref<any>(null)
const revision = ref(1)
const updatedAt = ref('')
const active = ref('hero')
const device = ref<'desktop' | 'mobile'>('desktop')
const saveState = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const checks = ref<Check[]>([])
const publishNote = ref('')
const publishBusy = ref(false)
const error = ref('')
let timer = 0
let hydrated = false

const sections = [
  { key: 'seo', label: '基础 SEO' },
  { key: 'hero', label: '首屏' },
  { key: 'capabilities', label: '产品能力' },
  { key: 'workflow', label: '工作流' },
  { key: 'tici', label: 'TICI 专题' },
  { key: 'progress', label: '项目进展' },
  { key: 'safety', label: '安全声明' },
  { key: 'background', label: '团队介绍' },
  { key: 'download', label: '下载区' },
  { key: 'footer', label: '页脚' },
  { key: 'order', label: '栏目顺序' },
]
const canPublish = computed(() => authState.identity?.role === 'publisher' || authState.identity?.role === 'owner')

async function load() {
  try {
    const result = await api<DraftResponse>('/api/admin/content/draft')
    content.value = result.content
    revision.value = result.revision
    updatedAt.value = result.updated_at
    const validation = await api<{ checks: Check[] }>('/api/admin/content/validation')
    checks.value = validation.checks
    window.setTimeout(() => { hydrated = true }, 0)
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '草稿加载失败' }
}
async function save() {
  if (!content.value || saveState.value === 'saving') return
  saveState.value = 'saving'
  try {
    const result = await api<{ revision: number; updated_at: string; checks: Check[] }>('/api/admin/content/draft', {
      method: 'PUT',
      body: JSON.stringify({ revision: revision.value, content: content.value }),
    })
    revision.value = result.revision
    updatedAt.value = result.updated_at
    checks.value = result.checks
    saveState.value = 'saved'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '保存失败'
    saveState.value = 'error'
  }
}
watch(content, () => {
  if (!hydrated) return
  saveState.value = 'idle'
  window.clearTimeout(timer)
  timer = window.setTimeout(() => void save(), 1200)
}, { deep: true })
function move(index: number, direction: number) {
  const target = index + direction
  if (target < 0 || target >= content.value.section_order.length) return
  const list = content.value.section_order
  const item = list[index]
  list.splice(index, 1)
  list.splice(target, 0, item)
}
async function uploadAsset(target: 'hero' | 'tici', event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  form.append('alt_text', content.value[target].image_alt)
  try {
    const asset = await api<AssetResponse>('/api/admin/assets', { method: 'POST', body: form })
    content.value[target].image_asset_id = asset.id
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '素材上传失败' }
}
async function publish() {
  if (!publishNote.value.trim()) return
  await save()
  publishBusy.value = true
  try {
    await api('/api/admin/content/publish', {
      method: 'POST',
      body: JSON.stringify({ release_note: publishNote.value }),
    })
    publishNote.value = ''
    error.value = ''
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '发布失败' }
  finally { publishBusy.value = false }
}
function sectionLabel(key: string) {
  return ({ capabilities: '产品能力', workflow: '工作流', tici: 'TICI', progress: '项目进展', safety: '安全声明', background: '团队介绍', download: '下载区' } as Record<string, string>)[key] || key
}
onMounted(() => void load())
</script>

<template>
  <div class="cms-toolbar">
    <div><p>结构化 CMS</p><h2>官网内容编辑器</h2></div>
    <div class="save-indicator"><Cloud :size="16" /><span>{{ saveState === 'saving' ? '正在保存…' : saveState === 'error' ? '保存失败' : '草稿已自动保存' }}</span><small>修订 {{ revision }}</small></div>
    <button class="secondary-button" @click="save"><Save :size="16" />保存草稿</button>
  </div>
  <div v-if="error" class="alert error">{{ error }}</div>
  <div v-if="content" class="cms-layout">
    <aside class="cms-nav panel">
      <button v-for="item in sections" :key="item.key" :class="{ active: active === item.key }" @click="active = item.key">
        <span>{{ item.label }}</span><ChevronRight :size="15" />
      </button>
    </aside>

    <section class="panel cms-editor">
      <div v-if="active === 'seo'">
        <div class="editor-heading"><span>基础设置</span><h3>SEO 信息</h3><p>用于搜索结果与页面分享摘要。</p></div>
        <label>页面标题<input v-model="content.seo.title" maxlength="70" /></label>
        <label>页面描述<textarea v-model="content.seo.description" rows="4" maxlength="180"></textarea></label>
        <label>关键词（逗号分隔）<input :value="content.seo.keywords.join('，')" @change="content.seo.keywords = ($event.target as HTMLInputElement).value.split(/[，,]/).filter(Boolean)" /></label>
      </div>
      <div v-else-if="active === 'hero'">
        <div class="editor-heading"><span>官网首屏</span><h3>核心叙事</h3><p>标题保持克制，避免使用未经验证的临床效果描述。</p></div>
        <label>眉题<input v-model="content.hero.eyebrow" /></label>
        <label>主标题<textarea v-model="content.hero.title" rows="2"></textarea></label>
        <label>说明<textarea v-model="content.hero.description" rows="4"></textarea></label>
        <div class="two-fields"><label>主按钮<input v-model="content.hero.primary_label" /></label><label>次按钮<input v-model="content.hero.secondary_label" /></label></div>
        <label>图片替代文本<input v-model="content.hero.image_alt" /></label>
        <label class="asset-picker"><ImagePlus :size="20" /><span>替换首屏工作台图片<small>JPEG / PNG / WebP / AVIF</small></span><input type="file" accept="image/jpeg,image/png,image/webp,image/avif" @change="uploadAsset('hero', $event)" /></label>
      </div>
      <div v-else-if="active === 'capabilities'">
        <div class="editor-heading"><span>产品信息</span><h3>产品能力</h3><p>固定六项能力，只管理标题与说明。</p></div>
        <label>栏目标题<input v-model="content.capabilities_title" /></label>
        <label>栏目引言<textarea v-model="content.capabilities_intro" rows="3"></textarea></label>
        <div v-for="item in content.capabilities" :key="item.key" class="repeater"><span>{{ item.key }}</span><label>标题<input v-model="item.title" /></label><label>说明<textarea v-model="item.description" rows="2"></textarea></label></div>
      </div>
      <div v-else-if="active === 'workflow'">
        <div class="editor-heading"><span>产品流程</span><h3>工作流</h3><p>从核验到导出的顺序保持可复核。</p></div>
        <label>栏目标题<input v-model="content.workflow_title" /></label>
        <div v-for="item in content.workflow" :key="item.step" class="repeater workflow-editor"><span>{{ item.step }}</span><label>步骤名<input v-model="item.title" /></label><label>说明<textarea v-model="item.description" rows="2"></textarea></label></div>
      </div>
      <div v-else-if="active === 'tici'">
        <div class="editor-heading"><span>概念解释</span><h3>TICI 专题</h3><p>必须明确这是数据表达思路，不等同于临床结论。</p></div>
        <label>标题<input v-model="content.tici.title" /></label>
        <label>说明<textarea v-model="content.tici.description" rows="6"></textarea></label>
        <label v-for="(_point, index) in content.tici.points" :key="index">要点 {{ Number(index) + 1 }}<input v-model="content.tici.points[Number(index)]" /></label>
        <label>图片替代文本<input v-model="content.tici.image_alt" /></label>
        <label class="asset-picker"><ImagePlus :size="20" /><span>替换 TICI 示例图片<small>不得上传生成式 CT 冒充产品结果</small></span><input type="file" accept="image/jpeg,image/png,image/webp,image/avif" @change="uploadAsset('tici', $event)" /></label>
      </div>
      <div v-else-if="active === 'progress'">
        <div class="editor-heading"><span>事实边界</span><h3>项目进展</h3><p>状态仅允许“已实现、研究中、待验证”。</p></div>
        <label>栏目标题<input v-model="content.progress_title" /></label>
        <div v-for="item in content.progress" :key="item.status" class="repeater"><span>{{ item.label }}</span><label>标题<input v-model="item.title" /></label><label>说明<textarea v-model="item.description" rows="3"></textarea></label></div>
      </div>
      <div v-else-if="active === 'safety'">
        <div class="editor-heading"><span>发布必检</span><h3>安全声明</h3><p>四条声明均需保留，发布检查会再次核验。</p></div>
        <label>标题<input v-model="content.safety.title" /></label>
        <label v-for="(_item, index) in content.safety.statements" :key="index">声明 {{ Number(index) + 1 }}<input v-model="content.safety.statements[Number(index)]" /></label>
      </div>
      <div v-else-if="active === 'background'">
        <div class="editor-heading"><span>项目背景</span><h3>团队介绍</h3><p>默认不展示成员个人信息。</p></div>
        <label>标题<input v-model="content.background.title" /></label>
        <label>介绍<textarea v-model="content.background.description" rows="5"></textarea></label>
        <label>项目归属<input v-model="content.background.affiliation" /></label>
      </div>
      <div v-else-if="active === 'download'">
        <div class="editor-heading"><span>公开下载</span><h3>下载区</h3><p>仅公开独立 TICI Viewer。</p></div>
        <label>标题<input v-model="content.download.title" /></label>
        <label>说明<textarea v-model="content.download.description" rows="5"></textarea></label>
        <label>按钮文字<input v-model="content.download.button_label" /></label>
        <label>无版本提示<input v-model="content.download.fallback_note" /></label>
      </div>
      <div v-else-if="active === 'footer'">
        <div class="editor-heading"><span>页尾信息</span><h3>页脚</h3></div>
        <label>品牌摘要<input v-model="content.footer.summary" /></label>
        <label>版权文字<input v-model="content.footer.copyright" /></label>
        <label>ICP备案号<input v-model="content.footer.icp_number" /></label>
      </div>
      <div v-else>
        <div class="editor-heading"><span>信息架构</span><h3>栏目顺序与显示</h3><p>首屏和页脚固定，下面栏目可以排序或暂时隐藏。</p></div>
        <div v-for="(item, index) in content.section_order" :key="item.key" class="order-row">
          <span>{{ String(Number(index) + 1).padStart(2, '0') }}</span><b>{{ sectionLabel(item.key) }}</b>
          <label class="switch"><input v-model="item.visible" type="checkbox" /><i></i><span>{{ item.visible ? '显示' : '隐藏' }}</span></label>
          <button class="icon-button" :disabled="Number(index) === 0" title="上移" @click="move(Number(index), -1)"><ArrowUp :size="16" /></button>
          <button class="icon-button" :disabled="Number(index) === content.section_order.length - 1" title="下移" @click="move(Number(index), 1)"><ArrowDown :size="16" /></button>
        </div>
      </div>
    </section>

    <aside class="cms-preview-column">
      <section class="panel preview-panel">
        <div class="preview-toolbar"><span><Eye :size="16" />实时预览</span><div><button :class="{ active: device === 'desktop' }" title="桌面预览" @click="device = 'desktop'"><Monitor :size="16" /></button><button :class="{ active: device === 'mobile' }" title="手机预览" @click="device = 'mobile'"><Smartphone :size="16" /></button></div></div>
        <div class="preview-frame" :class="device">
          <div class="mini-nav"><b>朗泰 LungTic</b><span>产品能力　工作流　TICI</span></div>
          <div class="mini-hero"><div><small>{{ content.hero.eyebrow }}</small><h4>{{ content.hero.title }}</h4><p>{{ content.hero.description }}</p><button>{{ content.hero.primary_label }}</button></div><img :src="content.hero.image_asset_id ? '/api/public/assets/' + content.hero.image_asset_id : workbench" :alt="content.hero.image_alt" /></div>
        </div>
      </section>
      <section class="panel publish-panel">
        <div class="panel-heading"><div><span>发布前检查</span><h3>内容校验</h3></div><CheckCircle2 :size="20" /></div>
        <ul><li v-for="(check, index) in checks.slice(0, 7)" :key="index" :class="check.level"><i></i>{{ check.message }}</li></ul>
        <label>发布说明<input v-model="publishNote" :disabled="!canPublish" placeholder="例如：更新体验版下载说明" /></label>
        <button class="primary-button full" :disabled="!canPublish || !publishNote || publishBusy" @click="publish"><Send :size="16" />{{ canPublish ? '发布到官网' : '编辑者无发布权限' }}</button>
      </section>
    </aside>
  </div>
</template>
