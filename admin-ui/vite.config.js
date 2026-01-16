import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    base: "/",
    server: {
      port: 5172,
    },
    define: {
      "import.meta.env.VITE_BASE_URL": JSON.stringify(`${env.VITE_BASE_URL}`),
      "import.meta.env.VITE_API_BASE_URL": JSON.stringify(`${env.VITE_API_BASE_URL}/api/`),
      "import.meta.env.VITE_RASA_TRAINING_BASE_URL": JSON.stringify(`${env.VITE_RASA_TRAINING_BASE_URL}`),
    },
  };
});

