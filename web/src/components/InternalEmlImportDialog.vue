<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMessage } from 'naive-ui';
import { internalEmlApi, type DomainsConfig } from '@/service/api/internal-eml';
import { accountsApi, type Group } from '@/service/api/accounts';
import { Icon } from '@iconify/vue';

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void;
  (e: 'created'): void;
}>();

const message = useMessage();

const mode = ref<'single' | 'bulk'>('single');
const submitting = ref(false);

// 单个
const single = ref({
  email: '',
  api_key: '',
  base_url: '',
  remark: ''
});

// 批量：textarea 每行一个 email[----api_key[----base_url]]
const bulkText = ref('');

const groupId = ref<number | null>(null);
const groups = ref<Group[]>([]);
const domainsConfig = ref<DomainsConfig | null>(null);

watch(
  () => props.show,
  async v => {
    if (v) {
      await loadConfig();
    } else {
      single.value = { email: '', api_key: '', base_url: '', remark: '' };
      bulkText.value = '';
    }
  }
);

async function loadConfig() {
  const [g, d] = await Promise.all([
    accountsApi.listGroups(),
    internalEmlApi.getDomains()
  ]);
  groups.value = (g.groups || []).filter(x => x.name !== '临时邮箱');
  if (!groupId.value && groups.value.length) {
    groupId.value = groups.value[0].id;
  }
  domainsConfig.value = d;
}

const supportedDomains = computed(() => Object.keys(domainsConfig.value?.domains || {}));

const inferredBaseUrl = computed(() => {
  const email = single.value.email.trim();
  if (!email || !email.includes('@')) return '';
  const domain = email.split('@').pop()!.toLowerCase();
  return domainsConfig.value?.domains?.[domain] || '';
});

async function submit() {
  if (mode.value === 'single') {
    if (!single.value.email || !single.value.email.includes('@')) {
      message.warning('请输入完整邮箱地址');
      return;
    }
    submitting.value = true;
    try {
      const res = await internalEmlApi.createAccount({
        email: single.value.email.trim(),
        api_key: single.value.api_key.trim() || undefined,
        base_url: single.value.base_url.trim() || undefined,
        remark: single.value.remark.trim() || undefined,
        group_id: groupId.value ?? undefined
      });
      if (res.success) {
        message.success('账号创建成功');
        emit('created');
        emit('update:show', false);
      } else {
        message.error(res.error || '创建失败');
      }
    } catch (e: any) {
      message.error(e?.response?.data?.error || '创建失败');
    } finally {
      submitting.value = false;
    }
  } else {
    const items = parseBulk(bulkText.value);
    if (!items.length) {
      message.warning('请至少输入一行邮箱');
      return;
    }
    submitting.value = true;
    try {
      const res = await internalEmlApi.bulkCreate(items, groupId.value ?? undefined);
      message.success(`创建 ${res.created_count} 个，跳过 ${res.skipped_count} 个`);
      if (res.skipped_count > 0) {
        message.info(
          '跳过原因: ' +
            res.skipped.map(s => `${s.email}: ${s.reason}`).join(' | '),
          { duration: 8000 }
        );
      }
      emit('created');
      if (res.created_count > 0) emit('update:show', false);
    } finally {
      submitting.value = false;
    }
  }
}

function parseBulk(text: string) {
  return text
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => {
      const parts = line.split('----');
      const email = parts[0]?.trim() || '';
      const api_key = parts[1]?.trim() || undefined;
      const base_url = parts[2]?.trim() || undefined;
      return { email, api_key, base_url };
    })
    .filter(x => x.email && x.email.includes('@'));
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="添加内网邮箱账号"
    style="width: 540px;"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-tabs v-model:value="mode" type="line" animated>
      <n-tab-pane name="single" tab="单个">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="邮箱" required>
            <n-input v-model:value="single.email" placeholder="xxx@cs2jp.com 或 xxx@jokerque.com" />
          </n-form-item>
          <n-form-item label="API Key">
            <n-input
              v-model:value="single.api_key"
              :placeholder="`留空使用默认（${domainsConfig?.default_key || '内置'}）`"
            />
          </n-form-item>
          <n-form-item label="baseURL">
            <n-input
              v-model:value="single.base_url"
              :placeholder="inferredBaseUrl || '留空则按域名自动解析'"
            />
            <template #feedback>
              <span v-if="inferredBaseUrl" class="op-70">
                自动识别: <code>{{ inferredBaseUrl }}</code>
              </span>
            </template>
          </n-form-item>
          <n-form-item label="分组">
            <n-select
              v-model:value="groupId"
              :options="groups.map(g => ({ label: g.name, value: g.id }))"
              placeholder="选择分组"
            />
          </n-form-item>
          <n-form-item label="备注">
            <n-input v-model:value="single.remark" placeholder="可选" />
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="bulk" tab="批量">
        <div class="text-12px op-70 mb-2">
          每行一个邮箱。三种格式都支持（自动识别）：
          <pre class="bg-#f5f5f5 dark:bg-#1f1f23 p-2 rounded text-11px mt-1">xxx@jokerque.com
xxx@jokerque.com----api_key
xxx@jokerque.com----api_key----http://custom-server:8080</pre>
        </div>
        <n-input
          v-model:value="bulkText"
          type="textarea"
          :rows="10"
          placeholder="user1@jokerque.com&#10;user2@cs2jp.com"
        />
        <n-form-item label="分组" label-placement="left" label-width="100" class="mt-2">
          <n-select
            v-model:value="groupId"
            :options="groups.map(g => ({ label: g.name, value: g.id }))"
          />
        </n-form-item>
      </n-tab-pane>
    </n-tabs>

    <div class="text-12px op-60 mt-2">
      <Icon icon="tabler:info-circle" class="inline-block align-middle" />
      支持的域名：{{ supportedDomains.join('，') || '加载中…' }}
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="submit">
          {{ mode === 'single' ? '创建' : '批量导入' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>
