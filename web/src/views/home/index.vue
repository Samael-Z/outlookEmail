<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Icon } from '@iconify/vue';
import * as echarts from 'echarts/core';
import { PieChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { accountsApi, type Account } from '@/service/api/accounts';
import { tempEmailsApi } from '@/service/api/temp-emails';
import { useThemeStore } from '@/store/modules/theme';

echarts.use([PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer]);

const { t } = useI18n();
const themeStore = useThemeStore();

const stats = ref({
  accounts: 0,
  groups: 0,
  tempEmails: 0,
  internalEml: 0,
  outlook: 0,
  imap: 0
});
const loading = ref(false);
const accountsRaw = ref<Account[]>([]);

const typePieRef = ref<HTMLElement | null>(null);
const groupBarRef = ref<HTMLElement | null>(null);
let typePieChart: echarts.ECharts | null = null;
let groupBarChart: echarts.ECharts | null = null;

async function load() {
  loading.value = true;
  try {
    const [g, a, t] = await Promise.all([
      accountsApi.listGroups(),
      accountsApi.listAccounts({ limit: 1000 }),
      tempEmailsApi.list().catch(() => ({ emails: [] as any[] }))
    ]);
    accountsRaw.value = a.accounts || [];
    stats.value.groups = g.groups?.length || 0;
    stats.value.accounts = accountsRaw.value.length;
    stats.value.tempEmails = (t as any).emails?.length || 0;
    stats.value.internalEml = accountsRaw.value.filter(x => x.account_type === 'internal_eml').length;
    stats.value.outlook = accountsRaw.value.filter(x => x.account_type === 'outlook').length;
    stats.value.imap = accountsRaw.value.filter(x => x.account_type === 'imap').length;

    renderTypePie();
    renderGroupBar(g.groups || []);
  } finally {
    loading.value = false;
  }
}

function renderTypePie() {
  if (!typePieRef.value) return;
  if (!typePieChart) {
    typePieChart = echarts.init(typePieRef.value, themeStore.darkMode ? 'dark' : undefined);
  }
  typePieChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center', textStyle: { color: themeStore.darkMode ? '#ddd' : '#333' } },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 6, borderColor: themeStore.darkMode ? '#18181c' : '#fff', borderWidth: 2 },
        label: { show: false },
        labelLine: { show: false },
        data: [
          { value: stats.value.outlook, name: 'Outlook OAuth', itemStyle: { color: '#2080f0' } },
          { value: stats.value.imap, name: 'IMAP', itemStyle: { color: '#18a058' } },
          { value: stats.value.internalEml, name: '内网 EML', itemStyle: { color: '#f0a020' } }
        ].filter(x => x.value > 0)
      }
    ]
  });
}

function renderGroupBar(groups: { id: number; name: string }[]) {
  if (!groupBarRef.value) return;
  if (!groupBarChart) {
    groupBarChart = echarts.init(groupBarRef.value, themeStore.darkMode ? 'dark' : undefined);
  }
  const counts = groups.map(g => ({
    name: g.name,
    count: accountsRaw.value.filter(a => a.group_id === g.id).length
  }));
  groupBarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 16, right: 16, bottom: 32, left: 40 },
    xAxis: {
      type: 'category',
      data: counts.map(c => c.name),
      axisLabel: { color: themeStore.darkMode ? '#aaa' : '#666', rotate: 30, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: themeStore.darkMode ? '#aaa' : '#666' },
      splitLine: { lineStyle: { color: themeStore.darkMode ? '#2c2c32' : '#eee' } }
    },
    series: [
      {
        type: 'bar',
        data: counts.map(c => c.count),
        itemStyle: { color: themeStore.primaryColor, borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 36
      }
    ]
  });
}

function resizeCharts() {
  typePieChart?.resize();
  groupBarChart?.resize();
}

watch(
  () => [themeStore.darkMode, themeStore.primaryColor],
  () => {
    typePieChart?.dispose();
    groupBarChart?.dispose();
    typePieChart = null;
    groupBarChart = null;
    renderTypePie();
    accountsApi.listGroups().then(g => renderGroupBar(g.groups || []));
  }
);

onMounted(async () => {
  await load();
  window.addEventListener('resize', resizeCharts);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts);
  typePieChart?.dispose();
  groupBarChart?.dispose();
});
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

    <n-grid :cols="2" :x-gap="16" :y-gap="16" class="mt-4" responsive="screen">
      <n-gi>
        <n-card title="账号类型分布">
          <div ref="typePieRef" style="height: 280px;" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="分组账号数">
          <div ref="groupBarRef" style="height: 280px;" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-card class="mt-4" title="使用提示">
      <ul class="pl-5 op-80 text-13px leading-loose">
        <li>左侧导航 <b>邮箱视图</b>：四栏分组 → 账号 → 邮件列表 → 详情</li>
        <li><b>内网邮箱</b>：@cs2jp.com / @jokerque.com 的专用视图，支持本地落库 + 服务端自动删除</li>
        <li><b>临时邮箱</b>：GPTMail / DuckMail / Cloudflare 多 tab 切换</li>
        <li><b>Token 刷新</b>：批量/失败重试支持 SSE 实时进度</li>
        <li><b>设置</b>：修改密码、对外 API Key、主题色、深色模式</li>
      </ul>
    </n-card>
  </div>
</template>
