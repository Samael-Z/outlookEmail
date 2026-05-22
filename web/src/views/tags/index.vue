<script setup lang="ts">
import { ref, onMounted, h } from 'vue';
import { useMessage, useDialog, NButton } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { tagsApi, type Tag } from '@/service/api/tags';

const message = useMessage();
const dialog = useDialog();

const tags = ref<Tag[]>([]);
const loading = ref(false);

const form = ref({ name: '', color: '#646cff' });
const submitting = ref(false);

const presetColors = [
  '#646cff',
  '#2080f0',
  '#18a058',
  '#f0a020',
  '#d03050',
  '#7c3aed',
  '#10b981',
  '#0ea5e9'
];

async function load() {
  loading.value = true;
  try {
    const r = await tagsApi.list();
    tags.value = r.tags || [];
  } finally {
    loading.value = false;
  }
}

async function create() {
  if (!form.value.name.trim()) {
    message.warning('请输入标签名称');
    return;
  }
  submitting.value = true;
  try {
    const r = await tagsApi.create(form.value);
    if (r.success) {
      message.success('已创建');
      form.value = { name: '', color: '#646cff' };
      await load();
    } else {
      message.error(r.error || '创建失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '创建失败');
  } finally {
    submitting.value = false;
  }
}

function remove(t: Tag) {
  dialog.warning({
    title: '确认删除',
    content: `删除标签「${t.name}」？已挂在账号上的标签关联也会一并解除。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const r = await tagsApi.delete(t.id);
        if (r.success) {
          message.success('已删除');
          await load();
        } else {
          message.error(r.error || '删除失败');
        }
      } catch (e: any) {
        message.error(e?.response?.data?.error || '删除失败');
      }
    }
  });
}

const columns: DataTableColumns<Tag> = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '名称',
    key: 'name',
    render: row =>
      h('div', { class: 'flex-y-center' }, [
        h('span', {
          style: `display:inline-block;width:12px;height:12px;border-radius:3px;background:${row.color};margin-right:8px;`
        }),
        h('span', null, row.name)
      ])
  },
  { title: '颜色', key: 'color' },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: row =>
      h(
        NButton,
        { size: 'small', type: 'error', ghost: true, onClick: () => remove(row) },
        { default: () => '删除' }
      )
  }
];

onMounted(load);
</script>

<template>
  <div class="flex flex-col gap-4">
    <n-card title="新建标签">
      <n-form inline label-placement="left">
        <n-form-item label="名称">
          <n-input v-model:value="form.name" placeholder="如：高优先级" style="width: 180px;" />
        </n-form-item>
        <n-form-item label="颜色">
          <n-space>
            <div
              v-for="c in presetColors"
              :key="c"
              @click="form.color = c"
              :style="{
                background: c,
                width: '24px',
                height: '24px',
                borderRadius: '4px',
                cursor: 'pointer',
                border: form.color === c ? '3px solid #fff' : '1px solid #ddd',
                boxShadow: form.color === c ? `0 0 0 2px ${c}` : 'none'
              }"
            />
            <n-color-picker
              v-model:value="form.color"
              :show-alpha="false"
              size="small"
              style="width: 130px;"
            />
          </n-space>
        </n-form-item>
        <n-form-item>
          <n-button type="primary" :loading="submitting" @click="create">
            <Icon icon="tabler:plus" />
            <span class="ml-1">创建</span>
          </n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <n-card title="标签列表">
      <template #header-extra>
        <n-button @click="load">
          <Icon icon="tabler:refresh" />
        </n-button>
      </template>
      <n-data-table
        :columns="columns"
        :data="tags"
        :loading="loading"
        :bordered="false"
        :row-key="(row: Tag) => row.id"
      />
    </n-card>
  </div>
</template>
