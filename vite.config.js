import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'launcher/index.html'),
        'sdf-playground': resolve(__dirname, 'prototypes/sdf-playground/index.html'),
      },
    },
  },
  base: '/AI-learning/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
});
