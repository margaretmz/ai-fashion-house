import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import svgr from 'vite-plugin-svgr';

// https://vite.dev/config/
export default defineConfig({
  build: {
        outDir: '../src/ai_fashion_house/web/static',
        emptyOutDir: true
    },
  plugins: [
      react(),
       svgr({
          exportAsDefault: true, // so you can do `import Icon from './icon.svg'`
          svgrOptions: {
            // optional svgr config
            icon: true,
          },
    }),
  ],
})
