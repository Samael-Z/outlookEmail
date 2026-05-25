<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useMessage, useDialog } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { accountsApi, type Account } from '@/service/api/accounts';
import { emailsApi, type EmailListItem, type Folder } from '@/service/api/emails';
import GroupManageDrawer from '@/components/GroupManageDrawer.vue';
import { sanitizeEmailHtml } from '@/utils/sanitize';

const message = useMessage();
const dialog = useDialog();
const showGroupManage = ref(false);
const checked = ref<string[]>([]);
const acting = ref(false);

// 全量账号（一次拉完，前端按 provider 分组）
const allAccounts = ref<Account[]>([]);
const loadingAccounts = ref(false);

// 按 provider 分类的元数据
interface ProviderCategory {
  key: string;
  label: string;
  icon: string;
  color: string;
  matches: (a: Account) => boolean;
}
const PERSONAL_TAG_NAME = '个人常用';

const PROVIDER_CATEGORIES: ProviderCategory[] = [
  {
    key: 'outlook',
    label: 'Outlook / Hotmail',
    icon: 'tabler:brand-windows',
    color: '#0078d4',
    matches: a => a.account_type === 'outlook' || a.provider === 'outlook'
  },
  {
    key: 'gmail',
    label: 'Gmail',
    icon: 'tabler:brand-google',
    color: '#ea4335',
    matches: a => a.provider === 'gmail'
  },
  {
    key: 'qq',
    label: 'QQ 邮箱',
    icon: 'tabler:brand-tencent-qq',
    color: '#1296db',
    matches: a => a.provider === 'qq'
  },
  {
    key: '163',
    label: '163 邮箱',
    icon: 'tabler:mail',
    color: '#d22f2f',
    matches: a => a.provider === '163'
  },
  {
    key: '126',
    label: '126 邮箱',
    icon: 'tabler:mail',
    color: '#a02828',
    matches: a => a.provider === '126'
  },
  {
    key: 'yahoo',
    label: 'Yahoo',
    icon: 'tabler:brand-yahoo',
    color: '#7e1fff',
    matches: a => a.provider === 'yahoo'
  },
  {
    key: 'aliyun',
    label: '阿里邮箱',
    icon: 'tabler:cloud',
    color: '#ff6a00',
    matches: a => a.provider === 'aliyun'
  },
  {
    key: 'custom',
    label: '自定义 IMAP',
    icon: 'tabler:server',
    color: '#646cff',
    matches: a => a.account_type === 'imap' && a.provider === 'custom'
  }
  // 内网 EML 不在此处展示：它有专门的 /internal-eml 页面，
  // 这里只承载日常邮箱（Outlook/Gmail/QQ/163 等）。
];

const selectedCategory = ref<string>('personal'); // 默认显示"个人常用"
const selectedAccount = ref<Account | null>(null);

const folder = ref<Folder>('inbox');
const emails = ref<EmailListItem[]>([]);
const loadingEmails = ref(false);
const refreshing = ref(false);
const detail = ref<any>(null);
const loadingDetail = ref(false);

const folderOptions: { label: string; value: Folder }[] = [
  { label: '收件箱', value: 'inbox' },
  { label: '垃圾邮件', value: 'junkemail' },
  { label: '已删除', value: 'deleteditems' },
  { label: '全部', value: 'all' }
];

// internal_eml 在此页面已被过滤，此 flag 永远为 false，但保留以减少模板改动
const isInternalEml = computed(() => false);

// 是否带"个人常用"标签
function isPersonal(a: Account): boolean {
  return (a.tags || []).some(t => t.name === PERSONAL_TAG_NAME);
}

const personalCount = computed(() => allAccounts.value.filter(isPersonal).length);

// 当前分类下的账号
const filteredAccounts = computed(() => {
  if (selectedCategory.value === 'personal') {
    return allAccounts.value.filter(isPersonal);
  }
  const cat = PROVIDER_CATEGORIES.find(c => c.key === selectedCategory.value);
  if (!cat) return [];
  return allAccounts.value.filter(cat.matches);
});

// 每个 provider 的账号数
const categoryCounts = computed(() => {
  const counts: Record<string, number> = {};
  for (const c of PROVIDER_CATEGORIES) {
    counts[c.key] = allAccounts.value.filter(c.matches).length;
  }
  return counts;
});

async function loadAccounts() {
  loadingAccounts.value = true;
  try {
    const r = await accountsApi.listAccounts({ limit: 1000 });
    // 内网 EML 账号有专门的 /internal-eml 页面，此处不展示
    allAccounts.value = (r.accounts || []).filter(a => a.account_type !== 'internal_eml');
  } finally {
    loadingAccounts.value = false;
  }
}

