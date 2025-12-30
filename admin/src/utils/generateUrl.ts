export const generateUrl = (targetUrl: string) => {
    const part = "api/v1";
    const backend = process.env.REACT_APP_BACKEND_LINK?.replace(/\/+$/, "") 
        || "https://reliktarte-production.up.railway.app";

    const pathPrefix = !targetUrl.includes(part) ? `/${part}` : "";
    const path = `${pathPrefix}/${targetUrl}`.replace(/\/+/g, "/");

    const url = `${backend}${path}`.replace(/([^:]\/)\/+/g, "$1"); // прибираємо подвійні слеші після домену
    return url;
};
