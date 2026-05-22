<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { accountsApi, type Account, type Group } from '@/service/api/accounts';
import { Icon } from '@iconify/vue';
import InternalEmlImportDialog from '@/components/InternalEmlImportDialog.vue';

const message = useMessage();
const dialog = useDialog();

const accounts = ref<Account[]>([]);
const groups = ref<Group[]>([]);
const total = ref(0);
const loading = ref(false);

const filterGroupId = ref<number | null>(null);
const filterKeyword = ref('');
const filterType = ref<string>('');

const checked = ref<number[]>([]);
const showImport = ref(false);

const TYPE_COLOR: Record<string, string> = {
  outlook: 'info',
  imap: 'success',
  internal_eml: 'warning',
  custom: 'default'
};

const groupLabel = computed(() => {
  const map: Record<number, string> = {};
  groups.value.forEach(g => (map[g.id] = g.name));
  return map;
});

async function loadGroups() {
  const r = await accountsApi.listGroups();
  groups.value = r.groups || [];
}

async function loadAccounts() {
  loading.value = true;
  try {
    const r = await accountsApi.listAccounts({
      group_id: filterGroupId.value ?? undefined,
      keyword: filterKeyword.value.trim() || undefined,
      limit: 200
    });
    let list = r.accounts || [];
    if (filterType.value) {
      list = list.filter(a => a.account_type === filterType.value);
    }
    accounts.value = list;
    total.value = r.total ?? list.length;
  } finally {
    loading.value = false;
  }
}

const columns: DataTableColumns<Account> = [
  { type: 'selection', width: 40 },
  { title: 'ID', key: 'id', width: 70 },
  {
    title: '邮箱',
    key: 'email',
    render: row => h('span', { class: 'text-13px font-medium' }, row.email)
  },
  {
    title: '类型',
    key: 'account_type',
    width: 130,
    render: row =>
      h(
        NTag,
        {
          type: (TYPE_COLOR[row.account_type] as any) || 'default',
          size: 'small',
          bordered: false
        },
        { default: () => row.account_type }
      )
  },
  { title: 'Provider', key: 'provider', width: 110 },
  {
    title: '分组',
    key: 'group_id',
    width: 140,
    render: row => (row.group_id ? groupLabel.value[row.group_id] || '-' : '-')
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: row =>
      h(
        NTag,
        {
          type: row.status === 'active' ? 'success' : 'default',
          size: 'small',
          bordered: false
        },
        { default: () => row.status }
      )
  },
  { title: '备注', key: 'remark', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: row =>
      h(
        NButton,
        {
          size: 'small',
          type: 'error',
          ghost: true,
          onClick: () => deleteOne(row)
        },
        { default: () => '删除' }
      )
  }
];

function onSelect(keys: (string | number)[]) {
  checked.value = keys.map(k => Number(k));
}

function deleteOne(row: Account) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除账号「${row.email}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await accountsApi.deleteAccount(row.id);
        message.success('已删除');
        await loadAccounts();
      } catch (e: any) {
        message.error(e?.response?.data?.error || '删除失败');
      }
    }
  });
}

function batchDelete() {
  if (!checked.value.length) return;
  dialog.warning({
    title: '批量删除',
    content: `确定删除选中的 ${checked.value.length} 个账号？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const r = await accountsApi.batchDelete(checked.value);
        message.success(r.message || `已删除 ${r.deleted_count || 0} 个`);
        checked.value = [];
        await loadAccounts();
      } catch (e: any) {
        message.error(e?.response?.data?.error || '删除失败');
      }
    }
  });
}

onMounted(async () => {
  await loadGroups();
  await loadAccounts();
});
</script>

<template>
  <n-card>
    <template #header>
      <span>账号管理</span>
      <n-tag size="small" class="ml-2" :bordered="false">共 {{ total }} 个</n-tag>
    </template>
    <template #header-extra>
      <n-space>
        <n-button @click="loadAccounts">
          <Icon icon="tabler:refresh" /> <span class="ml-1">刷新</span>
        </n-button>
        <n-button type="primary" @click="showImport = true">
          <Icon icon="tabler:plus" /> <span class="ml-1">添加内网邮箱</span>
        </n-button>
      </n-space>
    </template>

    <n-space class="mb-3" :wrap-item="false">
      <n-input
        v-model:value="filterKeyword"
        placeholder="搜索邮箱/备注"
        clearable
        style="width: 260px;"
        @keyup.enter="loadAccounts"
      />
      <n-select
        v-model:value="filterGroupId"
        :options="[
          { label: '全部分组', value: 0 },
          ...groups.map(g => ({ label: g.name, value: g.id }))
        ]"
        placeholder="分组"
        style="width: 180px;"
        @update:value="(v: number) => { filterGroupId = v === 0 ? null : v; loadAccounts(); }"
      />
      <n-select
        v-model:value="filterType"
        :options="[
          { label: '全部类型', value: '' },
          { label: 'Outlook OAuth', value: 'outlook' },
          { label: 'IMAP', value: 'imap' },
          { label: '内网 EML', value: 'internal_eml' }
        ]"
        placeholder="类型"
        style="width: 180px;"
        @update:value="loadAccounts"
      />
      <n-button @click="loadAccounts">
        <Icon icon="tabler:search" /> <span class="ml-1">查询</span>
      </n-button>
      <n-button
        type="error"
        :disabled="!checked.length"
        @click="batchDelete"
      >
        <Icon icon="tabler:trash" />
        <span class="ml-1">批量删除 ({{ checked.length }})</span>
      </n-button>
    </n-space>

    <n-data-table
      remote
      :columns="columns"
      :data="accounts"
      :loading="loading"
      :row-key="(row: Account) => row.id"
      :bordered="false"
      :max-height="500"
      @update:checked-row-keys="onSelect"
    />

    <InternalEmlImportDialog v-model:show="showImport" @created="loadAccounts" />
  </n-card>
</template>
