<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import { useAppStore } from '@/store/modules/app';
import { useThemeStore } from '@/store/modules/theme';
import { useAuthStore } from '@/store/modules/auth';
import { setLocale } from '@/locales';
import GlobalSearch from '@/components/GlobalSearch.vue';

const router = useRouter();
const { t } = useI18n();
const appStore = useAppStore();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const message = useMessage();

function toggleLocale() {
  const next = appStore.locale === 'zh-CN' ? 'en-US' : 'zh-CN';
  appStore.setLocale(next);
  setLocale(next);
}

async function handleLogout() {
  await authStore.logout();
  message.success(t('common.success'));
  router.push('/login');
}
</script>

<template>
  <div class="flex-y-center w-full">
    <n-button text @click="appStore.toggleSider()">
      <Icon
        :icon="appStore.siderCollapsed ? 'tabler:layout-sidebar-left-expand' : 'tabler:layout-sidebar-left-collapse'"
        class="text-20px"
      />
    </n-button>

    <div class="flex-1" />

    <GlobalSearch class="mr-3" />

    <n-button text class="mr-3" @click="toggleLocale">
      <Icon icon="tabler:language" class="text-18px" />
      <span class="ml-1 text-12px">{{ appStore.locale === 'zh-CN' ? '中' : 'EN' }}</span>
    </n-button>

    <n-button text class="mr-3" @click="themeStore.toggleDark()">
      <Icon
        :icon="themeStore.darkMode ? 'tabler:sun' : 'tabler:moon'"
        class="text-18px"
      />
    </n-button>

    <n-dropdown
      trigger="click"
      :options="[{ label: t('common.logout'), key: 'logout' }]"
      @select="handleLogout"
    >
      <n-button text>
        <Icon icon="tabler:user-circle" class="text-22px" />
      </n-button>
    </n-dropdown>
  </div>
</template>
