<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { useMessage, NTag, NButton } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { forwardingApi } from '@/service/api/forwarding';

interface ForwardingLog {
  id: number;
  account_id: number;
  account_email: string;
  message_id: string;
  channel: string;
  status: string;
  error_message: string | null;
  created_at: string;
}

const message = useMessage();
const tab = ref<'all' | 'failed'>('all');
const logs = ref<ForwardingLog[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const r = tab.value === 'failed' ? await forwardingApi.failedLogs() : await forwardingApi.logs({ per_page: 200 });
    logs.value = (r.logs || []) as ForwardingLog[];
  } catch (e: any) {
    message.error(e?.response?.data?.error || '加载失败');
  } finally {
    loading.value = false;
  }
}

const columns = computed<DataTableColumns<ForwardingLog>>(() => [
  { title: '时间', key: 'created_at', width: 170 },
  { title: '账号', key: 'account_email' },
  {
    title: '渠道',
    key: 'channel',
    width: 110,
    render: r => h(NTag, { size: 'small', bordered: false }, { default: () => r.channel || '—' })
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: r => {
      const t: any = r.status === 'success' ? 'success' : r.status === 'failed' ? 'error' : 'default';
      return h(NTag, { size: 'small', type: t, bordered: false }, { default: () => r.status });
    }
  },
  { title: '消息 ID', key: 'message_id', ellipsis: { tooltip: true }, width: 200 },
  { title: '错误', key: 'error_message', ellipsis: { tooltip: true } }
]);

onMounted(load);
</script>

<template>
  <n-card title="转发历史">
    <template #header-extra>
      <n-button @click="load">
        <Icon icon="tabler:refresh" />
        <span class="ml-1">刷新</span>
      </n-button>
    </template>

    <n-tabs v-model:value="tab" type="line" size="small" class="mb-3" @update:value="load">
      <n-tab-pane name="all" tab="全部" />
      <n-tab-pane name="failed" tab="失败" />
    </n-tabs>

    <n-data-table
      :columns="columns"
      :data="logs"
      :loading="loading"
      :max-height="600"
      :bordered="false"
    />
  </n-card>
</template>
