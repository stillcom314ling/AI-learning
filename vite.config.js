import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'launcher/index.html'),
        'sdf-playground': resolve(__dirname, 'prototypes/sdf-playground/index.html'),
        'match3-pad': resolve(__dirname, 'prototypes/match3-pad/index.html'),
      },
    },
  },
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
});
