<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { settingsApi, type AppSettings } from '@/service/api/settings';
import { forwardingApi } from '@/service/api/forwarding';

const message = useMessage();
const loading = ref(false);
const saving = ref(false);
const testing = ref('');

const settings = ref<AppSettings>({});

const form = ref({
  forward_check_interval_minutes: '5',
  forward_account_delay_seconds: '0',
  forward_email_window_minutes: '0',
  forward_include_junkemail: 'false',
  forward_channels: 'auto',
  // smtp
  smtp_host: '',
  smtp_port: '465',
  smtp_username: '',
  smtp_password: '',
  smtp_from_email: '',
  smtp_use_ssl: 'true',
  smtp_use_tls: 'false',
  email_forward_recipient: '',
  // telegram
  telegram_bot_token: '',
  telegram_chat_id: '',
  telegram_proxy_url: '',
  // wecom
  wecom_webhook_url: ''
});

const channels = computed(() => {
  const raw = String(form.value.forward_channels || 'auto').toLowerCase();
  if (raw === 'auto') return ['smtp', 'telegram', 'wecom'];
  return raw.split(/[,\s]+/).filter(Boolean);
});

function toggleChannel(name: 'smtp' | 'telegram' | 'wecom', enabled: boolean) {
  const current = new Set(channels.value);
  if (enabled) current.add(name);
  else current.delete(name);
  form.value.forward_channels = Array.from(current).join(',') || 'auto';
}

