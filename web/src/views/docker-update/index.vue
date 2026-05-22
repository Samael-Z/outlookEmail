<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useMessage, useDialog } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { systemApi, type DockerUpdateConfig } from '@/service/api/system';

const message = useMessage();
const dialog = useDialog();

const config = ref<DockerUpdateConfig | null>(null);
const loading = ref(false);
const starting = ref(false);
let pollTimer: any = null;

const isRunning = computed(() => {
  const s = config.value?.state?.status;
  return s === 'running' || s === 'pulling' || s === 'recreating' || s === 'pending';
});

const statusType = computed(() => {
  const s = (config.value?.state?.status || '').toLowerCase();
  if (s === 'success' || s === 'completed' || s === 'no-update') return 'success';
  if (s === 'failed' || s === 'error') return 'error';
  if (isRunning.value) return 'info';
  return 'default';
});

async function load() {
  loading.value = true;
  try {
    const r = await systemApi.dockerUpdateStatus();
    config.value = r.docker_update;
  } catch (e: any) {
    message.error(e?.response?.data?.error || '加载失败');
  } finally {
    loading.value = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(load, 3000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function triggerUpdate() {
  if (!config.value?.available) return;
  dialog.warning({
    title: '触发 Docker 在线更新',
    content: `将通过 Watchtower 拉取最新镜像并重建容器 ${config.value?.container}。期间服务会短暂中断。`,
    positiveText: '开始更新',
    negativeText: '取消',
    onPositiveClick: async () => {
      starting.value = true;
      try {
        const r = await systemApi.startDockerUpdate();
        if (r.success) {
          message.success(r.message || '已触发更新');
          await load();
          startPolling();
        } else {
          message.error(r.error || '触发失败');
        }
      } catch (e: any) {
        message.error(e?.response?.data?.error || '触发失败');
      } finally {
        starting.value = false;
      }
    }
  });
}

onMounted(async () => {
  await load();
  if (isRunning.value) startPolling();
});

onBeforeUnmount(stopPolling);
</script>

<template>
  <n-spin :show="loading">
    <n-card title="Docker 在线更新">
      <template #header-extra>
        <n-space>
          <n-button @click="load">
            <Icon icon="tabler:refresh" />
            <span class="ml-1">刷新状态</span>
          </n-button>
          <n-button
            type="primary"
            :loading="starting"
            :disabled="!config?.available || isRunning"
            @click="triggerUpdate"
          >
            <Icon icon="tabler:cloud-download" />
            <span class="ml-1">{{ isRunning ? '更新进行中' : '开始更新' }}</span>
          </n-button>
        </n-space>
      </template>

      <n-alert
        v-if="!config?.enabled"
        type="warning"
        :show-icon="false"
        class="mb-3"
      >
        Docker 在线更新未启用。需要在 Docker 容器中设置：
        <code>-e DOCKER_UPDATE_ENABLED=true</code>，
        <code>-e DOCKER_UPDATE_CONTAINER=outlook-mail-reader</code>，
        并挂载 <code>-v /var/run/docker.sock:/var/run/docker.sock</code>。
      </n-alert>
      <n-alert
        v-else-if="!config?.available"
        type="error"
        :show-icon="false"
        class="mb-3"
      >
        无法在线更新：{{ config?.reason }}
      </n-alert>
      <n-alert
        v-else
        type="info"
        :show-icon="false"
        class="mb-3"
      >
        启用 Watchtower 模式：拉取最新镜像并重建 <b>{{ config?.container }}</b>。
        固定版本标签（如 v2.0.x）的容器不能用此功能升级到新版本。
      </n-alert>

      <n-descriptions :column="2" bordered label-placement="left" class="mb-3">
        <n-descriptions-item label="容器名">
          {{ config?.container || '—' }}
        </n-descriptions-item>
        <n-descriptions-item label="当前镜像">
          {{ config?.current_image || '—' }}
        </n-descriptions-item>
        <n-descriptions-item label="Watchtower 镜像">
          {{ config?.watchtower_image || '—' }}
        </n-descriptions-item>
        <n-descriptions-item label="Docker Socket">
          {{ config?.socket_path || '—' }}
        </n-descriptions-item>
        <n-descriptions-item label="API 版本">
          {{ config?.api_version || 'auto' }}
        </n-descriptions-item>
        <n-descriptions-item label="可用性">
          <n-tag
            :type="config?.available ? 'success' : 'error'"
            size="small"
            :bordered="false"
          >
            {{ config?.available ? '可用' : '不可用' }}
          </n-tag>
        </n-descriptions-item>
      </n-descriptions>

      <n-card v-if="config?.state" size="small" title="最近一次任务">
        <n-descriptions :column="2" bordered label-placement="left">
          <n-descriptions-item label="状态">
            <n-tag :type="statusType" size="small" :bordered="false">
              {{ config.state.status || '—' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="开始">
            {{ config.state.started_at || '—' }}
          </n-descriptions-item>
          <n-descriptions-item label="结束">
            {{ config.state.finished_at || '—' }}
          </n-descriptions-item>
          <n-descriptions-item label="尝试次数">
            {{ config.state.attempts ?? 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="是否更新" :span="2">
            <n-tag
              :type="config.state.applied ? 'success' : 'default'"
              size="small"
              :bordered="false"
            >
              {{ config.state.applied ? '已升级' : '未更新（latest 已是最新）' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="消息" :span="2">
            {{ config.state.message || '—' }}
          </n-descriptions-item>
        </n-descriptions>

        <div v-if="config.state.log?.length" class="mt-3">
          <div class="text-12px font-medium mb-1">日志</div>
          <n-scrollbar style="max-height: 240px;">
            <pre class="text-12px p-2 bg-#f5f5f5 dark:bg-#1f1f23 rounded">{{
              config.state.log.join('\n')
            }}</pre>
          </n-scrollbar>
        </div>
      </n-card>
    </n-card>
  </n-spin>
</template>
