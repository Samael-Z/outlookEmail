<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useMessage, useDialog } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { accountsApi, type Group, type Account } from '@/service/api/accounts';
import { emailsApi, type EmailListItem, type Folder } from '@/service/api/emails';
import GroupManageDrawer from '@/components/GroupManageDrawer.vue';

const message = useMessage();
const dialog = useDialog();
const showGroupManage = ref(false);
const checked = ref<string[]>([]);
const acting = ref(false);

const groups = ref<Group[]>([]);
const accounts = ref<Account[]>([]);
const selectedGroupId = ref<number | null>(null);
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

const isInternalEml = computed(() => selectedAccount.value?.account_type === 'internal_eml');

async function loadGroups() {
  const r = await accountsApi.listGroups();
  groups.value = r.groups || [];
  if (groups.value.length) await selectGroup(groups.value[0].id);
}

async function selectGroup(id: number) {
  selectedGroupId.value = id;
  selectedAccount.value = null;
  emails.value = [];
  detail.value = null;
  const r = await accountsApi.listAccounts(id);
  // 排除内网 EML 账号——它们有专门的页面
  accounts.value = (r.accounts || []).filter(a => a.account_type !== 'internal_eml');
}

async function selectAccount(account: Account) {
  selectedAccount.value = account;
  detail.value = null;
  folder.value = 'inbox';
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
      return {
        id,
        folder: m?.folder || folder.value,
        id_mode: m?.id_mode
      };
    });
    const r = await emailsApi.markRead(selectedAccount.value.email, items);
    if (r.success) {
      message.success(`已标记 ${r.success_count || items.length} 封为已读`);
      await loadEmails();
      checked.value = [];
    } else {
      message.error(typeof r.error === 'string' ? r.error : '操作失败');
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || '操作失败');
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
      try {
        const r = await emailsApi.deleteMany(
          selectedAccount.value!.email,
          checked.value.map(String)
        );
        if (r.success) {
          message.success(`已删除 ${r.success_count || checked.value.length} 封`);
          await loadEmails();
          checked.value = [];
          if (detail.value && checked.value.includes(String(detail.value.id))) {
            detail.value = null;
          }
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

onMounted(loadGroups);
</script>

<template>
  <div class="wh-full" style="height: calc(100vh - 50px - 40px - 32px);">
    <n-split direction="horizontal" :default-size="0.16" :min="0.1" :max="0.3">
      <!-- 分组 -->
      <template #1>
        <n-card content-style="padding: 0;" class="h-full">
          <template #header>分组</template>
          <template #header-extra>
            <n-button size="tiny" text @click="showGroupManage = true">
              <Icon icon="tabler:settings" />
            </n-button>
          </template>
          <n-list hoverable clickable>
            <n-list-item
              v-for="g in groups"
              :key="g.id"
              @click="selectGroup(g.id)"
              :style="{ background: selectedGroupId === g.id ? 'rgba(100,108,255,0.1)' : '' }"
            >
              <div class="flex-y-center">
                <span
                  class="inline-block w-8px h-8px rounded-full mr-2"
                  :style="{ background: g.color }"
                />
                <span class="text-13px">{{ g.name }}</span>
              </div>
            </n-list-item>
          </n-list>
        </n-card>
      </template>

      <template #2>
        <n-split direction="horizontal" :default-size="0.22" :min="0.15" :max="0.4">
          <!-- 账号 -->
          <template #1>
            <n-card content-style="padding: 0;" class="h-full">
              <template #header>
                <span>账号 ({{ accounts.length }})</span>
              </template>
              <n-empty v-if="!accounts.length" description="此分组无账号" class="mt-12" />
              <n-list v-else hoverable clickable>
                <n-list-item
                  v-for="a in accounts"
                  :key="a.id"
                  @click="selectAccount(a)"
                  :style="{ background: selectedAccount?.id === a.id ? 'rgba(100,108,255,0.1)' : '' }"
                >
                  <div class="text-13px truncate">{{ a.email }}</div>
                  <div class="flex-y-center text-11px op-60 mt-1">
                    <n-tag size="tiny" :bordered="false" type="info">
                      {{ a.account_type }}
                    </n-tag>
                    <span class="ml-2 truncate">{{ a.remark }}</span>
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
                      <n-button
                        v-if="emails.length"
                        size="tiny"
                        @click="selectAll"
                      >
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
                    <n-divider />
                    <div
                      v-if="detail.body?.content || detail.html || detail.body_html"
                      v-html="detail.body?.content || detail.html || detail.body_html"
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

    <GroupManageDrawer v-model:show="showGroupManage" @changed="loadGroups" />
  </div>
</template>

<style scoped>
.email-html :deep(img) {
  max-width: 100%;
}
</style>
