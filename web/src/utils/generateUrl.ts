export const generateUrl = (targetUrl: string) => {
  const part = "api/v1";

  const isDomainNotEndsWithSlash = !(
   const BACKEND =
  process.env.REACT_APP_BACKEND_LINK?.replace(/^http:\/\//, "https://") ??
  "https://reliktarte-production.up.railway.app";

  const secondPart = `${validPart}${targetUrl}`.replaceAll("//", "/");
  const url = `${
    process.env.REACT_APP_BACKEND_LINK || "https://reliktarte-production.up.railway.app"
  }${secondPart}`;
console.log("🔍 ALL ENV:", process.env);
console.log("🔍 BACKEND_LINK:", process.env.REACT_APP_BACKEND_LINK);
  return url;
};