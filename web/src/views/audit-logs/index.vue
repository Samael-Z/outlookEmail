<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { useMessage, NTag } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { systemApi, type AuditLog } from '@/service/api/system';

const message = useMessage();

const logs = ref<AuditLog[]>([]);
const total = ref(0);
const page = ref(1);
const perPage = 50;
const loading = ref(false);

const action = ref<string>('');
const resourceType = ref<string>('');
const keyword = ref('');
const actionOptions = ref<Array<{ label: string; value: string }>>([]);
const resourceTypeOptions = ref<Array<{ label: string; value: string }>>([]);

const ACTION_COLOR: Record<string, any> = {
  create: 'success',
  add: 'success',
  update: 'info',
  edit: 'info',
  delete: 'error',
  remove: 'error',
  export: 'warning',
  import: 'warning',
  start: 'info',
  refresh: 'default'
};

async function load() {
  loading.value = true;
  try {
    const r = await systemApi.auditLogs({
      page: page.value,
      per_page: perPage,
      action: action.value || undefined,
      resource_type: resourceType.value || undefined,
      keyword: keyword.value.trim() || undefined
    });
    logs.value = r.logs || [];
    total.value = r.total || 0;
    actionOptions.value = [
      { label: '全部动作', value: '' },
      ...(r.distinct_actions || []).map(a => ({ label: a, value: a }))
    ];
    resourceTypeOptions.value = [
      { label: '全部资源类型', value: '' },
      ...(r.distinct_resource_types || []).map(t => ({ label: t, value: t }))
    ];
  } catch (e: any) {
    message.error(e?.response?.data?.error || '加载失败');
  } finally {
    loading.value = false;
  }
}

const columns = computed<DataTableColumns<AuditLog>>(() => [
  { title: '时间', key: 'created_at', width: 170 },
  {
    title: '动作',
    key: 'action',
    width: 110,
    render: row => {
      const type = ACTION_COLOR[row.action.toLowerCase()] || 'default';
      return h(NTag, { type, size: 'small', bordered: false }, { default: () => row.action });
    }
  },
  { title: '资源类型', key: 'resource_type', width: 140 },
  { title: '资源 ID', key: 'resource_id', width: 200, ellipsis: { tooltip: true } },
  { title: 'IP', key: 'user_ip', width: 140 },
  { title: '详情', key: 'details', ellipsis: { tooltip: true } }
]);

onMounted(load);
</script>

<template>
  <n-card title="审计日志">
    <template #header-extra>
      <n-button @click="load">
        <Icon icon="tabler:refresh" />
        <span class="ml-1">刷新</span>
      </n-button>
    </template>

    <n-space class="mb-3" :wrap-item="false">
      <n-input
        v-model:value="keyword"
        placeholder="搜索详情/资源 ID/IP"
        clearable
        style="width: 260px;"
        @keyup.enter="page = 1; load();"
      />
      <n-select
        v-model:value="action"
        :options="actionOptions"
        placeholder="动作"
        style="width: 160px;"
        @update:value="() => { page = 1; load(); }"
      />
      <n-select
        v-model:value="resourceType"
        :options="resourceTypeOptions"
        placeholder="资源类型"
        style="width: 180px;"
        @update:value="() => { page = 1; load(); }"
      />
      <n-button @click="page = 1; load();">
        <Icon icon="tabler:search" />
        <span class="ml-1">查询</span>
      </n-button>
    </n-space>

    <n-data-table
      :columns="columns"
      :data="logs"
      :loading="loading"
      :max-height="500"
      :bordered="false"
      :row-key="(row: AuditLog) => row.id"
    />

    <n-pagination
      v-if="total > 0"
      v-model:page="page"
      :page-size="perPage"
      :item-count="total"
      class="mt-3 justify-end"
      @update:page="load"
    />
  </n-card>
</template>
