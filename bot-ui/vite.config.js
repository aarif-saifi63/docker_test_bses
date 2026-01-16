import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), tailwindcss()],
    base: "/",
    server: {
      host: "0.0.0.0",                 
      port: 5175,                     
      allowedHosts: [
        "bseschatbot.expediensolutions.in", 
        "localhost",
        "127.0.0.1",
      ],
    },
    define: {
      "import.meta.env.VITE_BASE_URL": JSON.stringify(`${env.VITE_BASE_URL}`),
      "import.meta.env.VITE_API_BASE_URL": JSON.stringify(`${env.VITE_API_BASE_URL}/api/`),
      "import.meta.env.GOOGLE_MAPS_API_KEY": JSON.stringify(env.GOOGLE_MAPS_API_KEY),
    },
  };
});
