import { createRouter, createWebHistory } from 'vue-router'
import AuditView from './views/AuditView.vue'
import CmsView from './views/CmsView.vue'
import DashboardView from './views/DashboardView.vue'
import HistoryView from './views/HistoryView.vue'
import ReleasesView from './views/ReleasesView.vue'
import SettingsView from './views/SettingsView.vue'
import UploadView from './views/UploadView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/uploads', name: 'uploads', component: UploadView },
    { path: '/releases', name: 'releases', component: ReleasesView },
    { path: '/content', name: 'content', component: CmsView },
    { path: '/content/history', name: 'history', component: HistoryView },
    { path: '/audit', name: 'audit', component: AuditView },
    { path: '/settings', name: 'settings', component: SettingsView },
  ],
})
