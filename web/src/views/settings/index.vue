<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import { useI18n } from 'vue-i18n';
import { settingsApi, type AppSettings } from '@/service/api/settings';
import { useThemeStore } from '@/store/modules/theme';
import { useAppStore } from '@/store/modules/app';
import { setLocale } from '@/locales';
import { Icon } from '@iconify/vue';

const message = useMessage();
const { t } = useI18n();
const themeStore = useThemeStore();
const appStore = useAppStore();

const settings = ref<AppSettings>({});
const loading = ref(false);

// 密码修改
const newPassword = ref('');
const confirmPassword = ref('');
const changingPwd = ref(false);

// 外部 API Key
const apiKey = ref('');
const rotatingKey = ref(false);

// 高级设置
const duckmailForm = ref({ duckmail_base_url: '', duckmail_api_key: '' });
const cloudflareForm = ref({
  cloudflare_worker_domain: '',
  cloudflare_email_domains: '',
  cloudflare_admin_password: ''
});
const advancedForm = ref({ app_timezone: '' });
const savingAdvanced = ref(false);

const tab = ref('general');

const presetColors = [
  '#646cff', // Soybean default
  '#18a058', // Naive green
  '#2080f0', // Naive blue
  '#f0a020', // Warning
  '#d03050', // Error
  '#667eea', // 紫蓝
  '#764ba2', // 紫
  '#10b981'  // 翠绿
];

async function loadSettings() {
  loading.value = true;
  try {
    const res = await settingsApi.get();
    settings.value = res.settings || {};
    apiKey.value = res.settings?.external_api_key || '';
    duckmailForm.value.duckmail_base_url = String(res.settings?.duckmail_base_url || '');
    duckmailForm.value.duckmail_api_key = String(res.settings?.duckmail_api_key || '');
    cloudflareForm.value.cloudflare_worker_domain = String(res.settings?.cloudflare_worker_domain || '');
    cloudflareForm.value.cloudflare_email_domains = String(res.settings?.cloudflare_email_domains || '');
    cloudflareForm.value.cloudflare_admin_password = String(res.settings?.cloudflare_admin_password || '');
    advancedForm.value.app_timezone = String(res.settings?.app_timezone || '');
  } finally {
    loading.value = false;
  }
}

