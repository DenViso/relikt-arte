// src/utils/generateUrl.ts

export const generateUrl = (targetUrl: string): string => {
  // Беремо бекенд з env, замінюємо http на https, або ставимо дефолт
  const BACKEND =
    process.env.REACT_APP_BACKEND_LINK?.replace(/^http:\/\//, "https://") ??
    "https://reliktarte-production.up.railway.app";

  // Частина шляху API
  const API_PART = "api/v1";

  // Перевірка, чи закінчується домен на /
  const needsSlash = !BACKEND.endsWith("/");

  // Формуємо повний шлях
  let path = "";
  if (!targetUrl.includes(API_PART)) {
    path += `/${API_PART}`;
  }
  if (!targetUrl.startsWith("/")) {
    path += "/";
  }

  path += targetUrl;

  // Замінюємо подвійні слеші на один
  const finalPath = path.replace(/\/{2,}/g, "/");

  // Формуємо фінальний URL
  const url = `${BACKEND}${finalPath}`;

  console.log("🔍 BACKEND:", BACKEND);
  console.log("🔍 Generated URL:", url);

  return url;
};
