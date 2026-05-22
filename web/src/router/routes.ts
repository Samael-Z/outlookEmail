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
        path: 'forwarding',
        name: 'forwarding',
        component: () => import('@/views/forwarding/index.vue'),
        meta: { title: 'menu.forwarding', icon: 'tabler:send' }
      },
      {
        path: 'forwarding/history',
        name: 'forwarding-history',
        component: () => import('@/views/forwarding/history.vue'),
        meta: { title: 'menu.forwardingHistory', icon: 'tabler:history' }
      },
      {
        path: 'webdav',
        name: 'webdav',
        component: () => import('@/views/webdav/index.vue'),
        meta: { title: 'menu.webdav', icon: 'tabler:cloud-upload' }
      },
      {
        path: 'tags',
        name: 'tags',
        component: () => import('@/views/tags/index.vue'),
        meta: { title: 'menu.tags', icon: 'tabler:tags' }
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('@/views/projects/index.vue'),
        meta: { title: 'menu.projects', icon: 'tabler:briefcase' }
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
