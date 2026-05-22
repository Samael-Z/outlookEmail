<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import { useAuthStore } from '@/store/modules/auth';

const router = useRouter();
const route = useRoute();
const { t } = useI18n();
const authStore = useAuthStore();
const message = useMessage();

const password = ref('');
const loading = ref(false);

async function handleLogin() {
  if (!password.value) {
    message.warning(t('login.placeholder'));
    return;
  }
  loading.value = true;
  try {
    const res = await authStore.login(password.value);
    if (res.success) {
      message.success(t('login.success'));
      const redirect = (route.query.redirect as string) || '/home';
      router.push(redirect);
    } else {
      message.error(res.error || t('login.fail'));
    }
  } catch (e: any) {
    message.error(e?.response?.data?.error || t('login.fail'));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="wh-full flex-center"
    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
  >
    <n-card
      class="w-360px"
      :bordered="false"
      style="border-radius: 12px;"
    >
      <div class="text-center mb-6">
        <div class="text-22px font-bold mb-1">{{ t('app.name') }}</div>
        <div class="text-12px op-60">{{ t('app.welcome') }}</div>
      </div>
      <n-form @submit.prevent="handleLogin">
        <n-form-item :label="t('login.password')">
          <n-input
            v-model:value="password"
            type="password"
            show-password-on="click"
            :placeholder="t('login.placeholder')"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleLogin">
          {{ t('login.submit') }}
        </n-button>
      </n-form>
    </n-card>
  </div>
</template>
