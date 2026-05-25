<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
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
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="bg-shapes">
        <div class="shape shape-1" />
        <div class="shape shape-2" />
        <div class="shape shape-3" />
        <div class="shape shape-4" />
      </div>

      <div class="brand-content">
        <div class="brand-header">
          <div class="brand-logo">
            <Icon icon="tabler:mail-bolt" />
          </div>
          <div class="brand-name">OutlookEmail</div>
        </div>

        <div class="brand-tagline">
          <h1>统一收件 · 随机生成 · 批量管理</h1>
          <p>
            把 Outlook OAuth、IMAP、临时邮箱、内网 EML 邮件汇总到一个界面，
            搭配 Token 自动刷新与 WebDAV 备份，一处管理几十上百个收件箱。
          </p>
        </div>

        <ul class="feature-list">
          <li>
            <Icon icon="tabler:circle-check-filled" class="check" />
            <div>
              <div class="feat-title">多链路读取</div>
              <div class="feat-desc">Outlook Graph、IMAP、临时邮箱、内网 EML 自动回退</div>
            </div>
          </li>
          <li>
            <Icon icon="tabler:circle-check-filled" class="check" />
            <div>
              <div class="feat-title">随机一次性邮箱</div>
              <div class="feat-desc">🎲 一键生成 @cs2jp / @jokerque 邮箱，收码即用即弃</div>
            </div>
          </li>
          <li>
            <Icon icon="tabler:circle-check-filled" class="check" />
            <div>
              <div class="feat-title">Token 流式刷新</div>
              <div class="feat-desc">SSE 实时进度 + 失败重试 + 定时调度</div>
            </div>
          </li>
          <li>
            <Icon icon="tabler:circle-check-filled" class="check" />
            <div>
              <div class="feat-title">XSS / CSRF / 加密</div>
              <div class="feat-desc">DOMPurify + Double-Submit Token + Fernet 字段加密</div>
            </div>
          </li>
        </ul>

        <div class="brand-footer">
          <Icon icon="tabler:shield-check" class="text-success" />
          <span>所有凭据在数据库中均经 Fernet 加密存储</span>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-panel">
      <div class="form-card">
        <div class="form-header">
          <div class="mobile-logo">
            <Icon icon="tabler:mail-bolt" />
          </div>
          <h2>欢迎回来</h2>
          <p>使用管理员密码登录系统</p>
        </div>

        <n-form @submit.prevent="handleLogin">
          <n-form-item :label="t('login.password')" :show-feedback="false" class="mb-5">
            <n-input
              v-model:value="password"
              type="password"
              size="large"
              show-password-on="click"
              :placeholder="t('login.placeholder')"
              autofocus
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <Icon icon="tabler:lock" />
              </template>
            </n-input>
          </n-form-item>
          <n-button
            type="primary"
            size="large"
            block
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            <span v-if="!loading" class="flex-y-center">
              <Icon icon="tabler:login-2" />
              <span class="ml-2">{{ t('login.submit') }}</span>
            </span>
          </n-button>
        </n-form>

        <div class="form-hint">
          <Icon icon="tabler:info-circle" />
          <span>
            默认密码 <code>admin123</code> —
            登录后请立即到 <b>设置 → 安全</b> 修改为强密码（≥ 8 位）
          </span>
        </div>

        <div class="form-divider">
          <span>支持的邮件链路</span>
        </div>

        <div class="provider-row">
          <div class="provider" title="Outlook / Hotmail">
            <Icon icon="tabler:brand-windows" style="color: #0078d4" />
          </div>
          <div class="provider" title="Gmail">
            <Icon icon="tabler:brand-google" style="color: #ea4335" />
          </div>
          <div class="provider" title="QQ 邮箱">
            <Icon icon="tabler:brand-tencent-qq" style="color: #1296db" />
          </div>
          <div class="provider" title="163 / 126">
            <Icon icon="tabler:mail" style="color: #d22f2f" />
          </div>
          <div class="provider" title="Yahoo">
            <Icon icon="tabler:brand-yahoo" style="color: #7e1fff" />
          </div>
          <div class="provider" title="内网 EML">
            <Icon icon="tabler:building-lighthouse" style="color: #f0a020" />
          </div>
        </div>
      </div>

      <div class="page-footer">
        <span>© OutlookEmail · MIT License</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: flex;
  background: #f5f7fa;
  overflow: hidden;
}

