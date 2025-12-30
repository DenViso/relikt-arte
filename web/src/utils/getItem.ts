import axios from "axios";
import { generateUrl } from "./generateUrl";

export const getItems = async (url_part: string, params?: any) => {
    let validUrl = generateUrl(url_part);

    if (params) {
        const query = new URLSearchParams(params).toString();
        if (query) {
            validUrl += `?${query}`;
        }
    }

    const response = await axios.get(validUrl);
    return response.data;
};
