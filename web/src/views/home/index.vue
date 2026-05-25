<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Icon } from '@iconify/vue';
import * as echarts from 'echarts/core';
import { PieChart, LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { homeApi, type HomeStats } from '@/service/api/home';
import { useThemeStore } from '@/store/modules/theme';

echarts.use([
  PieChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer
]);

const { t } = useI18n();
const themeStore = useThemeStore();

const data = ref<HomeStats | null>(null);
const loading = ref(false);

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '夜深了，早点休息';
  if (h < 11) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

const cards = computed(() => [
  {
    key: 'accounts',
    label: '账号总数',
    value: data.value?.totals.accounts ?? 0,
    icon: 'tabler:users',
    gradient: 'linear-gradient(135deg, #ec4786 0%, #b955a4 100%)'
  },
  {
    key: 'groups',
    label: '分组数',
    value: data.value?.totals.groups ?? 0,
    icon: 'tabler:folders',
    gradient: 'linear-gradient(135deg, #865ec0 0%, #5144b4 100%)'
  },
  {
    key: 'temp_emails',
    label: '临时邮箱',
    value: data.value?.totals.temp_emails ?? 0,
    icon: 'tabler:mail-fast',
    gradient: 'linear-gradient(135deg, #56cdf3 0%, #719de3 100%)'
  },
  {
    key: 'internal_eml',
    label: '内网邮箱',
    value: data.value?.totals.internal_eml ?? 0,
    icon: 'tabler:building-lighthouse',
    gradient: 'linear-gradient(135deg, #fcbc25 0%, #f68057 100%)'
  }
]);

const lineRef = ref<HTMLElement | null>(null);
const donutRef = ref<HTMLElement | null>(null);
let lineChart: echarts.ECharts | null = null;
let donutChart: echarts.ECharts | null = null;

const isDark = computed(() => themeStore.darkMode);
const axisColor = computed(() => (isDark.value ? '#aaa' : '#666'));
const gridLineColor = computed(() => (isDark.value ? '#2c2c32' : '#eee'));

async function load() {
  loading.value = true;
  try {
    data.value = await homeApi.stats();
  } finally {
    loading.value = false;
  }
}

function renderLine() {
  if (!lineRef.value || !data.value) return;
  if (!lineChart) lineChart = echarts.init(lineRef.value);
  const daily = data.value.internal_eml_daily;
  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 24, left: 40, right: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: daily.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: gridLineColor.value } },
      axisLabel: { color: axisColor.value, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: axisColor.value },
      splitLine: { lineStyle: { color: gridLineColor.value } }
    },
    series: [
      {
        name: '内网邮件入库',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        sampling: 'lttb',
        data: daily.map(d => d.count),
        itemStyle: { color: '#646cff' },
        lineStyle: { width: 2, color: '#646cff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(100,108,255,0.45)' },
            { offset: 1, color: 'rgba(100,108,255,0.05)' }
          ])
        }
      }
    ]
  });
}

function renderDonut() {
  if (!donutRef.value || !data.value) return;
  if (!donutChart) donutChart = echarts.init(donutRef.value);
  const t = data.value.totals;
  donutChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      left: 'center',
      textStyle: { color: isDark.value ? '#ddd' : '#333' }
    },
    series: [
      {
        type: 'pie',
        radius: ['58%', '78%'],
        center: ['50%', '45%'],
        itemStyle: {
          borderRadius: 8,
          borderColor: isDark.value ? '#18181c' : '#fff',
          borderWidth: 3
        },
        label: { show: false },
        labelLine: { show: false },
        data: [
          { value: t.outlook, name: 'Outlook OAuth', itemStyle: { color: '#2080f0' } },
          { value: t.imap, name: 'IMAP', itemStyle: { color: '#18a058' } },
          { value: t.internal_eml, name: '内网 EML', itemStyle: { color: '#f0a020' } }
        ].filter(x => x.value > 0)
      }
    ]
  });
}

function resize() {
  lineChart?.resize();
  donutChart?.resize();
}

watch(
  () => [isDark.value, data.value],
  () => {
    if (data.value) {
      renderLine();
      renderDonut();
    }
  },
  { deep: true }
);

onMounted(async () => {
  await load();
  renderLine();
  renderDonut();
  window.addEventListener('resize', resize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize);
  lineChart?.dispose();
  donutChart?.dispose();
});
</script>

