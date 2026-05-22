<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { accountsApi, type Group } from '@/service/api/accounts';

const props = defineProps<{ show: boolean; accountId: number | null }>();
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void;
  (e: 'saved'): void;
}>();

const message = useMessage();
const loading = ref(false);
const saving = ref(false);

const groups = ref<Group[]>([]);
const detail = ref<any>(null);
const aliasesText = ref('');
const savingAliases = ref(false);

const form = ref({
  email: '',
  remark: '',
  status: 'active',
  group_id: null as number | null,
  forward_enabled: false,
  client_id: '',
  refresh_token: '',
  imap_host: '',
  imap_port: 993,
  imap_password: ''
});

watch(
  () => props.show,
  async v => {
    if (v && props.accountId) {
      await loadAll();
    }
  }
);

async function loadAll() {
  if (!props.accountId) return;
  loading.value = true;
  try {
    const [g, a] = await Promise.all([
      accountsApi.listGroups(),
      accountsApi.getAccount(props.accountId)
    ]);
    groups.value = g.groups || [];
    if (a.success && a.account) {
      detail.value = a.account;
      form.value = {
        email: a.account.email || '',
        remark: a.account.remark || '',
        status: a.account.status || 'active',
        group_id: a.account.group_id ?? null,
        forward_enabled: Boolean(a.account.forward_enabled),
        client_id: a.account.client_id || '',
        refresh_token: a.account.refresh_token || '',
        imap_host: a.account.imap_host || '',
        imap_port: Number(a.account.imap_port || 993),
        imap_password: a.account.imap_password || ''
      };
      aliasesText.value = (a.account.aliases || []).join('\n');
    }
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!props.accountId) return;
  saving.value = true;
  try {
    const body: Record<string, any> = {
      email: form.value.email,
      remark: form.value.remark,
      status: form.value.status,
      group_id: form.value.group_id,
      forward_enabled: form.value.forward_enabled,
      account_type: detail.value?.account_type || 'outlook',
      provider: detail.value?.provider || 'outlook'
    };
    if (detail.value?.account_type === 'outlook') {
      body.client_id = form.value.client_id;
      body.refresh_token = form.value.refresh_token;
    } else {
      body.imap_host = form.value.imap_host;
      body.imap_port = form.value.imap_port;
      body.imap_password = form.value.imap_password;
    }
    const r = await accountsApi.updateAccount(props.accountId, body);
    if (r.success) {
      message.success('已保存');
      emit('saved');
      emit('update:show', false);
    } else {
      message.error(r.error || '保存失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '保存失败');
  } finally {
    saving.value = false;
  }
}

async function saveAliases() {
  if (!props.accountId) return;
  savingAliases.value = true;
  try {
    const aliases = aliasesText.value
      .split(/\r?\n/)
      .map(s => s.trim())
      .filter(Boolean);
    const r = await accountsApi.updateAliases(props.accountId, aliases);
    if (r.success) {
      message.success('别名已保存');
      aliasesText.value = (r.aliases || []).join('\n');
    } else {
      message.error(r.errors?.join('；') || r.error || '保存失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '保存失败');
  } finally {
    savingAliases.value = false;
  }
}
</script>

<template>
  <n-drawer
    :show="show"
    :width="640"
    placement="right"
    @update:show="emit('update:show', $event)"
  >
    <n-drawer-content :title="`编辑账号 #${accountId}`" closable>
      <n-spin :show="loading">
        <div v-if="detail">
          <n-card size="small" class="mb-3">
            <n-form label-placement="left" label-width="100" size="small">
              <n-form-item label="账号类型">
                <n-tag size="small" :bordered="false">
                  {{ detail.account_type }} / {{ detail.provider }}
                </n-tag>
              </n-form-item>
              <n-form-item label="邮箱">
                <n-input v-model:value="form.email" />
              </n-form-item>
              <n-form-item label="备注">
                <n-input v-model:value="form.remark" />
              </n-form-item>
              <n-form-item label="状态">
                <n-radio-group v-model:value="form.status">
                  <n-radio value="active">激活</n-radio>
                  <n-radio value="disabled">禁用</n-radio>
                </n-radio-group>
              </n-form-item>
              <n-form-item label="分组">
                <n-select
                  v-model:value="form.group_id"
                  :options="groups.map(g => ({ label: g.name, value: g.id }))"
                />
              </n-form-item>
              <n-form-item label="开启转发">
                <n-switch v-model:value="form.forward_enabled" />
              </n-form-item>
            </n-form>
          </n-card>

          <n-card v-if="detail.account_type === 'outlook'" size="small" class="mb-3" title="OAuth 凭据">
            <n-form label-placement="left" label-width="100" size="small">
              <n-form-item label="Client ID">
                <n-input v-model:value="form.client_id" />
              </n-form-item>
              <n-form-item label="Refresh Token">
                <n-input
                  v-model:value="form.refresh_token"
                  type="password"
                  show-password-on="click"
                />
              </n-form-item>
            </n-form>
          </n-card>

          <n-card
            v-else-if="detail.account_type === 'imap' || detail.account_type === 'internal_eml'"
            size="small"
            class="mb-3"
            :title="detail.account_type === 'internal_eml' ? '内网 EML 凭据' : 'IMAP 凭据'"
          >
            <n-form label-placement="left" label-width="100" size="small">
              <n-form-item :label="detail.account_type === 'internal_eml' ? 'baseURL' : 'IMAP Host'">
                <n-input v-model:value="form.imap_host" />
              </n-form-item>
              <n-form-item v-if="detail.account_type !== 'internal_eml'" label="IMAP Port">
                <n-input-number v-model:value="form.imap_port" :min="1" :max="65535" />
              </n-form-item>
              <n-form-item :label="detail.account_type === 'internal_eml' ? 'API Key' : 'IMAP 密码'">
                <n-input
                  v-model:value="form.imap_password"
                  type="password"
                  show-password-on="click"
                />
              </n-form-item>
            </n-form>
          </n-card>

          <n-card size="small" class="mb-3">
            <template #header>
              别名邮箱
              <n-tag size="tiny" class="ml-2" :bordered="false">
                {{ aliasesText.split(/\r?\n/).filter(Boolean).length }} 个
              </n-tag>
            </template>
            <template #header-extra>
              <n-button size="small" :loading="savingAliases" @click="saveAliases">
                保存别名
              </n-button>
            </template>
            <n-input
              v-model:value="aliasesText"
              type="textarea"
              :rows="5"
              placeholder="每行一个别名邮箱"
            />
          </n-card>

          <div v-if="detail.account_type === 'outlook' && detail.last_refresh_at" class="text-12px op-70">
            <Icon icon="tabler:clock" class="inline-block align-middle" />
            最近刷新: {{ detail.last_refresh_at }} ({{ detail.last_refresh_status }})
          </div>
        </div>
      </n-spin>

      <template #footer>
        <n-space>
          <n-button @click="emit('update:show', false)">关闭</n-button>
          <n-button type="primary" :loading="saving" :disabled="!detail" @click="save">
            保存基础信息
          </n-button>
        </n-space>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>
