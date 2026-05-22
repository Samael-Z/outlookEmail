import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/_builtin/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    redirect: '/home',
    component: () => import('@/layouts/default/index.vue'),
    children: [
      {
        path: 'home',
        name: 'home',
        component: () => import('@/views/home/index.vue'),
        meta: { title: 'menu.home', icon: 'tabler:dashboard' }
      },
      {
        path: 'mailbox',
        name: 'mailbox',
        component: () => import('@/views/mailbox/index.vue'),
        meta: { title: 'menu.mailbox', icon: 'tabler:mail' }
      },
      {
        path: 'accounts',
        name: 'accounts',
        component: () => import('@/views/accounts/index.vue'),
        meta: { title: 'menu.accounts', icon: 'tabler:users' }
      },
      {
        path: 'internal-eml',
        name: 'internal-eml',
        component: () => import('@/views/internal-eml/index.vue'),
        meta: { title: 'menu.internalEml', icon: 'tabler:building-lighthouse' }
      },
      {
        path: 'temp-emails',
        name: 'temp-emails',
        component: () => import('@/views/temp-emails/index.vue'),
        meta: { title: 'menu.tempEmails', icon: 'tabler:mail-fast' }
      },
      {
        path: 'refresh',
        name: 'refresh',
        component: () => import('@/views/refresh/index.vue'),
        meta: { title: 'menu.refresh', icon: 'tabler:refresh' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: 'menu.settings', icon: 'tabler:settings' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/404/index.vue'),
    meta: { public: true }
  }
];
