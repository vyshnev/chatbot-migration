import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    // Only scan src/tests — keeps Playwright specs in tests/ out of Vitest
    include: ['src/tests/**/*.{test,spec}.{js,jsx,ts,tsx}'],
  }
})
