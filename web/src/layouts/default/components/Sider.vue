<script setup lang="ts">
import { computed, h } from 'vue';
import type { MenuOption } from 'naive-ui';
import { NIcon } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { routes } from '@/router/routes';
import { useAppStore } from '@/store/modules/app';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const appStore = useAppStore();

function renderIcon(iconName?: string) {
  if (!iconName) return undefined;
  return () => h(NIcon, null, { default: () => h(Icon, { icon: iconName }) });
}

const menuOptions = computed<MenuOption[]>(() => {
  const mainRoute = routes.find(r => r.path === '/');
  if (!mainRoute || !mainRoute.children) return [];
  return mainRoute.children
    .filter(c => c.meta?.title)
    .map(c => ({
      label: t(c.meta!.title as string),
      key: '/' + c.path,
      icon: renderIcon(c.meta!.icon as string | undefined)
    }));
});

const selectedKey = computed(() => route.path);

function handleSelect(key: string) {
  router.push(key);
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div
      class="h-50px flex items-center justify-center font-bold text-16px border-b border-#eee dark:border-#2c2c32"
    >
      <Icon icon="tabler:mail-bolt" class="text-22px text-primary" />
      <span v-if="!appStore.siderCollapsed" class="ml-2">OutlookEmail</span>
    </div>
    <n-menu
      :collapsed="appStore.siderCollapsed"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :options="menuOptions"
      :value="selectedKey"
      @update:value="handleSelect"
    />
  </div>
</template>
