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
    return `${cleanBase}${staticPath}`.replaceAll(/([^:]\/)\/+/g, "$1");
  }

  // ОБРОБКА API ЗАПИТІВ
  const API_PREFIX = "/api/v1";
  
  if (!path.includes(API_PREFIX)) {
    path = `${API_PREFIX}${path}`;
  }

  let fullUrl = `${cleanBase}${path}`.replaceAll(/([^:]\/)\/+/g, "$1");

  // ВАЖЛИВО: Додаємо слеш ПЕРЕД query параметрами
  if (fullUrl.includes("?")) {
    // Є query параметри - додаємо слеш перед ними
    const [urlPath, queryString] = fullUrl.split("?");
    if (!urlPath.endsWith("/")) {
      fullUrl = `${urlPath}/?${queryString}`;
    }
    // Немає query параметрів - додаємо слеш в кінець
  } else if (!fullUrl.endsWith("/")) {
      fullUrl += "/";
    
    
    
  }

  return fullUrl;
};