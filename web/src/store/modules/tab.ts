import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { RouteLocationNormalized } from 'vue-router';

export interface TabItem {
  fullPath: string;
  name: string;
  title: string;
  icon?: string;
  closable: boolean;
}

export const useTabStore = defineStore('tab', () => {
  const tabs = ref<TabItem[]>([]);
  const activeTab = ref<string>('');

  function addTab(route: RouteLocationNormalized) {
    const fullPath = route.fullPath;
    activeTab.value = fullPath;
    if (tabs.value.find(t => t.fullPath === fullPath)) return;
    tabs.value.push({
      fullPath,
      name: String(route.name || fullPath),
      title: (route.meta?.title as string) || String(route.name || fullPath),
      icon: route.meta?.icon as string | undefined,
      closable: route.path !== '/home'
    });
  }

  function removeTab(fullPath: string): string | undefined {
    const idx = tabs.value.findIndex(t => t.fullPath === fullPath);
    if (idx < 0) return;
    tabs.value.splice(idx, 1);
    if (activeTab.value === fullPath) {
      const next = tabs.value[idx] || tabs.value[idx - 1];
      activeTab.value = next?.fullPath || '';
      return activeTab.value || '/home';
    }
  }

  function clearTabs(keepFullPath?: string) {
    tabs.value = tabs.value.filter(t => !t.closable || t.fullPath === keepFullPath);
  }

  return { tabs, activeTab, addTab, removeTab, clearTabs };
});
