<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { accountsApi, type Account } from '@/service/api/accounts';

const accounts = ref<Account[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const res = await accountsApi.listAccounts();
    accounts.value = res.accounts || [];
  } finally {
    loading.value = false;
  }
}

onMounted(load);

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '邮箱', key: 'email' },
  { title: '类型', key: 'account_type', width: 120 },
  { title: 'Provider', key: 'provider', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '备注', key: 'remark' }
];
</script>

<template>
  <n-card>
    <template #header>账号管理</template>
    <template #header-extra>
      <n-button type="primary" @click="load">刷新</n-button>
    </template>
    <n-data-table
      :columns="columns"
      :data="accounts"
      :loading="loading"
      :pagination="{ pageSize: 20 }"
      :bordered="false"
    />
  </n-card>
</template>
