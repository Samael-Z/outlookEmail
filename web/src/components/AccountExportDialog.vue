<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMessage } from 'naive-ui';
import axios from 'axios';
import { Icon } from '@iconify/vue';
import { accountsApi, type Group } from '@/service/api/accounts';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{ (e: 'update:show', v: boolean): void }>();

const message = useMessage();

const mode = ref<'all' | 'selected' | 'single'>('all');
const password = ref('');
const groups = ref<Group[]>([]);
const selectedGroupIds = ref<number[]>([]);
const singleGroupId = ref<number | null>(null);
const submitting = ref(false);

watch(
  () => props.show,
  async v => {
    if (v) {
      password.value = '';
      const r = await accountsApi.listGroups();
      groups.value = r.groups || [];
      if (groups.value.length && !singleGroupId.value) {
        singleGroupId.value = groups.value[0].id;
      }
    }
  }
);

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function parseFilename(disposition: string, fallback: string): string {
  const utf = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf) return decodeURIComponent(utf[1]);
  const ascii = disposition.match(/filename="([^"]+)"/);
  if (ascii) return ascii[1];
  return fallback;
}

async function getCsrfHeader(): Promise<Record<string, string>> {
  try {
    const r = await axios.get('/api/csrf-token', { withCredentials: true });
    const t = r.data?.csrf_token;
    return t ? { 'X-CSRF-Token': t, 'X-CSRFToken': t } : {};
  } catch {
    return {};
  }
}

async function doExport() {
  if (!password.value) {
    message.warning('请输入登录密码');
    return;
  }
  submitting.value = true;
  try {
    const verify = await accountsApi.verifyExportPassword(password.value);
    if (!verify.success || !verify.verify_token) {
      message.error(verify.error || '密码验证失败');
      return;
    }
    const token = verify.verify_token;
    const csrf = await getCsrfHeader();

    let resp;
    if (mode.value === 'all') {
      resp = await axios.get('/api/accounts/export', {
        params: { verify_token: token },
        responseType: 'blob',
        withCredentials: true
      });
    } else if (mode.value === 'selected') {
      if (!selectedGroupIds.value.length) {
        message.warning('请选择至少一个分组');
        return;
      }
      resp = await axios.post(
        '/api/accounts/export-selected',
        { group_ids: selectedGroupIds.value, verify_token: token },
        { responseType: 'blob', withCredentials: true, headers: csrf }
      );
    } else {
      if (!singleGroupId.value) {
        message.warning('请选择分组');
        return;
      }
      // 单个分组导出无需 verify_token
      resp = await axios.get(`/api/groups/${singleGroupId.value}/export`, {
        responseType: 'blob',
        withCredentials: true
      });
    }

    // Blob 也可能是 JSON 错误
    if (resp.data.type?.includes('json')) {
      const text = await resp.data.text();
      try {
        const json = JSON.parse(text);
        message.error(json.error || '导出失败');
      } catch {
        message.error('导出失败');
      }
      return;
    }
    const disposition = resp.headers['content-disposition'] || '';
    const fallback = `export_${Date.now()}.txt`;
    downloadBlob(resp.data, parseFilename(disposition, fallback));
    message.success('已下载');
    emit('update:show', false);
  } catch (e: any) {
    if (e?.response?.data && e.response.data instanceof Blob) {
      try {
        const text = await e.response.data.text();
        const json = JSON.parse(text);
        message.error(json.error || '导出失败');
      } catch {
        message.error('导出失败');
      }
    } else {
      message.error(e?.response?.data?.error || '导出失败');
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="导出账号"
    style="width: 540px;"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-alert type="warning" :show-icon="false" class="mb-3">
      导出文件含明文密码 / Refresh Token / api_key，请妥善保管。
    </n-alert>

    <n-form label-placement="left" label-width="120">
      <n-form-item label="导出范围">
        <n-radio-group v-model:value="mode">
          <n-space vertical>
            <n-radio value="all">全部账号</n-radio>
            <n-radio value="selected">选择多个分组</n-radio>
            <n-radio value="single">单个分组</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item v-if="mode === 'selected'" label="分组">
        <n-select
          v-model:value="selectedGroupIds"
          multiple
          :options="groups.map(g => ({ label: g.name, value: g.id }))"
        />
      </n-form-item>
      <n-form-item v-if="mode === 'single'" label="分组">
        <n-select
          v-model:value="singleGroupId"
          :options="groups.map(g => ({ label: g.name, value: g.id }))"
        />
      </n-form-item>

      <n-form-item v-if="mode !== 'single'" label="登录密码">
        <n-input
          v-model:value="password"
          type="password"
          show-password-on="click"
          placeholder="导出全量/多分组需要密码确认"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="doExport">
          <Icon icon="tabler:download" />
          <span class="ml-1">导出并下载</span>
        </n-button>
      </div>
    </template>
  </n-modal>
</template>
