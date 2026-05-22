<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { accountsApi, type Group } from '@/service/api/accounts';
import { internalEmlApi, type BulkCreateItem } from '@/service/api/internal-eml';
import OAuthHelperDialog from './OAuthHelperDialog.vue';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void;
  (e: 'imported'): void;
}>();

const message = useMessage();

type AccountKind = 'outlook' | 'imap' | 'internal_eml';

const kind = ref<AccountKind>('outlook');

// outlook
const outlook = ref({
  account_string: '',
  account_format: 'client_id_refresh_token' as 'client_id_refresh_token' | 'refresh_token_client_id'
});

// imap
const imap = ref({
  provider: 'gmail' as 'gmail' | 'qq' | '163' | '126' | 'yahoo' | 'aliyun' | 'custom',
  account_string: '',
  imap_host: '',
  imap_port: 993
});

// internal eml
const internal = ref({
  account_string: ''
});

const groups = ref<Group[]>([]);
const groupId = ref<number | null>(null);
const remark = ref('');
const submitting = ref(false);
const showOAuth = ref(false);

watch(
  () => props.show,
  async v => {
    if (v) {
      await loadGroups();
    } else {
      outlook.value = { account_string: '', account_format: 'client_id_refresh_token' };
      imap.value = { provider: 'gmail', account_string: '', imap_host: '', imap_port: 993 };
      internal.value = { account_string: '' };
      remark.value = '';
    }
  }
);

async function loadGroups() {
  const r = await accountsApi.listGroups();
  groups.value = (r.groups || []).filter(g => g.name !== '临时邮箱');
  if (!groupId.value && groups.value.length) {
    groupId.value = groups.value[0].id;
  }
}

const placeholder = computed(() => {
  if (kind.value === 'outlook') {
    return outlook.value.account_format === 'client_id_refresh_token'
      ? 'email----password----client_id----refresh_token'
      : 'email----password----refresh_token----client_id';
  }
  if (kind.value === 'imap') {
    if (imap.value.provider === 'custom') {
      return 'email----imap_password\nemail----imap_password----imap.example.com----993';
    }
    return 'email----imap_password';
  }
  return 'xxx@jokerque.com\nxxx@cs2jp.com----api_key';
});

function onOAuthGotToken(payload: { client_id: string; refresh_token: string }) {
  // 把 client_id / refresh_token 追加为模板
  const tpl =
    outlook.value.account_format === 'client_id_refresh_token'
      ? `<email>----<password>----${payload.client_id}----${payload.refresh_token}`
      : `<email>----<password>----${payload.refresh_token}----${payload.client_id}`;
  outlook.value.account_string = outlook.value.account_string
    ? outlook.value.account_string + '\n' + tpl
    : tpl;
  message.info('已粘贴到导入框，请填写邮箱和密码');
}