:global(html.dark) .login-page,
.login-page :deep(.dark) {
  background: #101014;
}

/* ============ 左侧品牌区 ============ */
.brand-panel {
  flex: 1.1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 55%, #f5576c 100%);
  color: white;
  overflow: hidden;
  padding: 56px;
}

.bg-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
  animation: float 18s ease-in-out infinite;
}
.shape-1 {
  width: 360px;
  height: 360px;
  background: #f093fb;
  top: -100px;
  left: -80px;
  animation-delay: 0s;
}
.shape-2 {
  width: 280px;
  height: 280px;
  background: #4facfe;
  bottom: -60px;
  right: -40px;
  animation-delay: -4s;
}
.shape-3 {
  width: 220px;
  height: 220px;
  background: #fcb69f;
  top: 40%;
  right: 8%;
  animation-delay: -8s;
}
.shape-4 {
  width: 180px;
  height: 180px;
  background: #a18cd1;
  bottom: 20%;
  left: 15%;
  animation-delay: -12s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.08); }
  66% { transform: translate(-20px, 30px) scale(0.95); }
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 540px;
  width: 100%;
}

.brand-header {
  display: flex;
  align-items: center;
  margin-bottom: 64px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.brand-name {
  margin-left: 14px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.brand-tagline h1 {
  font-size: 38px;
  font-weight: 800;
  line-height: 1.25;
  margin: 0 0 16px;
  letter-spacing: -0.3px;
}

.brand-tagline p {
  font-size: 15px;
  line-height: 1.7;
  opacity: 0.92;
  margin: 0 0 40px;
  max-width: 480px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 48px;
}

.feature-list li {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
}

.feature-list .check {
  font-size: 22px;
  margin-right: 12px;
  margin-top: 1px;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.9);
}

.feat-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 2px;
}

.feat-desc {
  font-size: 13px;
  opacity: 0.8;
  line-height: 1.5;
}

.brand-footer {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  font-size: 13px;
}

.brand-footer .iconify {
  margin-right: 8px;
  font-size: 18px;
}

/* ============ 右侧表单区 ============ */
.form-panel {
  flex: 0.9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px 48px;
  background: #ffffff;
  position: relative;
}

:global(html.dark) .form-panel {
  background: #18181c;
}

.form-card {
  width: 100%;
  max-width: 420px;
}

.form-header {
  margin-bottom: 36px;
}

.mobile-logo {
  display: none;
  width: 56px;
  height: 56px;
  margin-bottom: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 30px;
  align-items: center;
  justify-content: center;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: -0.2px;
}

.form-header p {
  font-size: 14px;
  opacity: 0.6;
  margin: 0;
}

.login-btn {
  height: 48px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: 0.4px;
}

.form-hint {
  display: flex;
  align-items: flex-start;
  margin-top: 20px;
  padding: 12px 14px;
  background: rgba(100, 108, 255, 0.08);
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.6;
  color: #555;
}

:global(html.dark) .form-hint {
  background: rgba(100, 108, 255, 0.16);
  color: #bbb;
}

.form-hint .iconify {
  margin-right: 8px;
  margin-top: 1px;
  flex-shrink: 0;
  font-size: 16px;
  color: #646cff;
}

.form-hint code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

:global(html.dark) .form-hint code {
  background: rgba(255, 255, 255, 0.1);
}

.form-divider {
  display: flex;
  align-items: center;
  margin: 32px 0 16px;
  color: #999;
  font-size: 12px;
}

.form-divider::before,
.form-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}

:global(html.dark) .form-divider::before,
:global(html.dark) .form-divider::after {
  background: #2c2c32;
}

.form-divider span {
  padding: 0 14px;
}

.provider-row {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.provider {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  transition: transform 0.15s ease, background 0.15s ease;
  cursor: default;
}

.provider:hover {
  transform: translateY(-2px);
  background: rgba(100, 108, 255, 0.08);
}

:global(html.dark) .provider {
  background: #232328;
}

.page-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  opacity: 0.4;
}

/* ============ 响应式 ============ */
@media (max-width: 980px) {
  .brand-panel {
    display: none;
  }
  .mobile-logo {
    display: flex !important;
  }
  .form-panel {
    flex: 1;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  .form-card {
    background: white;
    padding: 36px 28px;
    border-radius: 16px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.15);
  }
  :global(html.dark) .form-card {
    background: #18181c;
  }
  .page-footer {
    color: white;
    opacity: 0.7;
  }
}
</style>
