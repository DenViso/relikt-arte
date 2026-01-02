import { useEffect, useState, useCallback, useMemo } from "react";
import "../../styles/components/UI/BuySectionFilters.scss";
import { getItems } from "../../utils/getItems";
import FilterInput from "./FilterInput";

// --- Опис типів ---
export type DefaultDropDownValue = {
    defaultFieldName: string;
    defaultValue: any;
};

export type DropDownOption = {
    name: string;
    value: any;
    key?: string;
};

export type DropDownAsyncOption = {
    url?: string;
    labelKey: string;
    value?: any;
};

interface DropDownProps {
    label: string;
    options: DropDownOption[] | DropDownAsyncOption;
    field: string;
    borderless?: boolean;
    onChosen: (field: string, value: any, label?: string) => void;
    defaultValue?: DefaultDropDownValue;
    needSearch?: boolean;
    dynamicLabel?: boolean;
}

const DropDown = ({
    label, options, field, onChosen, borderless = true,
    needSearch, defaultValue, dynamicLabel,
}: DropDownProps) => {
    const [filtersOpened, setFiltersOpened] = useState(false);
    const [selectedOption, setSelectedOption] = useState<any>({});
    const [currentOptions, setCurrentOptions] = useState<DropDownOption[]>([]);
    const [searchPrompt, setSearchPrompt] = useState("");

    // Вибір опції
    const handleOptionSelect = useCallback((value: any, identifier: string, label: string) => {
        setSelectedOption({ label, value, key: identifier });
        onChosen(field, value, label);
        setFiltersOpened(false);
    }, [field, onChosen]);

    // Завантаження даних
    useEffect(() => {
        const fetchOptions = async () => {
            let newOptions: DropDownOption[] = [];
            
            if (Array.isArray(options)) {
                // Якщо передано звичайний масив
                newOptions = options.map(item => ({
                    ...item, key: item.key || `opt-${item.value}`
                }));
            } else {
                // Якщо передано об'єкт для асинхронного завантаження
                const asyncOptions = options as DropDownAsyncOption;
                
                if (Array.isArray(asyncOptions?.value)) {
                    newOptions = asyncOptions.value.map((item: any) => ({
                        name: item[asyncOptions.labelKey],
                        value: item.id,
                        key: `opt-${item.id}`,
                    }));
                } else if (asyncOptions?.url) {
                    try {
                        const data = await getItems(asyncOptions.url);
                        if (Array.isArray(data)) {
                            newOptions = data.map((item: any) => ({
                                name: item[asyncOptions.labelKey],
                                value: item.id,
                                key: `opt-${item.id}`,
                            }));
                        }
                    } catch (err) {
                        console.error("Dropdown fetch error:", err);
                    }
                }
            }

            setCurrentOptions(newOptions);

            // Встановлення значення за замовчуванням
            if (newOptions.length > 0 && !selectedOption.key) {
                const def = newOptions[0];
                handleOptionSelect(def.value, def.key!, def.name);
            }
        };

        fetchOptions();
    }, [options, handleOptionSelect]); // Додано handleOptionSelect у залежності

    // Логіка фільтрації (Пошук)
    const filteredOptions = useMemo(() => {
        if (!searchPrompt) return currentOptions;
        return currentOptions.filter(opt => 
            opt.name.toLowerCase().includes(searchPrompt.toLowerCase())
        );
    }, [searchPrompt, currentOptions]);

    return (
        <div className="filters-filter">
            <p className={`upper small filters-filter-btn ${filtersOpened ? "opened" : ""} ${borderless ? "" : "border"}`}
               onClick={() => setFiltersOpened(!filtersOpened)}>
                <span>{dynamicLabel ? selectedOption?.label || label : label}</span>
                <svg width="14" height="6" viewBox="0 0 14 6" fill="none">
                    <path d="M12.833 5.33334L6.99967 0.666676L1.16634 5.33334" stroke="currentColor"/>
                </svg>
            </p>
            
            <div className={`filters-filter-options ${filtersOpened ? "opened" : ""}`}>
                {needSearch && (
                    <input 
                        className="filters-filter-options-search" 
                        placeholder="Пошук..." 
                        value={searchPrompt}
                        onChange={e => setSearchPrompt(e.target.value)}
                    />
                )}
                <div className="filters-filter-options-list">
                    {filteredOptions.map(opt => (
                        <FilterInput 
                            type="radio" 
                            key={opt.key} 
                            label={opt.name} 
                            groupName={field}
                            isChecked={selectedOption?.key === opt.key}
                            onChange={() => handleOptionSelect(opt.value, opt.key!, opt.name)}
                        />
                    ))}
                    {filteredOptions.length === 0 && (
                        <p className="small" style={{ padding: "10px", textAlign: "center", opacity: 0.5 }}>
                            Нічого не знайдено
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DropDown;