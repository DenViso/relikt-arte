export type ProductPhotoType = {
    id: number;
    product_id: number;
    photo: string;
    is_main: boolean;
    dependency: string;
    with_glass: any;
    orientation: any;
    type_of_platband: any;
    color_id: any;
    size_id: any;
};

// export type ProductType = {

//     id: number;
//     sku: string;
//     name: string;
//     price: number;
//     photo: string;
//     description?: {
//         construction?: {
//             main_text?: string;
//             additional_text?: string;
//         };
//         advantages?: string[];
//         finishing?: {
//             covering?: {
//                 text?: string;
//                 advantages?: string[];
//             };
//         };
//         text?: string;
//     };
//     have_glass?: boolean;
//     orientation_choice?: boolean;
//     material_choice?: boolean;
//     type_of_platband_choice?: boolean;
//     category_id: number;
//     covering_id: number;
//     photos: ProductPhotoType[];
// };
export type ProductDetailType = {
  value: string;  // Тільки значення, без label
};

export type ProductType = {
  id: number;
  sku: string;
  name: string;
  price: number;
  category_id?: number;
  photos?: ProductPhotoType[];
  have_glass?: boolean;
  orientation_choice?: boolean;
  material_choice?: boolean;
  type_of_platband_choice?: boolean;
  description?: {
    text?: string;
    details?: ProductDetailType[];  // ← ОНОВЛЕНО
    construction?: {
      main_text?: string;
      additional_text?: string;
    };
    advantages?: string[];
    finishing?: {
      covering?: {
        text?: string;
        advantages?: string[];
      };
    };
  };
};