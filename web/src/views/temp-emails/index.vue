<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useMessage, useDialog } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { tempEmailsApi, type TempEmail, type TempEmailMessage } from '@/service/api/temp-emails';

const message = useMessage();
const dialog = useDialog();

const tab = ref<'gptmail' | 'duckmail' | 'cloudflare'>('gptmail');
const all = ref<TempEmail[]>([]);
const loading = ref(false);

const selected = ref<TempEmail | null>(null);
const messages = ref<TempEmailMessage[]>([]);
const loadingMessages = ref(false);
const detail = ref<any>(null);
const loadingDetail = ref(false);

// 生成对话框
const showGenerate = ref(false);
const generating = ref(false);
const genForm = ref({
  provider: 'gptmail' as 'gptmail' | 'duckmail' | 'cloudflare',
  prefix: '',
  domain: '',
  username: '',
  password: ''
});
const duckmailDomains = ref<Array<{ value: string; label: string }>>([]);
const cloudflareDomains = ref<Array<{ value: string; label: string }>>([]);

const filtered = computed(() => all.value.filter(e => e.provider === tab.value));

async function load() {
  loading.value = true;
  try {
    const r = await tempEmailsApi.list();
    all.value = r.emails || [];
  } finally {
    loading.value = false;
  }
}

async function selectEmail(e: TempEmail) {
  selected.value = e;
  detail.value = null;
  loadingMessages.value = true;
  try {
    const r = await tempEmailsApi.messages(e.email);
    messages.value = r.messages || r.emails || [];
  } catch (err: any) {
    message.error(err?.response?.data?.error || '加载失败');
    messages.value = [];
  } finally {
    loadingMessages.value = false;
  }
}

async function refresh() {
  if (!selected.value) return;
  try {
    await tempEmailsApi.refresh(selected.value.email);
    await selectEmail(selected.value);
    message.success('已刷新');
  } catch (e: any) {
    message.error(e?.response?.data?.error || '刷新失败');
  }
}

async function openMessage(m: TempEmailMessage) {
  if (!selected.value || !m.id) return;
  loadingDetail.value = true;
  try {
    const r = await tempEmailsApi.messageDetail(selected.value.email, String(m.id));
    detail.value = r.message || r.email;
  } finally {
    loadingDetail.value = false;
  }
}

