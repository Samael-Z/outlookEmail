<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { accountsApi } from '@/service/api/accounts';
import { Icon } from '@iconify/vue';

const { t } = useI18n();
const stats = ref({ accounts: 0, groups: 0, tempEmails: 0, internalEml: 0 });
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const [g, a] = await Promise.all([
      accountsApi.listGroups(),
      accountsApi.listAccounts()
    ]);
    stats.value.groups = g.groups?.length || 0;
    stats.value.accounts = a.accounts?.length || 0;
    stats.value.internalEml = (a.accounts || []).filter(x => x.account_type === 'internal_eml').length;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi>
        <n-card hoverable>
          <div class="flex-y-center">
            <Icon icon="tabler:users" class="text-32px text-primary mr-3" />
            <div>
              <div class="text-12px op-60">{{ t('home.totalAccounts') }}</div>
              <div class="text-22px font-bold">{{ stats.accounts }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable>
          <div class="flex-y-center">
            <Icon icon="tabler:folders" class="text-32px text-info mr-3" />
            <div>
              <div class="text-12px op-60">{{ t('home.totalGroups') }}</div>
              <div class="text-22px font-bold">{{ stats.groups }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable>
          <div class="flex-y-center">
            <Icon icon="tabler:mail-fast" class="text-32px text-warning mr-3" />
            <div>
              <div class="text-12px op-60">{{ t('home.totalTempEmails') }}</div>
              <div class="text-22px font-bold">{{ stats.tempEmails }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable>
          <div class="flex-y-center">
            <Icon icon="tabler:building-lighthouse" class="text-32px text-success mr-3" />
            <div>
              <div class="text-12px op-60">{{ t('home.totalInternalEml') }}</div>
              <div class="text-22px font-bold">{{ stats.internalEml }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card class="mt-4" :title="t('app.welcome')">
      <n-alert type="info" :show-icon="false">
        本系统支持 Outlook OAuth、IMAP、临时邮箱、内网 EML 四类邮件读取链路。
        通过左侧导航切换视图：
        <ul class="mt-2 pl-5 list-disc op-80">
          <li><b>邮箱视图</b>：四栏邮件查阅（分组 → 账号 → 邮件列表 → 邮件详情）</li>
          <li><b>账号管理</b>：批量导入、编辑、删除邮箱账号</li>
          <li><b>内网邮箱</b>：@cs2jp.com / @jokerque.com 内网邮件服务器</li>
          <li><b>临时邮箱</b>：GPTMail / DuckMail / Cloudflare Temp Email</li>
        </ul>
      </n-alert>
    </n-card>
  </div>
</template>