<template>
  <div class="home-page">
    <!-- 顶部欢迎横幅 -->
    <n-card class="welcome-banner mb-4" :bordered="false">
      <div class="flex-y-center justify-between flex-wrap gap-4">
        <div class="flex-y-center">
          <div class="banner-icon">
            <Icon icon="tabler:mail-bolt" />
          </div>
          <div class="ml-4">
            <div class="text-20px font-bold">
              {{ greeting }}，欢迎使用 {{ t('app.name') }}
            </div>
            <div class="text-13px op-70 mt-1">
              今日是个适合管理收件箱的好天气 ☕
            </div>
          </div>
        </div>
        <div class="flex gap-8">
          <div class="banner-stat">
            <div class="text-12px op-60">激活账号</div>
            <div class="text-22px font-bold mt-1">
              {{ data?.totals.active ?? 0 }}
            </div>
          </div>
          <div class="banner-stat">
            <div class="text-12px op-60">已开转发</div>
            <div class="text-22px font-bold mt-1">
              {{ data?.totals.forwarding ?? 0 }}
            </div>
          </div>
          <div class="banner-stat">
            <div class="text-12px op-60">近 7 天失败</div>
            <div class="text-22px font-bold mt-1 text-error">
              {{ data?.refresh_recent.failed ?? 0 }}
            </div>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 4 张彩色渐变卡 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi v-for="card in cards" :key="card.key">
        <div class="stat-card" :style="{ background: card.gradient }">
          <div class="stat-label">{{ card.label }}</div>
          <Icon :icon="card.icon" class="stat-watermark" />
          <div class="stat-value">{{ card.value.toLocaleString() }}</div>
        </div>
      </n-gi>
    </n-grid>

    <!-- 两张图表 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen" class="mt-4">
      <n-gi :span="2">
        <n-card title="内网邮件最近 14 天入库" :bordered="false">
          <div ref="lineRef" style="height: 320px;" />
        </n-card>
      </n-gi>
      <n-gi :span="1">
        <n-card title="账号类型分布" :bordered="false">
          <div ref="donutRef" style="height: 320px;" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 快捷链接 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" class="mt-4">
      <n-gi>
        <n-card hoverable @click="$router.push('/mailbox')" class="quick-link">
          <div class="flex-y-center">
            <Icon icon="tabler:mail" class="text-28px text-primary mr-3" />
            <div>
              <div class="text-14px font-medium">邮箱视图</div>
              <div class="text-12px op-60">分组 → 账号 → 邮件</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable @click="$router.push('/internal-eml')" class="quick-link">
          <div class="flex-y-center">
            <Icon icon="tabler:building-lighthouse" class="text-28px text-warning mr-3" />
            <div>
              <div class="text-14px font-medium">内网邮箱</div>
              <div class="text-12px op-60">@cs2jp / @jokerque</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable @click="$router.push('/refresh')" class="quick-link">
          <div class="flex-y-center">
            <Icon icon="tabler:refresh" class="text-28px text-info mr-3" />
            <div>
              <div class="text-14px font-medium">Token 刷新</div>
              <div class="text-12px op-60">SSE 实时进度</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable @click="$router.push('/settings')" class="quick-link">
          <div class="flex-y-center">
            <Icon icon="tabler:settings" class="text-28px text-success mr-3" />
            <div>
              <div class="text-14px font-medium">系统设置</div>
              <div class="text-12px op-60">密码 / 主题 / API</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<style scoped>
.home-page {
  padding-bottom: 16px;
}

.welcome-banner {
  background: linear-gradient(135deg, rgba(100, 108, 255, 0.08) 0%, rgba(199, 95, 213, 0.08) 100%);
}

:deep(.dark) .welcome-banner {
  background: linear-gradient(135deg, rgba(100, 108, 255, 0.18) 0%, rgba(199, 95, 213, 0.18) 100%);
}

.banner-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #646cff 0%, #b955a4 100%);
  color: white;
  font-size: 28px;
  box-shadow: 0 8px 20px rgba(100, 108, 255, 0.3);
}

.banner-stat {
  text-align: center;
  min-width: 80px;
}

/* 彩色渐变统计卡 */
.stat-card {
  position: relative;
  padding: 22px 20px;
  border-radius: 12px;
  color: white;
  overflow: hidden;
  cursor: default;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  min-height: 130px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
}

.stat-label {
  font-size: 14px;
  opacity: 0.95;
  letter-spacing: 0.4px;
  font-weight: 500;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.stat-watermark {
  position: absolute;
  right: -10px;
  bottom: -10px;
  font-size: 110px;
  color: white;
  opacity: 0.18;
  pointer-events: none;
}

.quick-link {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.quick-link:hover {
  transform: translateY(-2px);
}
</style>
