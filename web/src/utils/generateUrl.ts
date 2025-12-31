export const generateUrl = (targetUrl: string): string => {
  // 1. Базовий домен бекенду
  const base = process.env.REACT_APP_BACKEND_LINK || "https://reliktarte-production.up.railway.app";
  
  // 2. Визначаємо оточення
  const isLocal = window.location.hostname === "localhost";
  
  // Очищаємо базу від слешів в кінці та виправляємо протокол
  let finalBase = base.replace(/\/+$/, "");
  if (isLocal) {
    finalBase = finalBase.replace(/^https:\/\//, "http://");
  } else {
    finalBase = finalBase.replace(/^http:\/\//, "https://");
  }

  // 3. ЛОГІКА ДЛЯ ЗОБРАЖЕНЬ (STATIC)
  // Якщо шлях містить "static", ми просто клеїмо домен + шлях
  if (targetUrl.includes("static/")) {
    const cleanPath = targetUrl.startsWith("/") ? targetUrl : `/${targetUrl}`;
    return `${finalBase}${cleanPath}`;
  }

  // 4. ЛОГІКА ДЛЯ API ЗАПИТІВ
  const API_PART = "api/v1";
  let path = targetUrl.startsWith("/") ? targetUrl : `/${targetUrl}`;
  
  // Додаємо api/v1 тільки якщо його ще немає в шляху
  if (!path.includes(API_PART)) {
    path = `/${API_PART}${path}`.replace(/\/+/g, "/");
  }

  return `${finalBase}${path}`;
};