async function saveAdvanced() {
  savingAdvanced.value = true;
  try {
    const patch = {
      ...duckmailForm.value,
      ...cloudflareForm.value,
      ...advancedForm.value
    };
    const r = await settingsApi.update(patch);
    if (r.success) {
      message.success('已保存');
      await loadSettings();
    } else {
      message.error(r.error || '保存失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '保存失败');
  } finally {
    savingAdvanced.value = false;
  }
}

async function changePassword() {
  if (!newPassword.value || newPassword.value.length < 8) {
    message.warning('新密码至少 8 位');
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    message.warning('两次输入的密码不一致');
    return;
  }
  changingPwd.value = true;
  try {
    const res = await settingsApi.changePassword(newPassword.value);
    if (res.success) {
      message.success('密码已修改');
      newPassword.value = '';
      confirmPassword.value = '';
      await loadSettings();
    } else {
      message.error(res.error || '修改失败');
    }
  } finally {
    changingPwd.value = false;
  }
}

function generateRandomKey() {
  const arr = new Uint8Array(24);
  crypto.getRandomValues(arr);
  apiKey.value = Array.from(arr)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

async function saveApiKey() {
  rotatingKey.value = true;
  try {
    const res = await settingsApi.rotateExternalApiKey(apiKey.value);
    if (res.success) {
      message.success('API Key 已保存');
      await loadSettings();
    } else {
      message.error(res.error || '保存失败');
    }
  } finally {
    rotatingKey.value = false;
  }
}

async function copyApiKey() {
  await navigator.clipboard.writeText(apiKey.value);
  message.success('已复制');
}

function applyLocale(v: 'zh-CN' | 'en-US') {
  appStore.setLocale(v);
  setLocale(v);
  message.success(t('common.success'));
}

function applyPrimaryColor(color: string) {
  themeStore.primaryColor = color;
  message.success(t('common.success'));
}

onMounted(loadSettings);
</script>

<template>
  <n-card>
    <template #header>{{ t('menu.settings') }}</template>
    <n-tabs v-model:value="tab" type="line" animated>
      <n-tab-pane name="general" tab="常规">
        <n-form label-placement="left" label-width="120" class="max-w-600px">
          <n-form-item :label="t('common.language')">
            <n-radio-group :value="appStore.locale" @update:value="applyLocale">
              <n-radio value="zh-CN">中文</n-radio>
              <n-radio value="en-US">English</n-radio>
            </n-radio-group>
          </n-form-item>

          <n-form-item label="主题模式">
            <n-radio-group
              :value="themeStore.darkMode ? 'dark' : 'light'"
              @update:value="(v: string) => { themeStore.darkMode = v === 'dark'; }"
            >
              <n-radio value="light">{{ t('common.lightMode') }}</n-radio>
              <n-radio value="dark">{{ t('common.darkMode') }}</n-radio>
            </n-radio-group>
          </n-form-item>

          <n-form-item label="主题色">
            <n-space>
              <div
                v-for="c in presetColors"
                :key="c"
                @click="applyPrimaryColor(c)"
                :style="{
                  background: c,
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  border: themeStore.primaryColor === c ? '3px solid #fff' : '1px solid #ddd',
                  boxShadow: themeStore.primaryColor === c ? `0 0 0 2px ${c}` : 'none'
                }"
              />
              <n-color-picker
                :value="themeStore.primaryColor"
                :show-alpha="false"
                size="small"
                @update:value="applyPrimaryColor"
              />
            </n-space>
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="security" tab="安全">
        <n-form label-placement="left" label-width="120" class="max-w-600px">
          <n-form-item label="当前密码">
            <n-input
              :value="settings.login_password_masked || '****'"
              readonly
              disabled
            />
          </n-form-item>
          <n-form-item label="新密码">
            <n-input
              v-model:value="newPassword"
              type="password"
              show-password-on="click"
              placeholder="至少 8 位"
            />
          </n-form-item>
          <n-form-item label="确认新密码">
            <n-input
              v-model:value="confirmPassword"
              type="password"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item :show-label="false">
            <n-button type="primary" :loading="changingPwd" @click="changePassword">
              修改密码
            </n-button>
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="api" tab="对外 API">
        <n-form label-placement="left" label-width="120" class="max-w-700px">
          <n-form-item label="API Key">
            <n-input-group>
              <n-input
                v-model:value="apiKey"
                type="password"
                show-password-on="click"
                placeholder="未配置"
              />
              <n-button @click="generateRandomKey">
                <Icon icon="tabler:dice" /> <span class="ml-1">随机生成</span>
              </n-button>
              <n-button @click="copyApiKey" :disabled="!apiKey">
                <Icon icon="tabler:copy" />
              </n-button>
            </n-input-group>
          </n-form-item>
          <n-form-item :show-label="false">
            <n-button type="primary" :loading="rotatingKey" @click="saveApiKey">
              保存
            </n-button>
          </n-form-item>
          <n-alert type="info" :show-icon="false" class="mt-2">
            通过 Header <code>X-API-Key</code> 或查询参数 <code>?api_key=</code>
            调用 <code>/api/external/*</code> 获取邮件，无需登录。
          </n-alert>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="advanced" tab="高级">
        <n-alert type="info" :show-icon="false" class="mb-3">
          这些高级设置主要服务于临时邮箱功能：DuckMail 私有域名 API、Cloudflare Temp Email Worker。
          其他设置（转发、WebDAV）已经迁移到独立的菜单页。
        </n-alert>

        <n-divider title-placement="left">DuckMail</n-divider>
        <n-form label-placement="left" label-width="180" class="max-w-800px">
          <n-form-item label="Base URL">
            <n-input
              v-model:value="duckmailForm.duckmail_base_url"
              placeholder="https://api.duckmail.sbs"
            />
          </n-form-item>
          <n-form-item label="API Key">
            <n-input
              v-model:value="duckmailForm.duckmail_api_key"
              type="password"
              show-password-on="click"
              placeholder="可选，访问私有域名需要"
            />
          </n-form-item>
        </n-form>

        <n-divider title-placement="left">Cloudflare Temp Email</n-divider>
        <n-form label-placement="left" label-width="180" class="max-w-800px">
          <n-form-item label="Worker 域名">
            <n-input
              v-model:value="cloudflareForm.cloudflare_worker_domain"
              placeholder="如 mail.example.com（不带 https://）"
            />
          </n-form-item>
          <n-form-item label="可用邮箱域名">
            <n-input
              v-model:value="cloudflareForm.cloudflare_email_domains"
              placeholder="多个用英文逗号分隔，如 a.com, b.com"
            />
          </n-form-item>
          <n-form-item label="Admin 密码">
            <n-input
              v-model:value="cloudflareForm.cloudflare_admin_password"
              type="password"
              show-password-on="click"
              placeholder="用于全部邮件视图等管理端能力"
            />
          </n-form-item>
        </n-form>

        <n-divider title-placement="left">时区</n-divider>
        <n-form label-placement="left" label-width="180" class="max-w-800px">
          <n-form-item label="应用时区">
            <n-input
              v-model:value="advancedForm.app_timezone"
              placeholder="如 Asia/Shanghai（影响 Cron 计算与日期显示）"
            />
          </n-form-item>
        </n-form>

        <div class="mt-4">
          <n-button type="primary" :loading="savingAdvanced" @click="saveAdvanced">
            保存高级设置
          </n-button>
        </div>
      </n-tab-pane>
    </n-tabs>
  </n-card>
</template>
