import { createApp } from 'vue';
import './index.css';
import './App.css';
import App from './App.vue';

createApp(App).mount('#app');

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.error('No se pudo registrar el service worker', error);
    });
  });
}