async function submit() {
  submitting.value = true;
  try {
    if (kind.value === 'internal_eml') {
      const items: BulkCreateItem[] = internal.value.account_string
        .split(/\r?\n/)
        .map(l => l.trim())
        .filter(Boolean)
        .map(line => {
          const [email, api_key, base_url] = line.split('----').map(s => s.trim());
          return { email, api_key: api_key || undefined, base_url: base_url || undefined };
        })
        .filter(x => x.email && x.email.includes('@'));
      if (!items.length) {
        message.warning('请至少输入一行有效邮箱');
        return;
      }
      const r = await internalEmlApi.bulkCreate(items, groupId.value ?? undefined, remark.value);
      message.success(`创建 ${r.created_count} 个，跳过 ${r.skipped_count} 个`);
      if (r.skipped_count > 0) {
        message.info(
          '跳过: ' + r.skipped.map(s => `${s.email}: ${s.reason}`).join(' | '),
          { duration: 8000 }
        );
      }
      emit('imported');
      if (r.created_count > 0) emit('update:show', false);
      return;
    }

    // outlook 或 imap：复用 /api/accounts
    const account_string =
      kind.value === 'outlook' ? outlook.value.account_string : imap.value.account_string;
    if (!account_string.trim()) {
      message.warning('请输入账号信息');
      return;
    }
    const body: Parameters<typeof accountsApi.bulkImport>[0] = {
      account_string,
      provider: kind.value === 'outlook' ? 'outlook' : imap.value.provider,
      group_id: groupId.value ?? undefined,
      remark: remark.value || undefined,
      account_format: kind.value === 'outlook' ? outlook.value.account_format : undefined,
      imap_host: kind.value === 'imap' ? imap.value.imap_host || undefined : undefined,
      imap_port: kind.value === 'imap' ? imap.value.imap_port : undefined
    };
    const r = await accountsApi.bulkImport(body);
    if (r.success) {
      message.success(r.message || `已添加 ${r.added_count || 0} 个`);
      emit('imported');
      emit('update:show', false);
    } else {
      message.error(r.error || '导入失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '导入失败');
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="添加邮箱账号"
    style="width: 640px;"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-tabs v-model:value="kind" type="line" animated>
      <n-tab-pane name="outlook" tab="Outlook OAuth">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="格式">
            <n-radio-group v-model:value="outlook.account_format">
              <n-radio value="client_id_refresh_token">
                email----password----<b>client_id----refresh_token</b>
              </n-radio>
              <n-radio value="refresh_token_client_id">
                email----password----<b>refresh_token----client_id</b>
              </n-radio>
            </n-radio-group>
          </n-form-item>
          <n-form-item label="账号列表">
            <n-input
              v-model:value="outlook.account_string"
              type="textarea"
              :rows="6"
              :placeholder="placeholder"
            />
          </n-form-item>
          <n-form-item :show-label="false">
            <n-button @click="showOAuth = true">
              <Icon icon="tabler:key" />
              <span class="ml-1">没有 Refresh Token？打开 OAuth 助手</span>
            </n-button>
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="imap" tab="IMAP">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="服务商">
            <n-select
              v-model:value="imap.provider"
              :options="[
                { label: 'Gmail', value: 'gmail' },
                { label: 'QQ 邮箱', value: 'qq' },
                { label: '163 邮箱', value: '163' },
                { label: '126 邮箱', value: '126' },
                { label: 'Yahoo', value: 'yahoo' },
                { label: '阿里邮箱', value: 'aliyun' },
                { label: '自定义 IMAP', value: 'custom' }
              ]"
            />
          </n-form-item>
          <n-form-item v-if="imap.provider === 'custom'" label="默认 IMAP Host">
            <n-input v-model:value="imap.imap_host" placeholder="imap.example.com（每行格式 4 段时可覆盖）" />
          </n-form-item>
          <n-form-item v-if="imap.provider === 'custom'" label="默认 IMAP Port">
            <n-input-number v-model:value="imap.imap_port" :min="1" :max="65535" />
          </n-form-item>
          <n-form-item label="账号列表">
            <n-input
              v-model:value="imap.account_string"
              type="textarea"
              :rows="6"
              :placeholder="placeholder"
            />
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="internal_eml" tab="内网 EML">
        <n-alert type="info" :show-icon="false" class="mb-3">
          内置支持 <code>@cs2jp.com</code> / <code>@jokerque.com</code>，
          会按域名自动解析 baseURL。可选追加 <code>----api_key</code> 覆盖默认密钥，或再追加 <code>----base_url</code>。
        </n-alert>
        <n-form label-placement="left" label-width="100">
          <n-form-item label="账号列表">
            <n-input
              v-model:value="internal.account_string"
              type="textarea"
              :rows="6"
              :placeholder="placeholder"
            />
          </n-form-item>
        </n-form>
      </n-tab-pane>
    </n-tabs>

    <n-divider />
    <n-form label-placement="left" label-width="100">
      <n-form-item label="分组">
        <n-select
          v-model:value="groupId"
          :options="groups.map(g => ({ label: g.name, value: g.id }))"
        />
      </n-form-item>
      <n-form-item label="备注">
        <n-input v-model:value="remark" placeholder="可选，统一应用到所有新增账号" />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="submit">
          导入
        </n-button>
      </div>
    </template>

    <OAuthHelperDialog v-model:show="showOAuth" @got-token="onOAuthGotToken" />
  </n-modal>
</template>
