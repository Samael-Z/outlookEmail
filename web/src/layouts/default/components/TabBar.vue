<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useTabStore } from '@/store/modules/tab';

const tabStore = useTabStore();
const router = useRouter();
const route = useRoute();
const { t } = useI18n();

const tabs = computed(() =>
  tabStore.tabs.map(tab => ({
    ...tab,
    displayTitle: tab.title.includes('.') ? t(tab.title) : tab.title
  }))
);

function handleClick(fullPath: string) {
  if (fullPath !== route.fullPath) router.push(fullPath);
}

function handleClose(fullPath: string) {
  const next = tabStore.removeTab(fullPath);
  if (next) router.push(next);
}
</script>

<template>
  <div
    class="h-40px bg-white dark:bg-#18181c border-b border-#eee dark:border-#2c2c32 flex-y-center px-2 overflow-x-auto"
  >
    <n-tabs
      type="card"
      size="small"
      :value="tabStore.activeTab"
      closable
      class="flex-1"
      @update:value="handleClick"
      @close="handleClose"
    >
      <n-tab-pane
        v-for="tab in tabs"
        :key="tab.fullPath"
        :name="tab.fullPath"
        :tab="tab.displayTitle"
        :closable="tab.closable"
        display-directive="show"
      />
    </n-tabs>
  </div>
</template>

<style scoped>
.h-40px {
  height: 40px;
}
</style>
