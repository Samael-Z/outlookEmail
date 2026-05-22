<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, h } from 'vue';
import { useMessage, useDialog, NTag, NButton } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { accountsApi, type Account } from '@/service/api/accounts';
import { refreshApi } from '@/service/api/refresh';

const message = useMessage();
const dialog = useDialog();

const accounts = ref<Account[]>([]);
const loading = ref(false);
const checked = ref<number[]>([]);

// 进度状态
const running = ref(false);
const total = ref(0);
const current = ref(0);
const successCount = ref(0);
const failedCount = ref(0);
const eventLog = ref<Array<{ type: string; email?: string; status?: string; error?: string; time: string }>>([]);

let eventSource: EventSource | null = null;

async function load() {
  loading.value = true;
  try {
    const r = await accountsApi.listAccounts({ limit: 500 });
    // 只显示 outlook 类型（其他类型没有 token 概念）
    accounts.value = (r.accounts || []).filter(a => a.account_type === 'outlook');
  } finally {
    loading.value = false;
  }
}

const progressPercent = computed(() => {
  if (total.value === 0) return 0;
  return Math.round((current.value / total.value) * 100);
});

function pushLog(entry: { type: string; email?: string; status?: string; error?: string }) {
  const time = new Date().toLocaleTimeString();
  eventLog.value.unshift({ ...entry, time });
  if (eventLog.value.length > 500) eventLog.value.pop();
}

function startSseSubscription(streamUrl: string) {
  if (eventSource) {
    eventSource.close();
  }
  running.value = true;
  current.value = 0;
  successCount.value = 0;
  failedCount.value = 0;
  total.value = 0;
  eventLog.value = [];

  eventSource = new EventSource(streamUrl, { withCredentials: true });
  eventSource.onmessage = ev => {
    try {
      const data = JSON.parse(ev.data);
      switch (data.type) {
        case 'start':
          total.value = data.total || 0;
          pushLog({ type: '开始', email: `共 ${total.value} 个账号` });
          break;
        case 'progress':
          current.value = data.current || 0;
          successCount.value = data.success_count || 0;
          failedCount.value = data.failed_count || 0;
          break;
        case 'account_result':
          pushLog({
            type: data.status === 'success' ? '✓ 成功' : '✗ 失败',
            email: data.email,
            error: data.error_message
          });
          successCount.value = data.success_count || 0;
          failedCount.value = data.failed_count || 0;
          break;
        case 'complete':
          pushLog({
            type: '完成',
            email: `成功 ${data.success_count}, 失败 ${data.failed_count}`
          });
          running.value = false;
          stopSse();
          break;
        case 'error':
        case 'conflict':
          pushLog({ type: '错误', error: data.message });
          running.value = false;
          stopSse();
          break;
      }
    } catch (e) {
      console.error('parse SSE:', e);
    }
  };
  eventSource.onerror = () => {
    if (running.value) {
      pushLog({ type: '连接中断' });
      running.value = false;
    }
    stopSse();
  };
}

function stopSse() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

async function refreshSelected() {
  if (!checked.value.length) {
    message.warning('请勾选要刷新的账号');
    return;
  }
  try {
    const r = await refreshApi.createSelectedTask(checked.value);
    if (!r.success) {
      message.error(r.error || '初始化任务失败');
      return;
    }
    startSseSubscription(r.stream_url);
  } catch (e: any) {
    message.error(e?.response?.data?.error || '启动失败');
  }
}

function retryFailedStream() {
  startSseSubscription('/api/accounts/refresh-failed-stream');
}

async function retryFailedNonStream() {
  dialog.warning({
    title: '重试失败账号',
    content: '将一次性重试所有失败的 Outlook 账号 Token 刷新，可能耗时较长。',
    positiveText: '开始',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const r = await refreshApi.retryFailed();
        message.success(`完成：成功 ${r.success_count}，失败 ${r.failed_count}`);
        await load();
      } catch (e: any) {
        message.error(e?.response?.data?.error || '重试失败');
      }
    }
  });
}

async function refreshOne(account: Account) {
  try {
    const r = await refreshApi.refreshOne(account.id);
    if (r.success) {
      message.success(`${account.email} 刷新成功`);
    } else {
      message.error(r.error || r.error_message || '刷新失败');
    }
    await load();
  } catch (e: any) {
    message.error(e?.response?.data?.error || '刷新失败');
  }
}

const columns: DataTableColumns<Account> = [
  { type: 'selection', width: 40 },
  { title: 'ID', key: 'id', width: 70 },
  { title: '邮箱', key: 'email' },
  {
    title: '最近刷新',
    key: 'last_refresh_at' as any,
    width: 180,
    render: row => (row as any).last_refresh_at || '—'
  },
  {
    title: '状态',
    key: 'last_refresh_status' as any,
    width: 100,
    render: row => {
      const s = (row as any).last_refresh_status || 'never';
      const type: any = s === 'success' ? 'success' : s === 'failed' ? 'error' : 'default';
      return h(NTag, { size: 'small', type, bordered: false }, { default: () => s });
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: row =>
      h(
        NButton,
        { size: 'small', onClick: () => refreshOne(row) },
        { default: () => '刷新' }
      )
  }
];

onMounted(load);
onBeforeUnmount(stopSse);
</script>

<template>
  <div class="flex flex-col gap-3">
    <n-card title="Token 刷新管理">
      <template #header-extra>
        <n-space>
          <n-button :disabled="running" @click="refreshSelected">
            <Icon icon="tabler:refresh" />
            <span class="ml-1">刷新选中 ({{ checked.length }})</span>
          </n-button>
          <n-button :disabled="running" type="warning" @click="retryFailedStream">
            <Icon icon="tabler:reload" />
            <span class="ml-1">重试失败（流式）</span>
          </n-button>
          <n-button :disabled="running" @click="retryFailedNonStream">
            重试失败（一次性）
          </n-button>
        </n-space>
      </template>

      <n-card v-if="running || eventLog.length" size="small" class="mb-3">
        <template #header>
          <span class="text-13px">
            进度: {{ current }} / {{ total }} · 成功 {{ successCount }} · 失败 {{ failedCount }}
          </span>
        </template>
        <n-progress
          type="line"
          :percentage="progressPercent"
          :status="running ? 'default' : failedCount > 0 ? 'warning' : 'success'"
          :indicator-placement="'inside'"
        />
        <n-scrollbar class="mt-2" style="max-height: 200px;">
          <div
            v-for="(log, i) in eventLog"
            :key="i"
            class="text-12px py-1 border-b border-#eee dark:border-#2c2c32 last:border-0"
          >
            <span class="op-50 mr-2">{{ log.time }}</span>
            <span
              :class="log.type.includes('成功') ? 'text-success' : log.type.includes('失败') || log.type.includes('错误') ? 'text-error' : ''"
            >
              [{{ log.type }}]
            </span>
            <span class="ml-2">{{ log.email }}</span>
            <span v-if="log.error" class="text-error ml-2">{{ log.error }}</span>
          </div>
        </n-scrollbar>
      </n-card>

      <n-data-table
        :columns="columns"
        :data="accounts"
        :loading="loading"
        :row-key="(row: Account) => row.id"
        :max-height="500"
        @update:checked-row-keys="(keys: any[]) => checked = keys.map(k => Number(k))"
      />
    </n-card>
  </div>
</template>
