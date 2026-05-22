<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { projectsApi, type Project, type ProjectAccount } from '@/service/api/projects';
import { accountsApi, type Group } from '@/service/api/accounts';

const message = useMessage();
const dialog = useDialog();

const projects = ref<Project[]>([]);
const groups = ref<Group[]>([]);
const selectedKey = ref<string | null>(null);
const accounts = ref<ProjectAccount[]>([]);
const loading = ref(false);
const filterStatus = ref<string>('');
const keyword = ref('');

// 启动项目对话框
const showStart = ref(false);
const starting = ref(false);
const startForm = ref({
  project_key: '',
  name: '',
  description: '',
  group_ids: [] as number[],
  use_alias_email: false
});

const STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '可领取', value: 'available' },
  { label: '已领取', value: 'claimed' },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '已移除', value: 'removed' }
];

const STATUS_COLOR: Record<string, any> = {
  available: 'info',
  claimed: 'warning',
  success: 'success',
  failed: 'error',
  removed: 'default'
};

async function loadAll() {
  const [p, g] = await Promise.all([projectsApi.list(), accountsApi.listGroups()]);
  projects.value = p.data?.projects || [];
  groups.value = (g.groups || []).filter(x => x.name !== '临时邮箱');
  if (projects.value.length && !selectedKey.value) {
    selectedKey.value = projects.value[0].project_key;
    await loadAccounts();
  }
}

async function loadAccounts() {
  if (!selectedKey.value) return;
  loading.value = true;
  try {
    const r = await projectsApi.accounts(selectedKey.value, {
      status: filterStatus.value || undefined,
      keyword: keyword.value || undefined
    });
    if (r.success && r.data) {
      accounts.value = r.data.accounts || [];
    } else {
      accounts.value = [];
      message.error(r.error || '加载失败');
    }
  } finally {
    loading.value = false;
  }
}

const currentProject = computed(() => projects.value.find(p => p.project_key === selectedKey.value));

