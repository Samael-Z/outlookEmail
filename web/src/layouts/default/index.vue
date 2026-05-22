<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useAppStore } from '@/store/modules/app';
import { useTabStore } from '@/store/modules/tab';
import LayoutSider from './components/Sider.vue';
import LayoutHeader from './components/Header.vue';
import LayoutTabBar from './components/TabBar.vue';

const appStore = useAppStore();
const tabStore = useTabStore();
const route = useRoute();

// 进入主布局时把当前路由加入标签页
onMounted(() => {
  tabStore.addTab(route);
});

watch(
  () => route.fullPath,
  () => tabStore.addTab(route)
);

const siderWidth = computed(() => (appStore.siderCollapsed ? 64 : 220));
</script>

<template>
  <n-layout has-sider class="h-screen">
    <n-layout-sider
      bordered
      :width="siderWidth"
      :collapsed-width="64"
      :collapsed="appStore.siderCollapsed"
      collapse-mode="width"
      :native-scrollbar="false"
    >
      <LayoutSider />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="h-50px flex items-center px-4">
        <LayoutHeader />
      </n-layout-header>

      <LayoutTabBar />

      <n-layout-content
        class="bg-#f5f7fa dark:bg-#101014"
        content-style="padding: 16px; height: calc(100vh - 50px - 40px);"
        :native-scrollbar="false"
      >
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" :key="route.fullPath" />
          </keep-alive>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.h-50px {
  height: 50px;
}
</style>
