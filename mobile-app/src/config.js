let currentApiUrl = (typeof process !== "undefined" && process.env && process.env.EXPO_PUBLIC_API_URL)
  ? process.env.EXPO_PUBLIC_API_URL
  : "https://safenex-backend-g9yf.onrender.com";

export const getApiUrl = () => currentApiUrl;

export const setApiUrl = (newUrl) => {
  if (!newUrl) return currentApiUrl;
  let formatted = newUrl.trim();
  if (!formatted.startsWith("http://") && !formatted.startsWith("https://")) {
    formatted = `http://${formatted}`;
  }
  // Trim trailing slash
  currentApiUrl = formatted.replace(/\/$/, "");
  return currentApiUrl;
};

export const API_URL = currentApiUrl;
