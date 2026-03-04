import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const envDir = '..';
  const rootEnv = loadEnv(mode, envDir, '');

  const googleClientId = rootEnv.VITE_GOOGLE_CLIENT_ID || rootEnv.APP_GOOGLE_CLIENT_ID || '';

  return {
    envDir,
    define: {
      'import.meta.env.VITE_GOOGLE_CLIENT_ID': JSON.stringify(googleClientId),
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@pages': '/src/pages',
        '@services': '/src/services',
        '@hooks': '/src/hooks',
        '@contexts': '/src/contexts',
        '@types': '/src/types',
        '@utils': '/src/utils',
        '@styles': '/src/styles',
      },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  };
});
