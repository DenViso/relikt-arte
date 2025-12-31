import { useEffect, useState, useCallback } from "react";
import "../../styles/components/UI/BuySectionFilters.scss";
import { getItems } from "../../utils/getItems";
import FilterInput from "./FilterInput";

// ... (типи залишаються такими ж)

const DropDown = ({
    label, options, field, onChosen, borderless = true,
    needSearch, defaultValue, dynamicLabel,
}: DropDownProps) => {
    const [filtersOpened, setFiltersOpened] = useState(false);
    const [selectedOption, setSelectedOption] = useState<any>({});
    const [currentOptions, setCurrentOptions] = useState<DropDownOption[]>([]);
    const [filteredOptions, setFilteredOptions] = useState<DropDownOption[]>([]);
    const [searchPrompt, setSearchPrompt] = useState("");

    const handleOptionSelect = useCallback((value: any, identifier: string, label: string) => {
        setSelectedOption({ label, value, key: identifier });
        onChosen(field, value, label);
        setFiltersOpened(false);
    }, [field, onChosen]);

    useEffect(() => {
        const fetchOptions = async () => {
            let newOptions: DropDownOption[] = [];
            const asyncOptions = options as DropDownAsyncOption;

            if (Array.isArray(asyncOptions?.value)) {
                newOptions = asyncOptions.value.map((item: any) => ({
                    name: item[asyncOptions.labelKey],
                    value: item.id,
                    key: `opt-${item.id}`,
                }));
            } else if (Array.isArray(options)) {
                newOptions = options.map(item => ({
                    ...item, key: item.key || `opt-${item.value}`
                }));
            } else if (asyncOptions?.url) {
                try {
                    const data = await getItems(asyncOptions.url);
                    newOptions = data.map((item: any) => ({
                        name: item[asyncOptions.labelKey],
                        value: item.id,
                        key: `opt-${item.id}`,
                    }));
                } catch (err) {
                    console.error("Dropdown fetch error:", err);
                }
            }

            setCurrentOptions(newOptions);
            setFilteredOptions(newOptions);

            // Встановлення значення за замовчуванням
            if (newOptions.length > 0 && !selectedOption.key) {
                const def = newOptions[0]; // або логіка з defaultValue
                handleOptionSelect(def.value, def.key!, def.name);
            }
        };

        fetchOptions();
    }, [options]); // Оновлюємо тільки при зміні об'єкта options

    return (
        <div className="filters-filter">
            <p className={`upper small filters-filter-btn ${filtersOpened ? "opened" : ""} ${borderless ? "" : "border"}`}
               onClick={() => setFiltersOpened(!filtersOpened)}>
                <span>{dynamicLabel ? selectedOption?.label || label : label}</span>
                <svg width="14" height="6" viewBox="0 0 14 6" fill="none"><path d="M12.833 5.33334L6.99967 0.666676L1.16634 5.33334" stroke="currentColor"/></svg>
            </p>
            <div className={`filters-filter-options ${filtersOpened ? "opened" : ""}`}>
                {needSearch && <input className="filters-filter-options-search" placeholder="Пошук" onChange={e => setSearchPrompt(e.target.value)}/>}
                {filteredOptions.map(opt => (
                    <FilterInput 
                        type="radio" key={opt.key} label={opt.name} groupName={field}
                        isChecked={selectedOption?.key === opt.key}
                        onChange={() => handleOptionSelect(opt.value, opt.key!, opt.name)}
                    />
                ))}
            </div>
        </div>
    );
};

export default DropDown;