function selectCategory(key: string) {
  selectedCategory.value = key;
  selectedAccount.value = null;
  emails.value = [];
  detail.value = null;
  checked.value = [];
}

async function selectAccount(account: Account) {
  selectedAccount.value = account;
  detail.value = null;
  folder.value = 'inbox';
  emails.value = [];
  checked.value = [];
  await loadEmails();
}

async function loadEmails() {
  if (!selectedAccount.value) return;
  loadingEmails.value = true;
  try {
    const r = await emailsApi.list(selectedAccount.value.email, {
      folder: folder.value,
      top: 30
    });
    if (r.success) {
      emails.value = r.emails || [];
    } else {
      message.error(typeof r.error === 'string' ? r.error : '加载失败');
      emails.value = [];
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '加载失败');
  } finally {
    loadingEmails.value = false;
  }
}

async function refreshEmails() {
  refreshing.value = true;
  try {
    await loadEmails();
  } finally {
    refreshing.value = false;
  }
}

async function openEmail(item: EmailListItem) {
  if (!selectedAccount.value || !item.id) return;
  loadingDetail.value = true;
  try {
    const r = await emailsApi.detail(selectedAccount.value.email, String(item.id));
    if (r.success) {
      detail.value = r.email;
    } else {
      message.error(typeof r.error === 'string' ? r.error : '加载详情失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '加载详情失败');
  } finally {
    loadingDetail.value = false;
  }
}

function toggleCheck(id: string) {
  const idx = checked.value.indexOf(id);
  if (idx >= 0) checked.value.splice(idx, 1);
  else checked.value.push(id);
}

function selectAll() {
  if (checked.value.length === emails.value.length) {
    checked.value = [];
  } else {
    checked.value = emails.value.filter(e => e.id).map(e => String(e.id));
  }
}

async function batchMarkRead() {
  if (!selectedAccount.value || !checked.value.length) return;
  acting.value = true;
  try {
    const items = checked.value.map(id => {
      const m = emails.value.find(e => String(e.id) === id);
      return { id, folder: m?.folder || folder.value, id_mode: m?.id_mode };
    });
    const r = await emailsApi.markRead(selectedAccount.value.email, items);
    if (r.success) {
      message.success(`已标记 ${r.success_count || items.length} 封为已读`);
      checked.value = [];
      await loadEmails();
    }
  } finally {
    acting.value = false;
  }
}

function batchDelete() {
  if (!selectedAccount.value || !checked.value.length) return;
  dialog.warning({
    title: '永久删除',
    content: `确定永久删除选中的 ${checked.value.length} 封邮件？该操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      acting.value = true;
      const deletedIds = checked.value.map(String);
      const detailWasDeleted = !!(detail.value && deletedIds.includes(String(detail.value.id)));
      try {
        const r = await emailsApi.deleteMany(selectedAccount.value!.email, deletedIds);
        if (r.success) {
          message.success(`已删除 ${r.success_count || deletedIds.length} 封`);
          checked.value = [];
          if (detailWasDeleted) detail.value = null;
          await loadEmails();
        } else {
          message.error(typeof r.error === 'string' ? r.error : '删除失败');
        }
      } catch (e: any) {
        message.error(e?.response?.data?.error || '删除失败');
      } finally {
        acting.value = false;
      }
    }
  });
}

function senderLabel(item: EmailListItem): string {
  if (!item.from) return '';
  if (typeof item.from === 'string') return item.from;
  return item.from.name || item.from.address || '';
}

function dateLabel(item: EmailListItem): string {
  return item.receivedDateTime || item.date || '';
}

function previewText(item: EmailListItem): string {
  return item.preview || item.bodyPreview || '';
}

onMounted(loadAccounts);
</script>

<template>
  <div class="wh-full" style="height: calc(100vh - 50px - 40px - 32px);">
    <n-split direction="horizontal" :default-size="0.16" :min="0.12" :max="0.28">
      <!-- 左栏：按 provider 分类 + 个人常用 -->
      <template #1>
        <n-card content-style="padding: 0;" class="h-full">
          <template #header>
            <span class="text-13px">分类</span>
          </template>
          <template #header-extra>
            <n-button size="tiny" text @click="showGroupManage = true" title="管理用户分组">
              <Icon icon="tabler:settings" />
            </n-button>
          </template>

          <n-scrollbar style="max-height: calc(100% - 0px);">
            <!-- 个人常用 -->
            <div class="category-section">
              <div class="category-header">置顶</div>
              <div
                class="category-item"
                :class="{ active: selectedCategory === 'personal' }"
                @click="selectCategory('personal')"
              >
                <Icon icon="tabler:star" class="category-icon" style="color: #f0a020;" />
                <span class="category-label">个人常用</span>
                <span class="category-count">{{ personalCount }}</span>
              </div>
              <div v-if="personalCount === 0" class="category-hint">
                给账号打"个人常用"标签后会出现在这里
              </div>
            </div>

            <!-- 按服务商 -->
            <div class="category-section">
              <div class="category-header">按服务商</div>
              <div
                v-for="cat in PROVIDER_CATEGORIES"
                :key="cat.key"
                class="category-item"
                :class="{ active: selectedCategory === cat.key, disabled: categoryCounts[cat.key] === 0 }"
                @click="selectCategory(cat.key)"
              >
                <Icon :icon="cat.icon" class="category-icon" :style="{ color: cat.color }" />
                <span class="category-label">{{ cat.label }}</span>
                <span class="category-count">{{ categoryCounts[cat.key] }}</span>
              </div>
            </div>
          </n-scrollbar>
        </n-card>
      </template>

      <template #2>
        <n-split direction="horizontal" :default-size="0.22" :min="0.15" :max="0.4">
          <!-- 账号列表 -->
          <template #1>
            <n-card content-style="padding: 0;" class="h-full">
              <template #header>
                <span>账号 ({{ filteredAccounts.length }})</span>
              </template>
              <n-spin v-if="loadingAccounts" />
              <n-empty
                v-else-if="!filteredAccounts.length"
                :description="selectedCategory === 'personal' ? '未标记常用账号' : '此分类无账号'"
                class="mt-12"
              />
              <n-list v-else hoverable clickable>
                <n-list-item
                  v-for="a in filteredAccounts"
                  :key="a.id"
                  @click="selectAccount(a)"
                  :style="{ background: selectedAccount?.id === a.id ? 'rgba(100,108,255,0.1)' : '' }"
                >
                  <div class="text-13px truncate">{{ a.email }}</div>
                  <div class="flex-y-center text-11px op-60 mt-1">
                    <n-tag v-if="isPersonal(a)" size="tiny" :bordered="false" type="warning" class="mr-1">
                      <template #icon>
                        <Icon icon="tabler:star-filled" />
                      </template>
                      常用
                    </n-tag>
                    <span class="truncate">{{ a.remark || a.account_type }}</span>
                  </div>
                </n-list-item>
              </n-list>
            </n-card>
          </template>

          <template #2>
            <n-split direction="horizontal" :default-size="0.4" :min="0.25" :max="0.6">
              <!-- 邮件列表 -->
              <template #1>
                <n-card content-style="padding: 0; display: flex; flex-direction: column;" class="h-full">
                  <template #header>
                    <n-select
                      v-model:value="folder"
                      :options="folderOptions"
                      size="small"
                      style="width: 130px;"
                      @update:value="loadEmails"
                    />
                  </template>
                  <template #header-extra>
                    <n-space size="small">
                      <n-button v-if="emails.length" size="tiny" @click="selectAll">
                        {{ checked.length === emails.length ? '清空' : '全选' }}
                      </n-button>
                      <n-button
                        v-if="checked.length"
                        size="tiny"
                        :loading="acting"
                        @click="batchMarkRead"
                      >
                        <Icon icon="tabler:eye-check" />
                        <span class="ml-1">已读 ({{ checked.length }})</span>
                      </n-button>
                      <n-button
                        v-if="checked.length"
                        size="tiny"
                        type="error"
                        :loading="acting"
                        @click="batchDelete"
                      >
                        <Icon icon="tabler:trash" />
                      </n-button>
                      <n-button
                        size="small"
                        type="primary"
                        :loading="refreshing"
                        :disabled="!selectedAccount"
                        @click="refreshEmails"
                      >
                        <Icon icon="tabler:refresh" />
                      </n-button>
                    </n-space>
                  </template>

                  <n-spin v-if="loadingEmails" />
                  <n-empty
                    v-else-if="!selectedAccount"
                    description="选择账号开始查看邮件"
                    class="mt-12"
                  />
                  <n-empty v-else-if="!emails.length" description="无邮件" class="mt-12" />
                  <n-list v-else hoverable clickable class="flex-1 overflow-auto">
                    <n-list-item
                      v-for="(e, i) in emails"
                      :key="e.id || i"
                      @click="openEmail(e)"
                      :style="{ background: detail?.id === e.id ? 'rgba(100,108,255,0.08)' : '' }"
                    >
                      <div class="flex-y-center mb-1">
                        <n-checkbox
                          v-if="e.id"
                          :checked="checked.includes(String(e.id))"
                          class="mr-2"
                          @click.stop
                          @update:checked="() => toggleCheck(String(e.id))"
                        />
                        <n-tag v-if="e.isUnread || e.isRead === false" size="tiny" type="info" class="mr-2">
                          未读
                        </n-tag>
                        <Icon v-if="e.hasAttachments" icon="tabler:paperclip" class="mr-1 op-60" />
                        <span class="text-13px font-medium truncate flex-1">
                          {{ e.subject || '(无主题)' }}
                        </span>
                      </div>
                      <div class="text-11px op-60 truncate">{{ senderLabel(e) }}</div>
                      <div class="text-11px op-50">{{ dateLabel(e) }}</div>
                      <div v-if="previewText(e)" class="text-11px op-50 truncate mt-1">
                        {{ previewText(e) }}
                      </div>
                    </n-list-item>
                  </n-list>
                </n-card>
              </template>

              <!-- 邮件详情 -->
              <template #2>
                <n-card content-style="padding: 0;" class="h-full">
                  <n-spin v-if="loadingDetail" />
                  <n-empty
                    v-else-if="!detail"
                    description="选择左侧邮件查看详情"
                    class="mt-12"
                  />
                  <div v-else class="p-4 h-full overflow-auto">
                    <h2 class="text-18px font-bold mb-3">
                      {{ detail.subject || '(无主题)' }}
                    </h2>
                    <div class="text-12px op-70 mb-1">
                      From:
                      {{
                        typeof detail.from === 'string'
                          ? detail.from
                          : (detail.from?.name || detail.from?.address || '')
                      }}
                    </div>
                    <div v-if="detail.to || detail.toRecipients" class="text-12px op-70 mb-1">
                      To:
                      {{
                        Array.isArray(detail.toRecipients)
                          ? detail.toRecipients.map((r: any) => r.emailAddress?.address || r.address || r).join(', ')
                          : (detail.to || '')
                      }}
                    </div>
                    <div class="text-12px op-70 mb-3">
                      时间: {{ detail.receivedDateTime || detail.date || '' }}
                    </div>

                    <div v-if="detail.attachments?.length" class="mb-3">
                      <div class="text-12px font-medium mb-1">附件：</div>
                      <n-space>
                        <n-button
                          v-for="(att, i) in detail.attachments"
                          :key="i"
                          size="small"
                          tag="a"
                          :href="att.url || '#'"
                          target="_blank"
                        >
                          <Icon icon="tabler:paperclip" />
                          <span class="ml-1">
                            {{ att.filename || '附件' }}
                            <span v-if="att.size"> ({{ (att.size / 1024).toFixed(1) }} KB)</span>
                          </span>
                        </n-button>
                      </n-space>
                    </div>

                    <n-divider />
                    <div
                      v-if="detail.body?.content || detail.html || detail.body_html"
                      v-html="sanitizeEmailHtml(detail.body?.content || detail.html || detail.body_html)"
                      class="email-html"
                    />
                    <pre v-else class="whitespace-pre-wrap text-13px">{{ detail.text || detail.body_text || '' }}</pre>
                  </div>
                </n-card>
              </template>
            </n-split>
          </template>
        </n-split>
      </template>
    </n-split>

    <GroupManageDrawer v-model:show="showGroupManage" @changed="loadAccounts" />
  </div>
</template>

<style scoped>
.category-section {
  padding: 6px 8px 12px;
}
.category-header {
  font-size: 11px;
  opacity: 0.5;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 6px 8px 4px;
  font-weight: 600;
}
.category-item {
  display: flex;
  align-items: center;
  padding: 7px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s ease;
  user-select: none;
}
.category-item:hover {
  background: rgba(100, 108, 255, 0.06);
}
.category-item.active {
  background: rgba(100, 108, 255, 0.14);
  color: #646cff;
  font-weight: 500;
}
.category-item.disabled {
  opacity: 0.4;
}
.category-icon {
  font-size: 18px;
  margin-right: 8px;
  flex-shrink: 0;
}
.category-label {
  flex: 1;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.category-count {
  font-size: 11px;
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 8px;
  border-radius: 10px;
  margin-left: 4px;
}
.category-item.active .category-count {
  background: #646cff;
  color: white;
}
.category-hint {
  font-size: 11px;
  opacity: 0.5;
  padding: 4px 10px 8px;
  line-height: 1.4;
}

.email-html :deep(img) {
  max-width: 100%;
}
</style>
