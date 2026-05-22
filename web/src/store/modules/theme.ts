import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export const useThemeStore = defineStore('theme', () => {
  const darkMode = useStorage('outlook-email:dark-mode', false);
  const primaryColor = useStorage('outlook-email:primary-color', '#646cff');

  function toggleDark() {
    darkMode.value = !darkMode.value;
  }

  return { darkMode, primaryColor, toggleDark };
});