async function deleteEmail(e: TempEmail) {
  dialog.warning({
    title: '删除临时邮箱',
    content: `确认删除「${e.email}」？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await tempEmailsApi.delete(e.email);
        message.success('已删除');
        if (selected.value?.id === e.id) {
          selected.value = null;
          messages.value = [];
          detail.value = null;
        }
        await load();
      } catch (err: any) {
        message.error(err?.response?.data?.error || '删除失败');
      }
    }
  });
}

async function openGenerate() {
  genForm.value = { provider: tab.value, prefix: '', domain: '', username: '', password: '' };
  showGenerate.value = true;
  if (tab.value === 'duckmail' && !duckmailDomains.value.length) {
    try {
      const r = await tempEmailsApi.duckmailDomains();
      duckmailDomains.value = (r.domains || []).map(d => ({
        value: d.domain,
        label: d.domain
      }));
      if (duckmailDomains.value.length) genForm.value.domain = duckmailDomains.value[0].value;
    } catch {
      // 忽略
    }
  }
  if (tab.value === 'cloudflare' && !cloudflareDomains.value.length) {
    try {
      const r = await tempEmailsApi.cloudflareDomains();
      cloudflareDomains.value = (r.domains || []).map(d => ({
        value: d.domain,
        label: d.domain
      }));
      if (cloudflareDomains.value.length) genForm.value.domain = cloudflareDomains.value[0].value;
    } catch {
      // 忽略
    }
  }
}

async function submitGenerate() {
  generating.value = true;
  try {
    const payload: any = { provider: genForm.value.provider };
    if (genForm.value.provider === 'gptmail') {
      payload.prefix = genForm.value.prefix || undefined;
      payload.domain = genForm.value.domain || undefined;
    } else if (genForm.value.provider === 'duckmail') {
      payload.domain = genForm.value.domain;
      payload.username = genForm.value.username;
      payload.password = genForm.value.password;
    } else {
      payload.domain = genForm.value.domain;
      payload.username = genForm.value.username || undefined;
    }
    const r = await tempEmailsApi.generate(payload);
    if (r.success) {
      message.success(r.message || `已生成 ${r.email}`);
      showGenerate.value = false;
      await load();
    } else {
      message.error(r.error || '生成失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '生成失败');
  } finally {
    generating.value = false;
  }
}

async function copyEmail(addr: string) {
  await navigator.clipboard.writeText(addr);
  message.success('已复制');
}

function senderLabel(m: TempEmailMessage): string {
  if (!m.from) return '';
  if (typeof m.from === 'string') return m.from;
  return m.from?.name || m.from?.address || JSON.stringify(m.from);
}

onMounted(load);
</script>

<template>
  <div class="wh-full" style="height: calc(100vh - 50px - 40px - 32px);">
    <n-card content-style="padding: 0; height: 100%; display: flex; flex-direction: column;">
      <template #header>
        <n-tabs v-model:value="tab" type="line" size="small" @update:value="selected = null">
          <n-tab-pane name="gptmail" tab="GPTMail" />
          <n-tab-pane name="duckmail" tab="DuckMail" />
          <n-tab-pane name="cloudflare" tab="Cloudflare" />
        </n-tabs>
      </template>
      <template #header-extra>
        <n-button type="primary" size="small" @click="openGenerate">
          <Icon icon="tabler:plus" />
          <span class="ml-1">生成</span>
        </n-button>
      </template>

      <div class="flex-1 flex" style="overflow: hidden;">
        <n-split direction="horizontal" :default-size="0.3" :min="0.2" :max="0.5" style="flex:1;">
          <template #1>
            <n-empty v-if="!filtered.length" :description="`暂无 ${tab} 临时邮箱`" class="mt-12" />
            <n-list v-else hoverable clickable style="height: 100%; overflow-y: auto;">
              <n-list-item
                v-for="e in filtered"
                :key="e.id"
                @click="selectEmail(e)"
                :style="{ background: selected?.id === e.id ? 'rgba(100,108,255,0.1)' : '' }"
              >
                <div class="flex-y-center justify-between">
                  <div class="flex-1 min-w-0">
                    <div class="text-13px truncate">{{ e.email }}</div>
                    <div class="text-11px op-60">{{ e.created_at }}</div>
                  </div>
                  <n-space size="small">
                    <n-button text size="tiny" @click.stop="copyEmail(e.email)">
                      <Icon icon="tabler:copy" />
                    </n-button>
                    <n-button text size="tiny" type="error" @click.stop="deleteEmail(e)">
                      <Icon icon="tabler:trash" />
                    </n-button>
                  </n-space>
                </div>
              </n-list-item>
            </n-list>
          </template>

          <template #2>
            <n-split direction="horizontal" :default-size="0.4" :min="0.25" :max="0.6">
              <template #1>
                <n-card content-style="padding: 0; display: flex; flex-direction: column;" class="h-full">
                  <template #header>
                    <span class="text-13px">{{ selected?.email || '邮件列表' }}</span>
                  </template>
                  <template #header-extra>
                    <n-button size="tiny" type="primary" :disabled="!selected" @click="refresh">
                      <Icon icon="tabler:refresh" />
                    </n-button>
                  </template>
                  <n-spin v-if="loadingMessages" />
                  <n-empty v-else-if="!selected" description="选择临时邮箱查看邮件" class="mt-12" />
                  <n-empty v-else-if="!messages.length" description="暂无邮件" class="mt-12" />
                  <n-list v-else hoverable clickable class="flex-1 overflow-auto">
                    <n-list-item
                      v-for="(m, i) in messages"
                      :key="m.id || i"
                      @click="openMessage(m)"
                    >
                      <div class="text-13px font-medium truncate">{{ m.subject || '(无主题)' }}</div>
                      <div class="text-11px op-60 truncate">{{ senderLabel(m) }}</div>
                      <div class="text-11px op-50">
                        {{ m.receivedDateTime || m.date || '' }}
                      </div>
                    </n-list-item>
                  </n-list>
                </n-card>
              </template>
              <template #2>
                <n-card content-style="padding: 0;" class="h-full">
                  <n-spin v-if="loadingDetail" />
                  <n-empty v-else-if="!detail" description="选择邮件查看详情" class="mt-12" />
                  <div v-else class="p-4 h-full overflow-auto">
                    <h2 class="text-18px font-bold mb-2">
                      {{ detail.subject || '(无主题)' }}
                    </h2>
                    <div class="text-12px op-70 mb-3">
                      时间: {{ detail.receivedDateTime || detail.date || '' }}
                    </div>
                    <n-divider />
                    <div
                      v-if="detail.body?.content || detail.html"
                      v-html="detail.body?.content || detail.html"
                      class="email-html"
                    />
                    <pre v-else class="whitespace-pre-wrap text-13px">{{ detail.text || '' }}</pre>
                  </div>
                </n-card>
              </template>
            </n-split>
          </template>
        </n-split>
      </div>
    </n-card>

    <!-- 生成对话框 -->
    <n-modal
      v-model:show="showGenerate"
      preset="card"
      :title="`生成 ${genForm.provider} 临时邮箱`"
      style="width: 480px;"
    >
      <n-form label-placement="left" label-width="80">
        <template v-if="genForm.provider === 'gptmail'">
          <n-form-item label="前缀">
            <n-input v-model:value="genForm.prefix" placeholder="可选，留空随机" />
          </n-form-item>
          <n-form-item label="域名">
            <n-input v-model:value="genForm.domain" placeholder="可选" />
          </n-form-item>
        </template>
        <template v-else-if="genForm.provider === 'duckmail'">
          <n-form-item label="用户名" required>
            <n-input v-model:value="genForm.username" placeholder="3 个字符以上" />
          </n-form-item>
          <n-form-item label="域名" required>
            <n-select v-model:value="genForm.domain" :options="duckmailDomains" />
          </n-form-item>
          <n-form-item label="密码" required>
            <n-input
              v-model:value="genForm.password"
              type="password"
              show-password-on="click"
              placeholder="6 个字符以上"
            />
          </n-form-item>
        </template>
        <template v-else>
          <n-form-item label="用户名">
            <n-input v-model:value="genForm.username" placeholder="可选，留空随机" />
          </n-form-item>
          <n-form-item label="域名" required>
            <n-select
              v-model:value="genForm.domain"
              :options="cloudflareDomains"
              :placeholder="cloudflareDomains.length ? '选择域名' : '请先在设置中配置 Cloudflare'"
            />
          </n-form-item>
        </template>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showGenerate = false">取消</n-button>
          <n-button type="primary" :loading="generating" @click="submitGenerate">生成</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.email-html :deep(img) {
  max-width: 100%;
}
</style>
