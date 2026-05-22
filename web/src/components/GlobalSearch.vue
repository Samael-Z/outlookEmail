<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { accountsApi, type Account } from '@/service/api/accounts';

const router = useRouter();

const show = ref(false);
const q = ref('');
const loading = ref(false);
const results = ref<Account[]>([]);
let timer: any = null;

function open() {
  show.value = true;
  q.value = '';
  results.value = [];
  setTimeout(() => {
    const input = document.querySelector('.global-search-input input') as HTMLInputElement;
    input?.focus();
  }, 50);
}

watch(q, value => {
  if (timer) clearTimeout(timer);
  if (!value.trim()) {
    results.value = [];
    loading.value = false;
    return;
  }
  loading.value = true;
  timer = setTimeout(async () => {
    try {
      const r = await accountsApi.search(value.trim(), 20);
      results.value = r.accounts || [];
    } catch {
      results.value = [];
    } finally {
      loading.value = false;
    }
  }, 220);
});

function go(a: Account) {
  show.value = false;
  if (a.account_type === 'internal_eml') {
    router.push('/internal-eml');
  } else if (a.account_type === 'imap' || a.account_type === 'outlook') {
    router.push('/mailbox');
  } else {
    router.push('/accounts');
  }
}

function onKey(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    open();
  }
}
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', onKey);
}

defineExpose({ open });
</script>

<template>
  <div>
    <n-button text class="mr-2" @click="open">
      <Icon icon="tabler:search" class="text-18px" />
      <span class="ml-1 text-12px op-60 hidden md:inline">搜索 (Ctrl+K)</span>
    </n-button>

    <n-modal
      v-model:show="show"
      preset="card"
      title="全局搜索"
      style="width: 560px;"
      :auto-focus="true"
    >
      <n-input
        v-model:value="q"
        size="large"
        placeholder="按邮箱地址 / 备注搜索…"
        class="global-search-input"
        clearable
      >
        <template #prefix>
          <Icon icon="tabler:search" />
        </template>
      </n-input>

      <n-spin :show="loading" class="mt-3">
        <n-empty v-if="!loading && q && !results.length" description="无匹配" class="my-6" />
        <n-list v-else hoverable clickable class="mt-2">
          <n-list-item v-for="a in results" :key="a.id" @click="go(a)">
            <div class="flex-y-center">
              <Icon
                :icon="
                  a.account_type === 'internal_eml'
                    ? 'tabler:building-lighthouse'
                    : a.account_type === 'outlook'
                    ? 'tabler:brand-windows'
                    : 'tabler:mail'
                "
                class="text-18px mr-3 op-70"
              />
              <div class="flex-1 min-w-0">
                <div class="text-13px font-medium truncate">{{ a.email }}</div>
                <div class="text-11px op-60 truncate">
                  {{ a.account_type }} · {{ a.remark || '无备注' }}
                </div>
              </div>
              <Icon icon="tabler:arrow-right" class="op-50 ml-2" />
            </div>
          </n-list-item>
        </n-list>
      </n-spin>
    </n-modal>
  </div>
</template>
