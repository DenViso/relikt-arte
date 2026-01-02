import { useContext, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import noImage from "../../assets/no_image.png";
import { paths } from "../../router/paths";
import "../../styles/components/UI/DoorCard.scss";
import {
    ProductPhotoType,
    ProductType,
} from "../../types/productsRelatedTypes";
import { getItems } from "../../utils/getItems";
import { addCartItem } from "../../utils/handleCart";
import Button from "./Button";
import { SavedObjectsContext } from "./BuySectionProducts";
import { DEFAULT_DOOR_SIZES, CATEGORIES_WITH_DEFAULT_SIZES } from "../../constants/defaultSizes";

type DoorCardProps = {
    product: ProductType;
};

const DoorCard = ({ product }: DoorCardProps) => {
    const savedObjects = useContext(SavedObjectsContext);
    const navigate = useNavigate();
    const [tags, setTags] = useState<any>([]);
    const [values, setValues] = useState<any>([]);
    const { setValue, getValues } = useForm();

    const stopPropagation = (e: any) => e.stopPropagation();

    useEffect(() => {
        setTags([]);

        const setUpTags = async () => {
            const newTags: any = [];
            const newValues: any = [];

            if (product.have_glass) {
                newTags.push({
                    name: product.have_glass
                        ? "Скло присутнє"
                        : "Скло відсутнє",
                    field: "with_glass",
                    value: product.have_glass,
                });

                newValues.push({
                    field: "with_glass",
                    value: product.have_glass,
                });
            }

            if (product.orientation_choice) {
                newTags.push({
                    name: "Петлі зліва",
                    field: "orientation_choice",
                    value: "left",
                });

                newValues.push({
                    field: "orientation",
                    value: "left",
                });
            }

            async function processProductCategory() {
                if (!product.category_id) return;

                try {
                    // СТАТИЧНІ РОЗМІРИ: Використовуємо дефолтні для дверей
                    if (CATEGORIES_WITH_DEFAULT_SIZES.includes(product.category_id)) {
                        const defaultSize = DEFAULT_DOOR_SIZES[0]; // Перший розмір як дефолтний
                        
                        newTags.push({
                            name: defaultSize.dimensions,
                            field: "size_id",
                            value: defaultSize.id,
                        });

                        newValues.push({
                            field: "size_id",
                            value: defaultSize.id,
                        });
                        
                        return; // Виходимо, не завантажуємо з API
                    }

                    // Для інших категорій - існуюча логіка
                    let categoryObject;

                    const currentCategoryInSavedObjects =
                        savedObjects?.categories?.find(
                            (category: any) =>
                                category.id === product.category_id
                        );

                    if (!currentCategoryInSavedObjects) {
                        categoryObject = await getItems(
                            `/api/v1/product/category/${product.category_id}`
                        );

                        if (!categoryObject) {
                            console.warn("Category not found:", product.category_id);
                            return;
                        }

                        if (!savedObjects?.categories) {
                            savedObjects.categories = [];
                        }

                        savedObjects.categories.push(categoryObject);
                    } else {
                        categoryObject = currentCategoryInSavedObjects;
                    }

                    // Якщо є allowed_sizes - використовуємо їх
                    if (categoryObject?.allowed_sizes?.length > 0) {
                        const categoryAllowedSize = categoryObject.allowed_sizes[0];

                        if (categoryAllowedSize) {
                            const savedObjectSize = savedObjects?.sizes?.find(
                                (size: any) => size.id === categoryAllowedSize
                            );

                            if (savedObjectSize) {
                                newTags.push({
                                    name: savedObjectSize.dimensions,
                                    field: "size_id",
                                    value: savedObjectSize.id,
                                });

                                newValues.push({
                                    field: "size_id",
                                    value: savedObjectSize.id,
                                });
                            } else {
                                const sizeObject = await getItems(
                                    `/api/v1/product/size/${categoryAllowedSize}`
                                );

                                if (sizeObject) {
                                    newTags.push({
                                        name: sizeObject.dimensions,
                                        field: "size_id",
                                        value: sizeObject.id,
                                    });

                                    newValues.push({
                                        field: "size_id",
                                        value: sizeObject.id,
                                    });

                                    if (!savedObjects?.sizes) {
                                        savedObjects.sizes = [];
                                    }

                                    savedObjects.sizes.push(sizeObject);
                                }
                            }
                        }
                    }
                    // Якщо немає allowed_sizes - просто пропускаємо, без помилок
                } catch (error) {
                    console.error("Error processing product category:", error);
                }
            }

            await processProductCategory();

            if (product.id !== null) {
                newValues.push({
                    field: "product_id",
                    value: product.id,
                });
            }

            if (product.material_choice) {
                newValues.push({
                    field: "material",
                    value: "wood",
                });
            }

            if (product.type_of_platband_choice) {
                newValues.push({
                    field: "type_of_platband",
                    value: "default",
                });
            }

            const processColor = async () => {
                try {
                    if (savedObjects?.color) {
                        newValues.push({
                            field: "color_id",
                            value: savedObjects.color.id,
                        });
                    } else {
                        const colorResponse = await getItems(
                            "/api/v1/product/related/product_color/list?page=1&size=1"
                        );

                        const colors = Array.isArray(colorResponse) 
                            ? colorResponse 
                            : colorResponse?.items || [];

                        if (colors.length > 0 && colors[0]) {
                            savedObjects.color = colors[0];

                            newValues.push({
                                field: "color_id",
                                value: savedObjects.color.id,
                            });
                        }
                    }
                } catch (error) {
                    console.error("Error processing color:", error);
                }
            };

            await processColor();

            const processGlassColor = async () => {
                try {
                    if (savedObjects?.glassColor) {
                        newValues.push({
                            field: "glass_color_id",
                            value: savedObjects.glassColor.id,
                        });
                    } else {
                        const glassColorResponse = await getItems(
                            "/api/v1/product/related/product_glass_color/list?page=1&size=1"
                        );

                        const glassColors = Array.isArray(glassColorResponse) 
                            ? glassColorResponse 
                            : glassColorResponse?.items || [];

                        if (glassColors.length > 0 && glassColors[0]) {
                            savedObjects.glassColor = glassColors[0];

                            newValues.push({
                                field: "glass_color_id",
                                value: savedObjects.glassColor.id,
                            });
                        }
                    }
                } catch (error) {
                    console.error("Error processing glass color:", error);
                }
            };

            if (product.have_glass) {
                await processGlassColor();
            }

            setTags(newTags);
            setValues(newValues);
        };

        setUpTags();
    }, [product]);

    useEffect(() => {
        const setDefaultValues = () => {
            if (values.length > 0) {
                values.forEach((valueObj: any) => {
                    setValue(valueObj.field, valueObj.value);
                });
            }
        };

        setDefaultValues();
    }, [values, setValue]);

    const handleSubmit = async (e: any) => {
        e.stopPropagation();
        const data = getValues();

        try {
            await addCartItem(data);
            console.log("✅ Item added to cart");
        } catch (error) {
            console.error("❌ Error adding to cart:", error);
        }
    };

    return (
        <div
            className="door-card"
            onClick={() => navigate(paths.buy + `/${product.id}`)}
        >
            <p className="black small sku">Арт. {product.sku}</p>

            <div className="door-card-image-container">
                <img
                    src={
                        product.photos?.find(
                            (photo: ProductPhotoType) => photo.is_main
                        )?.photo || noImage
                    }
                    alt={`door-${product.price}-${product.id}`}
                />
            </div>

            <p className="black bold name" onClick={stopPropagation}>
                {product.name}
            </p>

            <p className="black bold price" onClick={stopPropagation}>
                {product.price} ₴
            </p>

            <div className="tags" onClick={stopPropagation}>
                {tags.length > 0 &&
                    tags.map((tag: any, index: number) => (
                        <p key={`tag[${index}]`} className="pre-small gray">
                            {tag.name}
                        </p>
                    ))}
            </div>

            <Button
                inversed={true}
                borderless={false}
                additionalClasses={["upper"]}
                onClickCallback={handleSubmit}
            >
                <svg
                    width="19"
                    height="20"
                    viewBox="0 0 28 29"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path
                        d="M12.833 24.5542C12.833 25.5207 12.0495 26.3042 11.083 26.3042C10.1165 26.3042 9.33301 25.5207 9.33301 24.5542C9.33301 23.5877 10.1165 22.8042 11.083 22.8042C12.0495 22.8042 12.833 23.5877 12.833 24.5542Z"
                        stroke="currentColor"
                    />
                    <path
                        d="M23.333 24.5542C23.333 25.5207 22.5495 26.3042 21.583 26.3042C20.6165 26.3042 19.833 25.5207 19.833 24.5542C19.833 23.5877 20.6165 22.8042 21.583 22.8042C22.5495 22.8042 23.333 23.5877 23.333 24.5542Z"
                        stroke="currentColor"
                    />
                    <path
                        d="M6.99967 5.30416H20.9997C23.577 5.30416 25.6663 7.3935 25.6663 9.97082V15.8042C25.6663 18.3815 23.577 20.4708 20.9997 20.4708H11.6663C9.08901 20.4708 6.99967 18.3815 6.99967 15.8042V5.30416ZM6.99967 5.30416C6.99967 4.01549 5.95501 2.97083 4.66634 2.97083H2.33301M6.99967 9.97082H25.083"
                        stroke="currentColor"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </svg>
                додати до кошику
            </Button>
        </div>
    );
};

export default DoorCard;