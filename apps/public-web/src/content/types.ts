export type ProgressStatus = 'implemented' | 'researching' | 'pending'

export interface SiteContent {
  schema_version: 1
  seo: { title: string; description: string; keywords: string[] }
  navigation: Array<{ label: string; anchor: string }>
  hero: {
    eyebrow: string
    title: string
    description: string
    primary_label: string
    secondary_label: string
    image_alt: string
    image_asset_id?: string | null
  }
  capabilities_title: string
  capabilities_intro: string
  capabilities: Array<{ key: string; title: string; description: string }>
  workflow_title: string
  workflow: Array<{ step: string; title: string; description: string }>
  tici: {
    eyebrow: string
    title: string
    description: string
    points: string[]
    image_alt: string
    image_asset_id?: string | null
  }
  progress_title: string
  progress: Array<{
    status: ProgressStatus
    label: string
    title: string
    description: string
  }>
  safety: { title: string; statements: string[] }
  background: { title: string; description: string; affiliation: string }
  download: {
    eyebrow: string
    title: string
    description: string
    button_label: string
    fallback_note: string
  }
  footer: { summary: string; copyright: string; icp_number: string }
  section_order: Array<{
    key: 'capabilities' | 'workflow' | 'tici' | 'progress' | 'safety' | 'background' | 'download'
    visible: boolean
  }>
}

export interface ReleaseSummary {
  id: string
  version: string
  channel: string
  platform: string
  release_notes: string
  file_name: string
  byte_size: number
  sha256: string
  published_at: string
  download_url: string
}
