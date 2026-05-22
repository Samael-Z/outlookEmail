<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMessage, useDialog } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { settingsApi, type AppSettings } from '@/service/api/settings';
import { webdavApi } from '@/service/api/forwarding';

const message = useMessage();
const dialog = useDialog();

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const uploading = ref(false);

const settings = ref<AppSettings>({});

const form = ref({
  webdav_backup_enabled: 'false',
  webdav_backup_url: '',
  webdav_backup_username: '',
  webdav_backup_password: '',
  webdav_backup_cron: '0 3 * * *'
});
const verifyPassword = ref('');
const nextRun = ref('');
const lastRun = ref({ at: '', status: '', message: '', filename: '' });

async function load() {
  loading.value = true;
  try {
    const r = await settingsApi.get();
    settings.value = r.settings || {};
    form.value.webdav_backup_enabled = String(settings.value.webdav_backup_enabled || 'false');
    form.value.webdav_backup_url = String(settings.value.webdav_backup_url || '');
    form.value.webdav_backup_username = String(settings.value.webdav_backup_username || '');
    form.value.webdav_backup_password = String(settings.value.webdav_backup_password || '');
    form.value.webdav_backup_cron = String(settings.value.webdav_backup_cron || '0 3 * * *');
    nextRun.value = String(settings.value.webdav_backup_next_run || '');
    lastRun.value = {
      at: String(settings.value.webdav_backup_last_run_at || ''),
      status: String(settings.value.webdav_backup_last_status || ''),
      message: String(settings.value.webdav_backup_last_message || ''),
      filename: String(settings.value.webdav_backup_last_filename || '')
    };
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!verifyPassword.value) {
    message.warning('修改 WebDAV 备份设置需要输入登录密码确认');
    return;
  }
  saving.value = true;
  try {
    const r = await settingsApi.update({
      ...form.value,
      webdav_backup_verify_password: verifyPassword.value
    });
    if (r.success) {
      message.success('已保存');
      verifyPassword.value = '';
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

async function testConnection() {
  testing.value = true;
  try {
    const r = await webdavApi.testBackup({
      url: form.value.webdav_backup_url,
      username: form.value.webdav_backup_username,
      password: form.value.webdav_backup_password
    });
    if (r.success) message.success(r.message || '测试成功');
    else message.error(r.error || '测试失败');
  } catch (e: any) {
    message.error(e?.response?.data?.error || '测试失败');
  } finally {
    testing.value = false;
  }
}

async function previewCron() {
  try {
    const r = await webdavApi.validateCron(form.value.webdav_backup_cron);
    if (r.success && r.preview?.next_run) {
      nextRun.value = r.preview.next_run;
      message.success(`下次执行: ${nextRun.value}`);
    } else {
      message.error(r.error || 'Cron 无效');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || 'Cron 校验失败');
  }
}

function manualUpload() {
  dialog.warning({
    title: '手动上传真实备份',
    content: '将立即生成"全部分组"备份文件并上传到 WebDAV。请输入登录密码确认。',
    positiveText: '上传',
    negativeText: '取消',
    onPositiveClick: () => {
      return new Promise<void>(resolve => {
        const pwd = prompt('请输入登录密码确认');
        if (!pwd) {
          resolve();
          return;
        }
        uploading.value = true;
        webdavApi
          .uploadBackup(pwd)
          .then(r => {
            if (r.success) message.success(r.message || '上传成功');
            else message.error(r.error || '上传失败');
            return load();
          })
          .catch(e => message.error(e?.response?.data?.error || '上传失败'))
          .finally(() => {
            uploading.value = false;
            resolve();
          });
      });
    }
  });
}

onMounted(load);
</script>

<template>
  <n-spin :show="loading">
    <n-card title="WebDAV 备份">
      <n-alert type="info" :show-icon="false" class="mb-4">
        定时把全部分组（含临时邮箱、内网邮箱凭据）以 <code>all_groups_backup_YYYYMMDD_HHMMSS.txt</code>
        格式上传到 WebDAV 目录。涉及敏感数据，建议使用专用目录并加访问控制。
      </n-alert>

      <n-form label-placement="left" label-width="180" class="max-w-800px">
        <n-form-item label="启用定时备份">
          <n-switch
            :value="form.webdav_backup_enabled === 'true'"
            @update:value="(v: boolean) => (form.webdav_backup_enabled = String(v))"
          />
        </n-form-item>
        <n-form-item label="WebDAV 目录 URL">
          <n-input
            v-model:value="form.webdav_backup_url"
            placeholder="https://dav.jianguoyun.com/dav/mailBackup"
          />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="form.webdav_backup_username" />
        </n-form-item>
        <n-form-item label="密码 / App Password">
          <n-input
            v-model:value="form.webdav_backup_password"
            type="password"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="Cron 表达式 (5 段)">
          <n-input-group>
            <n-input v-model:value="form.webdav_backup_cron" placeholder="0 3 * * *" />
            <n-button @click="previewCron">预览下次执行</n-button>
          </n-input-group>
          <template #feedback>
            <span v-if="nextRun" class="text-12px op-70">下次执行: {{ nextRun }}</span>
          </template>
        </n-form-item>
        <n-divider />
        <n-form-item label="登录密码（确认修改）">
          <n-input
            v-model:value="verifyPassword"
            type="password"
            show-password-on="click"
            placeholder="修改备份设置需要输入登录密码"
          />
        </n-form-item>
        <n-form-item :show-label="false">
          <n-space>
            <n-button type="primary" :loading="saving" @click="save">保存设置</n-button>
            <n-button :loading="testing" @click="testConnection">
              <Icon icon="tabler:network" /> <span class="ml-1">测试 WebDAV</span>
            </n-button>
            <n-button :loading="uploading" type="warning" @click="manualUpload">
              <Icon icon="tabler:upload" /> <span class="ml-1">手动上传备份</span>
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <n-card v-if="lastRun.at" class="mt-4" title="最近一次执行">
      <n-descriptions :column="1" bordered label-placement="left">
        <n-descriptions-item label="时间">{{ lastRun.at }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag
            :type="lastRun.status === 'success' ? 'success' : 'error'"
            size="small"
            bordered
          >
            {{ lastRun.status }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="文件名">{{ lastRun.filename || '—' }}</n-descriptions-item>
        <n-descriptions-item label="消息">{{ lastRun.message || '—' }}</n-descriptions-item>
      </n-descriptions>
    </n-card>
  </n-spin>
</template>
