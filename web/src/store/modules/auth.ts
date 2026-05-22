import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';
import { authApi } from '@/service/api/auth';

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = useStorage('outlook-email:logged-in', false);

  async function login(password: string) {
    const result = await authApi.login(password);
    if (result.success) {
      isLoggedIn.value = true;
    }
    return result;
  }

  async function logout() {
    try {
      await authApi.logout();
    } finally {
      isLoggedIn.value = false;
    }
  }

  return { isLoggedIn, login, logout };
});
