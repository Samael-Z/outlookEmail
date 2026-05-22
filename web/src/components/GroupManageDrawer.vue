<script setup lang="ts">
import { ref, watch, h } from 'vue';
import { useMessage, useDialog, NButton, NSpace } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { accountsApi, type Group } from '@/service/api/accounts';
import { Icon } from '@iconify/vue';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void;
  (e: 'changed'): void;
}>();

const message = useMessage();
const dialog = useDialog();

const groups = ref<Group[]>([]);
const loading = ref(false);

const editing = ref<Group | null>(null);
const form = ref({
  name: '',
  description: '',
  color: '#646cff',
  proxy_url: ''
});
const submitting = ref(false);

async function load() {
  loading.value = true;
  try {
    const r = await accountsApi.listGroups();
    groups.value = r.groups || [];
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.show,
  v => {
    if (v) load();
  }
);

function resetForm() {
  form.value = { name: '', description: '', color: '#646cff', proxy_url: '' };
  editing.value = null;
}

function startEdit(g: Group) {
  editing.value = g;
  form.value = {
    name: g.name,
    description: g.description || '',
    color: g.color || '#646cff',
    proxy_url: (g as any).proxy_url || ''
  };
}

async function submit() {
  if (!form.value.name.trim()) {
    message.warning('请输入分组名称');
    return;
  }
  submitting.value = true;
  try {
    if (editing.value) {
      const r = await accountsApi.updateGroup(editing.value.id, form.value);
      if (r.success) {
        message.success('已更新');
        resetForm();
        await load();
        emit('changed');
      } else {
        message.error(r.error || '更新失败');
      }
    } else {
      const r = await accountsApi.createGroup(form.value);
      if (r.success) {
        message.success('已创建');
        resetForm();
        await load();
        emit('changed');
      } else {
        message.error(r.error || '创建失败');
      }
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '操作失败');
  } finally {
    submitting.value = false;
  }
}

function remove(g: Group) {
  if (g.is_system) {
    message.warning('系统分组不可删除');
    return;
  }
  dialog.warning({
    title: '确认删除',
    content: `删除分组「${g.name}」？该分组下的账号会被移到默认分组。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const r = await accountsApi.deleteGroup(g.id);
        if (r.success) {
          message.success('已删除');
          await load();
          emit('changed');
        } else {
          message.error(r.error || '删除失败');
        }
      } catch (e: any) {
        message.error(e?.response?.data?.error || '删除失败');
      }
    }
  });
}

const columns: DataTableColumns<Group> = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '名称',
    key: 'name',
    render: row =>
      h('div', { class: 'flex-y-center' }, [
        h('span', {
          style: `display:inline-block;width:10px;height:10px;border-radius:50%;background:${row.color};margin-right:6px;`
        }),
        h('span', null, row.name)
      ])
  },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  { title: '排序', key: 'sort_order', width: 70 },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: row =>
      h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          { size: 'small', onClick: () => startEdit(row) },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            ghost: true,
            disabled: !!row.is_system,
            onClick: () => remove(row)
          },
          { default: () => '删除' }
        )
      ])
  }
];
</script>

<template>
  <n-drawer
    :show="show"
    :width="640"
    placement="right"
    @update:show="emit('update:show', $event)"
  >
    <n-drawer-content title="分组管理" closable>
      <n-card size="small" class="mb-3">
        <template #header>
          {{ editing ? `编辑分组: ${editing.name}` : '新建分组' }}
        </template>
        <n-form label-placement="left" label-width="80" size="small">
          <n-form-item label="名称" required>
            <n-input v-model:value="form.name" placeholder="必填" />
          </n-form-item>
          <n-form-item label="描述">
            <n-input v-model:value="form.description" placeholder="可选" />
          </n-form-item>
          <n-form-item label="颜色">
            <n-color-picker v-model:value="form.color" :show-alpha="false" />
          </n-form-item>
          <n-form-item label="代理 URL">
            <n-input
              v-model:value="form.proxy_url"
              placeholder="http://127.0.0.1:7890 或 socks5://..."
            />
          </n-form-item>
          <n-form-item :show-label="false">
            <n-space>
              <n-button type="primary" :loading="submitting" @click="submit">
                {{ editing ? '保存修改' : '创建分组' }}
              </n-button>
              <n-button v-if="editing" @click="resetForm">取消</n-button>
            </n-space>
          </n-form-item>
        </n-form>
      </n-card>

      <n-data-table
        :columns="columns"
        :data="groups"
        :loading="loading"
        :row-key="(row: Group) => row.id"
        size="small"
      />

      <template #footer>
        <n-button @click="emit('update:show', false)">关闭</n-button>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>
