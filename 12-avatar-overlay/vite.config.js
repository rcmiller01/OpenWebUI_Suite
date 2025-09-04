import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';

export default defineConfig({
  root: 'web',
  server: {
    port: 5173,
    host: 'localhost',
    open: true
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11']
    })
  ],
  optimizeDeps: {
    include: ['@rive-app/canvas', 'reconnecting-websocket']
  }
});
