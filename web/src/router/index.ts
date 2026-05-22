import type { App } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { routes } from './routes';
import { useAuthStore } from '@/store/modules/auth';
import { useTabStore } from '@/store/modules/tab';

export const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();
  if (to.meta?.public || authStore.isLoggedIn) {
    next();
  } else {
    next({ path: '/login', query: { redirect: to.fullPath } });
  }
});

router.afterEach(to => {
  if (to.meta?.public) return;
  if (to.path === '/login') return;
  const tabStore = useTabStore();
  tabStore.addTab(to);
});

export async function setupRouter(app: App) {
  app.use(router);
  await router.isReady();
}
