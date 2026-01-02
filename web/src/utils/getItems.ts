import axios from "axios";
import { SetAvailablePagesCount } from "../redux/actions/PageActions";
import { RootStore } from "../redux/Stores/RootStore";
import { encodeData } from "./encodeData";
import { generateUrl } from "./generateUrl";

export const getItems = async (
    url_part: string,
    data?: any,
    usePagination?: boolean,
    options?: any
) => {
    let validUrl = generateUrl(url_part);

    if (data) {
        const filters = encodeData(data);

        validUrl += `${
            validUrl.includes("?") ? "&" : "?"
        }encoded_filters=${filters}`;
    }

    if (usePagination) {
        const currentState = RootStore.getState();

        validUrl += `${validUrl.includes("?") ? "&" : "?"}page=${
            currentState.PageReducer.currentPage
        }`;
    }

    return await axios
        .get(validUrl, options)
        .then((res) => {
            if (res.data.pages_count && usePagination) {
                RootStore.dispatch(
                    SetAvailablePagesCount(res.data.pages_count)
                );
            }

            return res.data?.results || res.data;
        })
        .catch(() => []);
};
