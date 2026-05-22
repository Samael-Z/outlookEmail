import { createApp } from 'vue';
import { createPinia } from 'pinia';
import 'virtual:uno.css';
import '@/styles/index.scss';
import App from './App.vue';
import { setupRouter } from './router';
import { setupI18n } from './locales';

async function bootstrap() {
  const app = createApp(App);
  app.use(createPinia());
  setupI18n(app);
  await setupRouter(app);
  app.mount('#app');
}

bootstrap();
