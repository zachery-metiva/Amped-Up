import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
  },
  optimizeDeps: {
    // Leaflet uses dynamic requires that Vite's scanner misses;
    // pre-bundling explicitly ensures tiles and markers render on first load.
    include: ['leaflet', 'react-leaflet'],
  },
});