async function load() {
  loading.value = true;
  try {
    const r = await settingsApi.get();
    settings.value = r.settings || {};
    Object.keys(form.value).forEach(k => {
      if (settings.value[k] !== undefined && settings.value[k] !== null) {
        (form.value as any)[k] = String(settings.value[k]);
      }
    });
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    const r = await settingsApi.update(form.value);
    if (r.success) {
      message.success('已保存');
      await load();
    } else {
      message.error(r.error || '保存失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '保存失败');
  } finally {
    saving.value = false;
  }
}

async function test(channel: 'smtp' | 'telegram' | 'wecom') {
  testing.value = channel;
  try {
    const config: any = {};
    if (channel === 'smtp') {
      config.smtp = {
        smtp_host: form.value.smtp_host,
        smtp_port: form.value.smtp_port,
        smtp_username: form.value.smtp_username,
        smtp_password: form.value.smtp_password,
        smtp_from_email: form.value.smtp_from_email,
        email_forward_recipient: form.value.email_forward_recipient,
        smtp_use_ssl: form.value.smtp_use_ssl,
        smtp_use_tls: form.value.smtp_use_tls
      };
    } else if (channel === 'telegram') {
      config.telegram = {
        telegram_bot_token: form.value.telegram_bot_token,
        telegram_chat_id: form.value.telegram_chat_id,
        telegram_proxy_url: form.value.telegram_proxy_url
      };
    } else {
      config.wecom = { wecom_webhook_url: form.value.wecom_webhook_url };
    }
    const r = await forwardingApi.testChannel(channel, config);
    if (r.success) message.success(r.message || '测试成功');
    else message.error(r.error || '测试失败');
  } catch (e: any) {
    message.error(e?.response?.data?.error || '测试失败');
  } finally {
    testing.value = '';
  }
}

async function triggerCheck() {
  try {
    const r = await forwardingApi.triggerCheck();
    if (r.success) message.success(r.message || '已触发');
    else message.error(r.error || '触发失败');
  } catch (e: any) {
    message.error(e?.response?.data?.error || '触发失败');
  }
}

onMounted(load);
</script>

<template>
  <n-spin :show="loading">
    <n-card title="邮件转发设置">
      <template #header-extra>
        <n-space>
          <n-button @click="triggerCheck">
            <Icon icon="tabler:player-play" /> <span class="ml-1">立即触发检查</span>
          </n-button>
          <n-button type="primary" :loading="saving" @click="save">
            保存全部
          </n-button>
        </n-space>
      </template>

      <n-form label-placement="left" label-width="180" class="max-w-800px">
        <n-form-item label="轮询间隔（分钟）">
          <n-input-number
            :value="Number(form.forward_check_interval_minutes)"
            :min="1"
            :max="60"
            @update:value="(v: number | null) => (form.forward_check_interval_minutes = String(v ?? 5))"
          />
        </n-form-item>
        <n-form-item label="账号间延迟（秒）">
          <n-input-number
            :value="Number(form.forward_account_delay_seconds)"
            :min="0"
            :max="60"
            @update:value="(v: number | null) => (form.forward_account_delay_seconds = String(v ?? 0))"
          />
        </n-form-item>
        <n-form-item label="转发邮件时间窗（分钟）">
          <n-input-number
            :value="Number(form.forward_email_window_minutes)"
            :min="0"
            :max="1440"
            @update:value="(v: number | null) => (form.forward_email_window_minutes = String(v ?? 0))"
          />
          <template #feedback>
            <span class="text-12px op-60">0 表示不限制，仅转发自上次游标之后的新邮件</span>
          </template>
        </n-form-item>
        <n-form-item label="转发垃圾邮件">
          <n-switch
            :value="form.forward_include_junkemail === 'true'"
            @update:value="(v: boolean) => (form.forward_include_junkemail = String(v))"
          />
        </n-form-item>
        <n-form-item label="启用渠道">
          <n-space>
            <n-checkbox
              :checked="channels.includes('smtp')"
              @update:checked="(v: boolean) => toggleChannel('smtp', v)"
            >
              SMTP
            </n-checkbox>
            <n-checkbox
              :checked="channels.includes('telegram')"
              @update:checked="(v: boolean) => toggleChannel('telegram', v)"
            >
              Telegram
            </n-checkbox>
            <n-checkbox
              :checked="channels.includes('wecom')"
              @update:checked="(v: boolean) => toggleChannel('wecom', v)"
            >
              企业微信
            </n-checkbox>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- SMTP -->
    <n-card class="mt-4">
      <template #header>
        <Icon icon="tabler:mail" class="inline-block align-middle mr-2" />
        SMTP 配置
      </template>
      <template #header-extra>
        <n-button
          size="small"
          :loading="testing === 'smtp'"
          @click="test('smtp')"
        >
          <Icon icon="tabler:send" /> <span class="ml-1">发送测试邮件</span>
        </n-button>
      </template>
      <n-form label-placement="left" label-width="160" class="max-w-800px">
        <n-form-item label="SMTP 服务器">
          <n-input v-model:value="form.smtp_host" placeholder="smtp.example.com" />
        </n-form-item>
        <n-form-item label="端口">
          <n-input v-model:value="form.smtp_port" placeholder="465" />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="form.smtp_username" />
        </n-form-item>
        <n-form-item label="密码 / App Password">
          <n-input v-model:value="form.smtp_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="发件人">
          <n-input v-model:value="form.smtp_from_email" placeholder="alerts@example.com" />
        </n-form-item>
        <n-form-item label="收件人">
          <n-input v-model:value="form.email_forward_recipient" placeholder="me@example.com" />
        </n-form-item>
        <n-form-item label="加密">
          <n-space>
            <n-checkbox
              :checked="form.smtp_use_ssl === 'true'"
              @update:checked="(v: boolean) => (form.smtp_use_ssl = String(v))"
            >
              SSL
            </n-checkbox>
            <n-checkbox
              :checked="form.smtp_use_tls === 'true'"
              @update:checked="(v: boolean) => (form.smtp_use_tls = String(v))"
            >
              TLS（STARTTLS）
            </n-checkbox>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- Telegram -->
    <n-card class="mt-4">
      <template #header>
        <Icon icon="tabler:brand-telegram" class="inline-block align-middle mr-2" />
        Telegram 配置
      </template>
      <template #header-extra>
        <n-button
          size="small"
          :loading="testing === 'telegram'"
          @click="test('telegram')"
        >
          <Icon icon="tabler:send" /> <span class="ml-1">发送测试消息</span>
        </n-button>
      </template>
      <n-form label-placement="left" label-width="160" class="max-w-800px">
        <n-form-item label="Bot Token">
          <n-input
            v-model:value="form.telegram_bot_token"
            type="password"
            show-password-on="click"
            placeholder="从 @BotFather 获取"
          />
        </n-form-item>
        <n-form-item label="Chat ID">
          <n-input v-model:value="form.telegram_chat_id" placeholder="个人 ID 或群组 -100xxxx" />
        </n-form-item>
        <n-form-item label="代理 URL">
          <n-input v-model:value="form.telegram_proxy_url" placeholder="可选，http:// 或 socks5://" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- WeCom -->
    <n-card class="mt-4">
      <template #header>
        <Icon icon="tabler:building" class="inline-block align-middle mr-2" />
        企业微信群机器人
      </template>
      <template #header-extra>
        <n-button
          size="small"
          :loading="testing === 'wecom'"
          @click="test('wecom')"
        >
          <Icon icon="tabler:send" /> <span class="ml-1">发送测试消息</span>
        </n-button>
      </template>
      <n-form label-placement="left" label-width="160" class="max-w-800px">
        <n-form-item label="Webhook URL">
          <n-input
            v-model:value="form.wecom_webhook_url"
            type="password"
            show-password-on="click"
            placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
          />
        </n-form-item>
      </n-form>
    </n-card>
  </n-spin>
</template>
