<script setup lang="ts">
import { useRouter } from 'vue-router';
const router = useRouter();
</script>

<template>
  <div class="wh-full flex-col-center" style="height: 100vh; background: #f5f7fa;">
    <div class="text-80px font-bold op-30">404</div>
    <div class="text-14px op-70 mb-4">页面未找到</div>
    <n-button type="primary" @click="router.push('/home')">回到首页</n-button>
  </div>
</template>
