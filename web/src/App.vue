<script setup lang="ts">
import { computed } from 'vue';
import { darkTheme, dateZhCN, zhCN, dateEnUS, enUS } from 'naive-ui';
import { useThemeStore } from '@/store/modules/theme';
import { useAppStore } from '@/store/modules/app';

const themeStore = useThemeStore();
const appStore = useAppStore();

const naiveTheme = computed(() => (themeStore.darkMode ? darkTheme : null));
const themeOverrides = computed(() => ({
  common: {
    primaryColor: themeStore.primaryColor,
    primaryColorHover: themeStore.primaryColor,
    primaryColorPressed: themeStore.primaryColor,
    primaryColorSuppl: themeStore.primaryColor,
    borderRadius: '6px'
  }
}));

const locale = computed(() => (appStore.locale === 'en-US' ? enUS : zhCN));
const dateLocale = computed(() => (appStore.locale === 'en-US' ? dateEnUS : dateZhCN));
</script>

<template>
  <n-config-provider
    :theme="naiveTheme"
    :theme-overrides="themeOverrides"
    :locale="locale"
    :date-locale="dateLocale"
  >
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <router-view />
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>
