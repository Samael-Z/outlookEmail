<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { accountsApi, type Group, type Account } from '@/service/api/accounts';

const groups = ref<Group[]>([]);
const accounts = ref<Account[]>([]);
const selectedGroupId = ref<number | null>(null);
const selectedAccountId = ref<number | null>(null);

async function loadGroups() {
  const res = await accountsApi.listGroups();
  groups.value = res.groups || [];
  if (groups.value.length) {
    selectedGroupId.value = groups.value[0].id;
    await loadAccounts(groups.value[0].id);
  }
}

async function loadAccounts(groupId: number) {
  const res = await accountsApi.listAccounts(groupId);
  accounts.value = res.accounts || [];
  selectedAccountId.value = null;
}

async function selectGroup(id: number) {
  selectedGroupId.value = id;
  await loadAccounts(id);
}

onMounted(loadGroups);
</script>

<template>
  <div class="wh-full" style="height: calc(100vh - 50px - 40px - 32px);">
    <n-split direction="horizontal" :default-size="0.2" :min="0.1" :max="0.4">
      <template #1>
        <n-card content-style="padding: 0; overflow-y: auto;" class="h-full">
          <n-list hoverable clickable>
            <n-list-item
              v-for="g in groups"
              :key="g.id"
              @click="selectGroup(g.id)"
              :style="{ background: selectedGroupId === g.id ? 'rgba(100,108,255,0.08)' : '' }"
            >
              <span
                class="inline-block w-8px h-8px rounded-full mr-2"
                :style="{ background: g.color }"
              />
              {{ g.name }}
            </n-list-item>
          </n-list>
        </n-card>
      </template>

      <template #2>
        <n-split direction="horizontal" :default-size="0.3">
          <template #1>
            <n-card content-style="padding: 0; overflow-y: auto;" class="h-full">
              <n-empty v-if="!accounts.length" description="暂无账号" class="mt-12" />
              <n-list v-else hoverable clickable>
                <n-list-item
                  v-for="a in accounts"
                  :key="a.id"
                  @click="selectedAccountId = a.id"
                  :style="{ background: selectedAccountId === a.id ? 'rgba(100,108,255,0.08)' : '' }"
                >
                  <div class="text-13px">{{ a.email }}</div>
                  <div class="text-11px op-60">{{ a.account_type }}</div>
                </n-list-item>
              </n-list>
            </n-card>
          </template>
          <template #2>
            <n-card content-style="padding: 0;" class="h-full">
              <n-empty
                description="选择左侧账号以查看邮件"
                class="mt-12"
              />
            </n-card>
          </template>
        </n-split>
      </template>
    </n-split>
  </div>
</template>
