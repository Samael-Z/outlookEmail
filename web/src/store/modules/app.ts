import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export type LocaleKey = 'zh-CN' | 'en-US';

export const useAppStore = defineStore('app', () => {
  const locale = useStorage<LocaleKey>('outlook-email:locale', 'zh-CN');
  const siderCollapsed = useStorage('outlook-email:sider-collapsed', false);

  function setLocale(value: LocaleKey) {
    locale.value = value;
  }

  function toggleSider() {
    siderCollapsed.value = !siderCollapsed.value;
  }

  return { locale, siderCollapsed, setLocale, toggleSider };
});
