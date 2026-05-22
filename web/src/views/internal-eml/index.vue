<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import { accountsApi, type Account } from '@/service/api/accounts';
import {
  internalEmlApi,
  type InternalEmlMessage,
  type InternalEmlMessageDetail
} from '@/service/api/internal-eml';
import { Icon } from '@iconify/vue';

const message = useMessage();

const accounts = ref<Account[]>([]);
const selectedAccountId = ref<number | null>(null);
const messages = ref<InternalEmlMessage[]>([]);
const total = ref(0);
const page = ref(1);
const perPage = 20;
const keyword = ref('');
const loadingList = ref(false);
const refreshing = ref(false);
const detail = ref<InternalEmlMessageDetail | null>(null);
const loadingDetail = ref(false);

async function loadAccounts() {
  const res = await accountsApi.listAccounts();
  accounts.value = (res.accounts || []).filter(a => a.account_type === 'internal_eml');
  if (accounts.value.length && selectedAccountId.value == null) {
    selectedAccountId.value = accounts.value[0].id;
    await loadMessages();
  }
}

async function loadMessages() {
  if (!selectedAccountId.value) return;
  loadingList.value = true;
  try {
    const res = await internalEmlApi.list(selectedAccountId.value, {
      page: page.value,
      per_page: perPage,
      keyword: keyword.value || undefined
    });
    messages.value = res.messages || [];
    total.value = res.total || 0;
  } finally {
    loadingList.value = false;
  }
}

async function refreshFromServer() {
  if (!selectedAccountId.value) return;
  refreshing.value = true;
  try {
    const r = await internalEmlApi.refresh(selectedAccountId.value);
    if (r.success) {
      message.success(`拉取 ${r.fetched} 封，删除 ${r.deleted} 封`);
    } else {
      message.error(r.error || '拉取失败');
    }
    await loadMessages();
  } finally {
    refreshing.value = false;
  }
}

async function selectAccount(id: number) {
  selectedAccountId.value = id;
  page.value = 1;
  detail.value = null;
  await loadMessages();
}

async function openMessage(id: number) {
  if (!selectedAccountId.value) return;
  loadingDetail.value = true;
  try {
    const res = await internalEmlApi.detail(selectedAccountId.value, id);
    detail.value = res.message;
    const m = messages.value.find(x => x.id === id);
    if (m) m.is_read = 1;
  } finally {
    loadingDetail.value = false;
  }
}

async function deleteMessage(id: number) {
  if (!selectedAccountId.value) return;
  await internalEmlApi.remove(selectedAccountId.value, id);
  message.success('已删除');
  if (detail.value?.id === id) detail.value = null;
  await loadMessages();
}

function attachmentUrl(idx: number) {
  if (!selectedAccountId.value || !detail.value) return '#';
  return internalEmlApi.attachmentUrl(selectedAccountId.value, detail.value.id, idx);
}

onMounted(loadAccounts);
</script>

