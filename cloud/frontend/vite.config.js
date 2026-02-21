import { defineConfig } from 'vite';

export default defineConfig({
  base: '/block/',
  build: {
    rollupOptions: {
      external: ['blockly'],
      output: {
        globals: {
          blockly: 'Blockly'
        }
      }
    }
  }
});
