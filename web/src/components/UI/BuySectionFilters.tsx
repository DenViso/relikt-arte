import { useEffect, useRef, useState, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { filtersData } from "../../data/filters";
import {
    RANGE,
    VALUE_LESS_THAN_OR_EQUALS,
    VALUE_MORE_THAN_OR_EQUALS,
} from "../../data/operations";
import { SetFilters } from "../../redux/actions/FiltersActions";
import "../../styles/components/UI/BuySectionFilters.scss";
import { getItems } from "../../utils/getItems";
import { handleInputByAllowedSymbols } from "../../utils/handleInputByAllowedSymbols";
import Filter from "./Filter";

const BuySectionFilters = () => {
    const [minPrice, setMinPrice] = useState("");
    const [maxPrice, setMaxPrice] = useState("");
    const [filtersOptions, setFiltersOptions] = useState<any>({});
    const [currentFilters, setCurrentFilters] = useState<any>([]);
    const [glassChoiceAvailable, setGlassChoiceAvailable] = useState(false);
    
    const sidebarRef = useRef<HTMLDivElement>(null);
    const dispatch = useDispatch();
    const currentWidth = useSelector((state: any) => state.ScreenPropertiesReducer.width);

    // Функція перевірки наявності скла в обраних категоріях
    const checkGlassAvailability = useCallback(() => {
        const selectedCategories = currentFilters.filter((f: any) => f.field === "category_id");
        const hasGlass = selectedCategories.some((cat: any) => cat?.originalObject?.is_glass_available);
        setGlassChoiceAvailable(hasGlass);
    }, [currentFilters]);

    // Завантаження опцій для фільтрів (виконується один раз)
    useEffect(() => {
        const loadAllOptions = async () => {
            const newOptions: any = {};
            
            for (const item of filtersData) {
                if (item.optionsUrl) {
                    try {
                        const data = await getItems(item.optionsUrl);
                        if (data && Array.isArray(data)) {
                            newOptions[item.field] = data.map((opt: any) => ({
                                name: opt[item.targetKey || "name"],
                                value: opt.id,
                                field: item.field,
                                originalObject: opt,
                            }));
                        }
                    } catch (err) {
                        console.error(`Error loading options for ${item.field}:`, err);
                    }
                } else if (item.options) {
                    newOptions[item.field] = item.options.map((opt: any) => ({
                        ...opt,
                        field: item.field,
                        originalObject: opt,
                    }));
                }
            }
            setFiltersOptions(newOptions);
        };

        loadAllOptions();
    }, []);

    // Синхронізація фільтрів з Redux
    useEffect(() => {
        // Видаляємо дублікати та невалідні значення
        const validFilters = currentFilters.filter((f: any) => f && Object.keys(f).length > 0);
        
        // Перевірка доступності скла
        checkGlassAvailability();

        if (validFilters.length > 0) {
            dispatch(SetFilters(validFilters));
        }
    }, [currentFilters, dispatch, checkGlassAvailability]);

    // Обробка зміни ціни
    useEffect(() => {
        const cMin = minPrice ? Number(minPrice) : null;
        const cMax = maxPrice ? Number(maxPrice) : null;

        setCurrentFilters((prev: any) => {
            // Видаляємо старий фільтр ціни
            const otherFilters = prev.filter((f: any) => f.field !== "price");
            
            if (!cMin && !cMax) return otherFilters;

            // Створюємо новий фільтр ціни
            const priceFilter: any = { field: "price" };
            if (cMin && cMax) {
                priceFilter.value = [cMin, cMax];
                priceFilter.operation = RANGE;
            } else if (cMin) {
                priceFilter.value = cMin;
                priceFilter.operation = VALUE_MORE_THAN_OR_EQUALS;
            } else {
                priceFilter.value = cMax;
                priceFilter.operation = VALUE_LESS_THAN_OR_EQUALS;
            }

            return [...otherFilters, priceFilter];
        });
    }, [minPrice, maxPrice]);

    const toggleSidebar = () => {
        sidebarRef.current?.classList.toggle("active");
    };

    return (
        <>
            {currentWidth <= 900 && (
                <div className="filters-button" onClick={toggleSidebar}>
                    <svg width="14" height="6" viewBox="0 0 14 6" fill="none">
                        <path d="M12.833 5.33334L6.99967 0.666676L1.16634 5.33334" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </div>
            )}

            <div className="filters-container" ref={sidebarRef}>
                <p className="upper pre-small black bold">фільтр</p>
                
                <div className="filters-price">
                    <p className="upper small black">ціна</p>
                    <div className="filters-price-inputs">
                        <input
                            type="text"
                            value={minPrice}
                            onChange={(e) => handleInputByAllowedSymbols({ event: e, set: setMinPrice })}
                            placeholder="ВІД"
                        />
                        <span></span>
                        <input
                            type="text"
                            value={maxPrice}
                            onChange={(e) => handleInputByAllowedSymbols({ event: e, set: setMaxPrice })}
                            placeholder="ДО"
                        />
                    </div>
                </div>

                {filtersData.map((filter: any) => {
                    // Логіка відображення фільтра скла
                    if (filter.field === "have_glass" && !glassChoiceAvailable) {
                        return null;
                    }

                    return (
                        <Filter
                            key={filter.field} // Використовуємо унікальне ім'я поля як ключ
                            label={filter.name}
                            options={filtersOptions[filter.field] || filter.options || []}
                            filters={currentFilters}
                            handleFilter={setCurrentFilters}
                            type={filter.field === "have_glass" ? "radio" : undefined}
                        />
                    );
                })}
            </div>
        </>
    );
};

export default BuySectionFilters;