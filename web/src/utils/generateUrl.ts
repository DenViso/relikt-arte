export const generateUrl = (targetUrl: string): string => {
  if (!targetUrl) return "";

  const BASE_URL = process.env.REACT_APP_API_URL || "https://reliktarte-production.up.railway.app";
  const cleanBase = BASE_URL.replace(/\/+$/, "");

  // Якщо вже повний URL - повертаємо як є
  if (targetUrl.startsWith("http")) {
    return targetUrl;
  }

  let path = targetUrl.startsWith("/") ? targetUrl : `/${targetUrl}`;

  // ОБРОБКА СТАТИЧНИХ ФАЙЛІВ
  if (path.includes("/static/") || path.startsWith("/static")) {
    const staticPath = path.replace("/api/v1", "");
    return `${cleanBase}${staticPath}`.replace(/([^:]\/)\/+/g, "$1");
  }

  // ОБРОБКА API ЗАПИТІВ
  const API_PREFIX = "/api/v1";
  
  if (!path.includes(API_PREFIX)) {
    path = `${API_PREFIX}${path}`;
  }

  let fullUrl = `${cleanBase}${path}`.replace(/([^:]\/)\/+/g, "$1");

  // ВАЖЛИВО: Додаємо слеш тільки якщо НЕМАЄ query параметрів
  if (!fullUrl.includes("?") && !fullUrl.endsWith("/")) {
    fullUrl += "/";
  }

  return fullUrl;
};