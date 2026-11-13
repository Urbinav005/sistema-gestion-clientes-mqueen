// Configuración de Vite: plugin de React y puerto fijo 5173,
// el mismo que el backend autoriza en CORS.
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Si el puerto está ocupado, falla en vez de usar otro (CORS solo acepta 5173)
    strictPort: true,
  },
})
