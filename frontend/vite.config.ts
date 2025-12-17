import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react(), tailwindcss()],
    
    // Base path for assets - use '/' for S3/CloudFront deployment
    base: '/',
    
    // Build configuration for S3 deployment
    build: {
      // Output directory
      outDir: 'dist',
      
      // Generate source maps for debugging (disable in production if needed)
      sourcemap: mode !== 'production',
      
      // Chunk size warning limit (in kB)
      chunkSizeWarningLimit: 500,
      
      // Rollup options for code splitting
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            // Vendor chunk for React and related libraries
            vendor: ['react', 'react-dom', 'react-router-dom'],
            // Markdown rendering chunk
            markdown: ['marked'],
          },
          // Asset file naming with hash for cache busting
          assetFileNames: 'assets/[name]-[hash][extname]',
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
        },
      },
    },
    
    // Define environment variables to expose to the client
    define: {
      // Ensure VITE_API_URL is available at build time
      __API_URL__: JSON.stringify(env.VITE_API_URL || '/api'),
    },
    
    // Preview server configuration (for local testing of production build)
    preview: {
      port: 4173,
      strictPort: true,
    },
    
    // Development server configuration
    server: {
      port: 5173,
      strictPort: true,
      // Proxy API requests to backend during development
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
