// src/utils/generateUrl.ts

export const generateUrl = (targetUrl: string): string => {
  // Беремо бекенд з env або дефолт
  let BACKEND =
    process.env.REACT_APP_BACKEND_LINK ??
    "https://reliktarte-production.up.railway.app";

  // Якщо бекенд не починається з http, додаємо https
  if (!/^https?:\/\//.test(BACKEND)) {
    BACKEND = "https://" + BACKEND;
  }

  // Якщо локально (localhost), дозволяємо http
  if (window.location.hostname === "localhost") {
    BACKEND = BACKEND.replace(/^https:\/\//, "http://");
  } else {
    // На проді — завжди https
    BACKEND = BACKEND.replace(/^http:\/\//, "https://");
  }

  const API_PART = "api/v1";

  // Формуємо шлях
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

  const url = `${BACKEND}${finalPath}`;

  console.log("🔍 BACKEND:", BACKEND);
  console.log("🔍 Generated URL:", url);

  return url;
};