<template>
  <div class="wh-full" style="height: calc(100vh - 50px - 40px - 32px);">
    <n-split direction="horizontal" :default-size="0.18" :min="0.12" :max="0.3">
      <template #1>
        <n-card content-style="padding: 0;" class="h-full" :title="`内网邮箱 (${accounts.length})`">
          <n-empty v-if="!accounts.length" description="无内网邮箱账号" class="mt-12" />
          <n-list v-else hoverable clickable>
            <n-list-item
              v-for="a in accounts"
              :key="a.id"
              @click="selectAccount(a.id)"
              :style="{ background: selectedAccountId === a.id ? 'rgba(100,108,255,0.1)' : '' }"
            >
              <div class="text-13px">{{ a.email }}</div>
              <div class="text-11px op-60">{{ a.imap_host || '默认 baseURL' }}</div>
            </n-list-item>
          </n-list>
        </n-card>
      </template>

      <template #2>
        <n-split direction="horizontal" :default-size="0.4" :min="0.25" :max="0.6">
          <template #1>
            <n-card content-style="padding: 0; display: flex; flex-direction: column;" class="h-full">
              <template #header>
                <div class="flex-y-center w-full gap-2">
                  <n-input
                    v-model:value="keyword"
                    placeholder="搜索主题/发件人/正文"
                    clearable
                    size="small"
                    @keyup.enter="loadMessages()"
                  />
                  <n-button size="small" @click="loadMessages()">
                    <Icon icon="tabler:search" />
                  </n-button>
                  <n-button
                    size="small"
                    type="primary"
                    :loading="refreshing"
                    @click="refreshFromServer"
                  >
                    <Icon icon="tabler:refresh" /> <span class="ml-1">拉取</span>
                  </n-button>
                </div>
              </template>
              <n-empty v-if="!messages.length" description="暂无邮件" class="mt-12" />
              <n-list v-else hoverable clickable class="flex-1 overflow-auto">
                <n-list-item
                  v-for="m in messages"
                  :key="m.id"
                  @click="openMessage(m.id)"
                  :style="{ background: detail?.id === m.id ? 'rgba(100,108,255,0.08)' : '' }"
                >
                  <div class="flex-y-center mb-1">
                    <n-tag v-if="!m.is_read" size="tiny" type="info" class="mr-2">未读</n-tag>
                    <Icon v-if="m.has_attachment" icon="tabler:paperclip" class="mr-1 op-60" />
                    <span class="text-13px font-medium truncate">{{ m.subject || '(无主题)' }}</span>
                  </div>
                  <div class="text-11px op-60 truncate">{{ m.from_addr }}</div>
                  <div class="text-11px op-50">{{ m.received_at || m.fetched_at }}</div>
                </n-list-item>
              </n-list>
              <div v-if="total > 0" class="p-2 border-t border-#eee dark:border-#2c2c32">
                <n-pagination
                  v-model:page="page"
                  :page-size="perPage"
                  :item-count="total"
                  size="small"
                  @update:page="loadMessages()"
                />
              </div>
            </n-card>
          </template>

          <template #2>
            <n-card content-style="padding: 0;" class="h-full">
              <n-empty v-if="!detail && !loadingDetail" description="选择左侧邮件查看详情" class="mt-12" />
              <n-spin v-else-if="loadingDetail" />
              <div v-else-if="detail" class="p-4 h-full overflow-auto">
                <div class="flex-y-center justify-between mb-3">
                  <h2 class="text-18px font-bold">{{ detail.subject || '(无主题)' }}</h2>
                  <n-button size="small" type="error" @click="deleteMessage(detail.id)">
                    删除
                  </n-button>
                </div>
                <div class="text-12px op-70 mb-1">From: {{ detail.from_addr }}</div>
                <div class="text-12px op-70 mb-1">To: {{ detail.to_addr }}</div>
                <div class="text-12px op-70 mb-3">
                  时间: {{ detail.received_at || detail.fetched_at }}
                </div>

                <div v-if="detail.attachments?.length" class="mb-3">
                  <div class="text-12px font-medium mb-1">附件：</div>
                  <n-space>
                    <n-button
                      v-for="(att, i) in detail.attachments"
                      :key="i"
                      size="small"
                      tag="a"
                      :href="attachmentUrl(i)"
                      target="_blank"
                    >
                      <Icon icon="tabler:paperclip" />
                      <span class="ml-1">
                        {{ att.filename || '附件' }}（{{ (att.size / 1024).toFixed(1) }} KB）
                      </span>
                    </n-button>
                  </n-space>
                </div>

                <n-divider />
                <div v-if="detail.body_html" v-html="detail.body_html" class="email-html" />
                <pre v-else class="whitespace-pre-wrap text-13px">{{ detail.body_text }}</pre>
              </div>
            </n-card>
          </template>
        </n-split>
      </template>
    </n-split>
  </div>
</template>

<style scoped>
.email-html :deep(img) {
  max-width: 100%;
}
</style>
