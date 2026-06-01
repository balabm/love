/**
 * Shared axios instance for LOVE UI.
 * Injects X-API-Key on every request so external access works.
 * Reads VITE_API_URL and VITE_API_KEY from .env at build time.
 */
import axios from "axios";

// Use explicit env var if set; otherwise auto-detect based on hostname
const isLocalhost = typeof window !== "undefined" && window.location.hostname === "localhost";
export const API = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "love-dev-key";

const api = axios.create({
  baseURL: API,
  headers: {
    "X-API-Key": API_KEY,
  },
});

export default api;
