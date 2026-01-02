export const generateUrl = (targetUrl: string): string => {
  if (!targetUrl) return "";

  // ЗАВЖДИ використовуємо https для Railway, навіть з localhost
  const base = "https://reliktarte-production.up.railway.app";
  
  // 1. Очищуємо базу від слешів у кінці
  const finalBase = base.replace(/\/+$/, "");

  // 2. Формуємо початковий шлях
  let path = targetUrl.startsWith("/") ? targetUrl : `/${targetUrl}`;

  // 3. Обробка статичних файлів (картинок)
  if (path.includes("/static/")) {
  const cleanPath = path.replace("/api/v1", ""); 
    return `${finalBase}${cleanPath}`.replace(/\/+/g, "/").replace(":/", "://");
  }



  // 4. Обробка API запитів
  const API_PART = "/api/v1";
  if (!path.includes(API_PART)) {
    path = `${API_PART}${path}`;
  }

  // 5. Фінальна збірка URL
  let fullUrl = `${finalBase}${path}`.replace(/\/+/g, "/").replace(":/", "://");
    // ... далі йде логіка для API, де ми додаємо слеш
  if (!fullUrl.endsWith("/")) {
    fullUrl += "/";
}

  // 6. ВИРІШАЛЬНИЙ КРОК: додаємо слеш у кінець, якщо його немає
  // Це запобігає редиректу 307, який блокує CORS
  if (!fullUrl.endsWith("/")) {
    fullUrl += "/";
  }

  return fullUrl;
};