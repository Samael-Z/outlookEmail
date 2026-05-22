import type { App } from 'vue';
import { createI18n } from 'vue-i18n';
import zhCN from './zh-CN';
import enUS from './en-US';
import { useAppStore } from '@/store/modules/app';

let i18n: ReturnType<typeof createI18n> | null = null;

export function setupI18n(app: App) {
  const appStore = useAppStore();
  i18n = createI18n({
    legacy: false,
    locale: appStore.locale,
    fallbackLocale: 'zh-CN',
    messages: { 'zh-CN': zhCN, 'en-US': enUS }
  });
  app.use(i18n);
}

export function setLocale(locale: 'zh-CN' | 'en-US') {
  if (i18n) {
    (i18n.global.locale as any).value = locale;
  }
}

export function t(key: string): string {
  if (!i18n) return key;
  return (i18n.global.t as any)(key);
}
