<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { oauthApi } from '@/service/api/oauth';
import { copyText } from '@/utils/clipboard';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void;
  (e: 'got-token', payload: { email?: string; client_id: string; refresh_token: string }): void;
}>();

const message = useMessage();

const authInfo = ref<{ auth_url: string; client_id: string; redirect_uri: string } | null>(null);
const redirectedUrl = ref('');
const tokenResult = ref<{ client_id: string; refresh_token: string } | null>(null);
const loadingAuth = ref(false);
const exchanging = ref(false);

watch(
  () => props.show,
  async v => {
    if (v) {
      authInfo.value = null;
      redirectedUrl.value = '';
      tokenResult.value = null;
      await generateAuthUrl();
    }
  }
);

async function generateAuthUrl() {
  loadingAuth.value = true;
  try {
    const r = await oauthApi.getAuthUrl();
    if (r.success) {
      authInfo.value = {
        auth_url: r.auth_url,
        client_id: r.client_id,
        redirect_uri: r.redirect_uri
      };
    }
  } finally {
    loadingAuth.value = false;
  }
}

async function copyAuthUrl() {
  if (!authInfo.value) return;
  const ok = await copyText(authInfo.value.auth_url);
  if (ok) message.success('已复制授权链接');
  else message.error('复制失败，请手动选择');
}

async function exchange() {
  if (!redirectedUrl.value.trim()) {
    message.warning('请粘贴授权后的完整 URL');
    return;
  }
  exchanging.value = true;
  try {
    const r = await oauthApi.exchangeToken(redirectedUrl.value.trim());
    if (r.success && r.refresh_token && r.client_id) {
      tokenResult.value = { client_id: r.client_id, refresh_token: r.refresh_token };
      message.success('换取成功');
    } else {
      message.error(r.error || '换取失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '换取失败');
  } finally {
    exchanging.value = false;
  }
}

async function copyToken(value: string) {
  const ok = await copyText(value);
  if (ok) message.success('已复制');
  else message.error('复制失败，请手动选择');
}

function applyToImport() {
  if (!tokenResult.value) return;
  emit('got-token', tokenResult.value);
  emit('update:show', false);
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="OAuth 助手：获取 Refresh Token"
    style="width: 640px;"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-alert type="info" :show-icon="false" class="mb-3">
      使用项目内置（或环境变量配置的）Client ID 生成授权链接 → 浏览器登录授权 →
      把浏览器跳转到的 <code>localhost:8080</code> 完整 URL 粘贴回来 → 换取 Refresh Token。
    </n-alert>

    <n-spin :show="loadingAuth">
      <div v-if="authInfo">
        <div class="mb-2 text-12px op-70">
          Client ID: <code>{{ authInfo.client_id }}</code><br />
          Redirect URI: <code>{{ authInfo.redirect_uri }}</code>
        </div>
        <n-form-item label="1. 授权链接" label-placement="top">
          <n-input-group>
            <n-input :value="authInfo.auth_url" readonly type="text" />
            <n-button @click="copyAuthUrl">
              <Icon icon="tabler:copy" />
            </n-button>
            <n-button tag="a" :href="authInfo.auth_url" target="_blank" type="primary">
              <Icon icon="tabler:external-link" />
              <span class="ml-1">打开</span>
            </n-button>
          </n-input-group>
        </n-form-item>

        <n-form-item label="2. 粘贴授权后的完整 URL" label-placement="top">
          <n-input
            v-model:value="redirectedUrl"
            type="textarea"
            :rows="3"
            placeholder="http://localhost:8080/?code=xxx&state=12345"
          />
        </n-form-item>
        <n-button
          type="primary"
          block
          :loading="exchanging"
          @click="exchange"
        >
          <Icon icon="tabler:key" />
          <span class="ml-1">换取 Refresh Token</span>
        </n-button>

        <n-divider v-if="tokenResult" />
        <div v-if="tokenResult">
          <n-form-item label="Client ID" label-placement="top">
            <n-input-group>
              <n-input :value="tokenResult.client_id" readonly />
              <n-button @click="copyToken(tokenResult.client_id)">
                <Icon icon="tabler:copy" />
              </n-button>
            </n-input-group>
          </n-form-item>
          <n-form-item label="Refresh Token" label-placement="top">
            <n-input-group>
              <n-input :value="tokenResult.refresh_token" readonly type="password" show-password-on="click" />
              <n-button @click="copyToken(tokenResult.refresh_token)">
                <Icon icon="tabler:copy" />
              </n-button>
            </n-input-group>
          </n-form-item>
          <n-button type="primary" block @click="applyToImport">
            <Icon icon="tabler:check" />
            <span class="ml-1">应用到导入对话框</span>
          </n-button>
        </div>
      </div>
    </n-spin>

    <template #footer>
      <div class="flex justify-end">
        <n-button @click="emit('update:show', false)">关闭</n-button>
      </div>
    </template>
  </n-modal>
</template>