async function startProject() {
  if (!startForm.value.project_key.trim()) {
    message.warning('请输入项目 key');
    return;
  }
  starting.value = true;
  try {
    const r = await projectsApi.start({
      project_key: startForm.value.project_key.trim(),
      name: startForm.value.name.trim() || undefined,
      description: startForm.value.description.trim() || undefined,
      group_ids: startForm.value.group_ids.length ? startForm.value.group_ids : undefined,
      use_alias_email: startForm.value.use_alias_email
    });
    if (r.success) {
      message.success(r.message || '项目已启动');
      showStart.value = false;
      selectedKey.value = startForm.value.project_key.trim();
      startForm.value = { project_key: '', name: '', description: '', group_ids: [], use_alias_email: false };
      await loadAll();
      await loadAccounts();
    } else {
      message.error(r.error || '启动失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '启动失败');
  } finally {
    starting.value = false;
  }
}

async function claimOne() {
  if (!selectedKey.value) return;
  try {
    const r = await projectsApi.claimRandom(selectedKey.value, { lease_seconds: 600 });
    if (r.success && r.data) {
      message.success(`已领取 ${r.data.email}`);
      await loadAccounts();
    } else {
      message.warning(r.error || '没有可领取的账号');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '领取失败');
  }
}

async function complete(row: ProjectAccount, kind: 'success' | 'failed') {
  if (!selectedKey.value || !row.claim_token) {
    message.warning('该账号未在领取状态');
    return;
  }
  const api = kind === 'success' ? projectsApi.completeSuccess : projectsApi.completeFailed;
  try {
    const r = await api(selectedKey.value, {
      account_id: row.account_id,
      claim_token: row.claim_token,
      detail: ''
    });
    if (r.success) {
      message.success(kind === 'success' ? '已标记成功' : '已标记失败');
      await loadAccounts();
    } else {
      message.error(r.error || '操作失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '操作失败');
  }
}

async function release(row: ProjectAccount) {
  if (!selectedKey.value || !row.claim_token) return;
  try {
    const r = await projectsApi.release(selectedKey.value, {
      account_id: row.account_id,
      claim_token: row.claim_token
    });
    if (r.success) {
      message.success('已释放');
      await loadAccounts();
    } else {
      message.error(r.error || '释放失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '释放失败');
  }
}

async function resetFailed(row: ProjectAccount) {
  if (!selectedKey.value) return;
  try {
    const r = await projectsApi.resetFailed(selectedKey.value, row.account_id);
    if (r.success) {
      message.success('已重置为可领取');
      await loadAccounts();
    } else {
      message.error(r.error || '重置失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '重置失败');
  }
}

function removeAccount(row: ProjectAccount) {
  if (!selectedKey.value) return;
  dialog.warning({
    title: '移除',
    content: `将账号 ${row.email} 从项目中移除？账号本身不会被删除。`,
    positiveText: '移除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const r = await projectsApi.remove(selectedKey.value!, row.account_id);
        if (r.success) {
          message.success('已移除');
          await loadAccounts();
        } else {
          message.error(r.error || '移除失败');
        }
      } catch (e: any) {
        message.error(e?.response?.data?.error || '移除失败');
      }
    }
  });
}

const columns = computed<DataTableColumns<ProjectAccount>>(() => [
  { title: 'ID', key: 'account_id', width: 70 },
  { title: '邮箱', key: 'email', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const type = STATUS_COLOR[row.status] || 'default';
      return h(NTag, { type, size: 'small', bordered: false }, { default: () => row.status });
    }
  },
  { title: '领取者', key: 'caller_id', width: 140, render: r => r.caller_id || '—' },
  { title: '领取时间', key: 'claimed_at', width: 180 },
  { title: '详情', key: 'detail', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    render: row =>
      h(NSpace, { size: 'small' }, () => {
        const buttons: any[] = [];
        if (row.status === 'claimed') {
          buttons.push(
            h(NButton, { size: 'small', type: 'success', onClick: () => complete(row, 'success') }, { default: () => '成功' }),
            h(NButton, { size: 'small', type: 'error', onClick: () => complete(row, 'failed') }, { default: () => '失败' }),
            h(NButton, { size: 'small', onClick: () => release(row) }, { default: () => '释放' })
          );
        }
        if (row.status === 'failed') {
          buttons.push(
            h(NButton, { size: 'small', onClick: () => resetFailed(row) }, { default: () => '重置' })
          );
        }
        buttons.push(
          h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => removeAccount(row) }, { default: () => '移除' })
        );
        return buttons;
      })
  }
]);

onMounted(loadAll);
</script>

<template>
  <div class="flex flex-col gap-4">
    <n-card title="项目管理">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="selectedKey"
            :options="projects.map(p => ({ label: `${p.project_key}${p.name ? ' · ' + p.name : ''}`, value: p.project_key }))"
            placeholder="选择项目"
            style="width: 280px;"
            size="small"
            @update:value="loadAccounts"
          />
          <n-button size="small" type="primary" @click="showStart = true">
            <Icon icon="tabler:plus" />
            <span class="ml-1">启动/更新项目</span>
          </n-button>
          <n-button size="small" :disabled="!selectedKey" @click="claimOne">
            <Icon icon="tabler:hand-grab" />
            <span class="ml-1">随机领取</span>
          </n-button>
          <n-button size="small" :disabled="!selectedKey" @click="loadAccounts">
            <Icon icon="tabler:refresh" />
          </n-button>
        </n-space>
      </template>

      <n-grid v-if="currentProject" :cols="5" :x-gap="12" :y-gap="8">
        <n-gi>
          <n-statistic label="项目 key" :value="currentProject.project_key" />
        </n-gi>
        <n-gi>
          <n-statistic label="账号总数" :value="currentProject.total_count ?? 0" />
        </n-gi>
        <n-gi>
          <n-statistic label="可领取" :value="currentProject.available_count ?? 0" />
        </n-gi>
        <n-gi>
          <n-statistic label="成功" :value="currentProject.success_count ?? 0" />
        </n-gi>
        <n-gi>
          <n-statistic label="失败" :value="currentProject.failed_count ?? 0" />
        </n-gi>
      </n-grid>
    </n-card>

    <n-card v-if="selectedKey" title="项目账号">
      <template #header-extra>
        <n-space>
          <n-input
            v-model:value="keyword"
            placeholder="搜索邮箱"
            size="small"
            clearable
            style="width: 200px;"
            @keyup.enter="loadAccounts"
          />
          <n-select
            v-model:value="filterStatus"
            :options="STATUS_OPTIONS"
            size="small"
            style="width: 140px;"
            @update:value="loadAccounts"
          />
        </n-space>
      </template>
      <n-data-table
        :columns="columns"
        :data="accounts"
        :loading="loading"
        :max-height="500"
        :bordered="false"
        :row-key="(row: ProjectAccount) => row.account_id"
      />
    </n-card>

    <n-empty v-else description="请先选择或启动一个项目" class="my-12" />

    <!-- 启动项目对话框 -->
    <n-modal
      v-model:show="showStart"
      preset="card"
      title="启动 / 更新项目"
      style="width: 560px;"
    >
      <n-alert type="info" :show-icon="false" class="mb-3">
        指定一个项目 key，系统会把选定分组下的所有"激活"账号加入项目。
        重复 key 会增量同步：新增缺失账号、保留已领取/成功状态。
      </n-alert>
      <n-form label-placement="left" label-width="120">
        <n-form-item label="项目 key" required>
          <n-input v-model:value="startForm.project_key" placeholder="例如 launch-2025-q3" />
        </n-form-item>
        <n-form-item label="项目名称">
          <n-input v-model:value="startForm.name" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="startForm.description" type="textarea" :rows="2" />
        </n-form-item>
        <n-form-item label="包含分组">
          <n-select
            v-model:value="startForm.group_ids"
            multiple
            :options="groups.map(g => ({ label: g.name, value: g.id }))"
            placeholder="留空 = 全部"
          />
        </n-form-item>
        <n-form-item label="使用别名邮箱">
          <n-switch v-model:value="startForm.use_alias_email" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showStart = false">取消</n-button>
          <n-button type="primary" :loading="starting" @click="startProject">启动</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>
