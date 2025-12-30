import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.product.models import Product, Category, ProductPhoto
from src.core.config import settings

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️  python-docx не встановлено. Опис не буде імпортовано.")

async def import_catalog():
    """Імпорт товарів з каталогу"""
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    engine = create_async_engine(str(settings.db.url))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Шлях до каталогу
    catalog_path = Path("static/catalog/door")
    
    if not catalog_path.exists():
        print(f"❌ Папка {catalog_path} не знайдена!")
        print(f"   Спочатку виконай: xcopy /E /I \"..\\resource\\Katalog\\door\" \"static\\catalog\\door\"")
        return
    
    async with async_session() as session:
        # Отримай або створи категорію "Двері"
        result = await session.execute(
            select(Category).where(Category.name == "Двері")
        )
        category = result.scalar_one_or_none()
        
        if not category:
            category = Category(
                name="Двері",
                is_glass_available=False,
                have_material_choice=False,
                have_orientation_choice=False,
                have_type_of_platband_choice=False
            )
            session.add(category)
            await session.flush()
        
        category_id = category.id
        count = 0
        
        # Пройдись по класах
        for class_dir in sorted(catalog_path.iterdir()):
            if not class_dir.is_dir():
                continue
            
            class_name = class_dir.name
            print(f"\n📁 Обробка класу: {class_name}")
            
            # Пройдись по товарах
            for product_dir in sorted(class_dir.iterdir()):
                if not product_dir.is_dir():
                    continue
                
                product_name = product_dir.name
                
                # Знайди ВСІ фото
                photo_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    photo_files.extend(list(product_dir.glob(f"*{ext}")))
                
                if not photo_files:
                    print(f"  ⚠️  {product_name}: немає фото, пропускаю")
                    continue
                
                # Читай опис з docx
                description_details = []
                covering_text = None
                has_glass = False
                has_orientation = False
                
                desc_file = product_dir / "description.docx"
                if desc_file.exists() and DOCX_AVAILABLE:
                    try:
                        doc = Document(desc_file)
                        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                        
                        # Структура файлу:
                        # lines[0] = артикул
                        # lines[1] = модель
                        # lines[2] = колір
                        # lines[3] = виріб
                        # lines[4] = розмір
                        # lines[5] = сторона відкривання (опціонально)
                        # lines[6] = скло (опціонально)
                        
                        if lines and len(lines) >= 5:
                            article = lines[0]       # Артикул
                            model = lines[1]         # Модель
                            color = lines[2]         # Колір
                            product_type = lines[3]  # Виріб
                            size = lines[4]          # Розмір
                            
                            description_details = [
                                {"label": "Артикул", "value": article},
                                {"label": "Модель", "value": model},
                                {"label": "Колір", "value": color},
                                {"label": "Виріб", "value": product_type},
                                {"label": "Розмір виробу", "value": size}
                            ]
                            
                            covering_text = color  # Колір іде в covering.text
                            
                            # Перевір сторону відкривання (6-й рядок = lines[5])
                            if len(lines) > 5:
                                orientation_value = lines[5].strip().lower()
                                if orientation_value in ['праве', 'ліве', 'правий', 'лівий', 'правое', 'левое']:
                                    description_details.append({"label": "Сторона відкривання", "value": lines[5]})
                                    has_orientation = True
                                    
                                    # Перевір скло (7-й рядок = lines[6])
                                    if len(lines) > 6:
                                        description_details.append({"label": "Скло", "value": lines[6]})
                                        has_glass = True
                                else:
                                    # Якщо 6-й рядок не сторона, то це скло
                                    description_details.append({"label": "Скло", "value": lines[5]})
                                    has_glass = True
                                    
                    except Exception as e:
                        print(f"  ⚠️  {product_name}: помилка читання опису - {e}")
                
                # Створи description з правильною структурою
                description = {
                    "uk": f"Двері {class_name} - {product_name}",
                    "construction": None,
                    "advantages": [],
                    "finishing": {
                        "covering": {
                            "text": covering_text,
                            "advantages": []
                        }
                    } if covering_text else None,
                    "text": None,
                    "details": description_details
                }
                
                # SKU та ціна
                sku = f"DOOR-{class_name.replace(' ', '-')}-{product_name}"
                price = 50000  # 500 грн у копійках
                
                # Перевір чи існує
                result = await session.execute(
                    select(Product).where(Product.sku == sku)
                )
                existing_product = result.scalar_one_or_none()
                
                if existing_product:
                    # Оновіть опис та boolean поля
                    existing_product.description = description
                    existing_product.have_glass = has_glass
                    existing_product.orientation_choice = has_orientation
                    
                    # Перевір існуючі фото
                    result = await session.execute(
                        select(ProductPhoto).where(ProductPhoto.product_id == existing_product.id)
                    )
                    existing_photos = result.scalars().all()
                    existing_photo_paths = {p.photo for p in existing_photos}
                    
                    # Додай нові фото
                    new_photos_count = 0
                    for idx, photo_file in enumerate(photo_files):
                        photo_path = f"/static/catalog/door/{class_name}/{product_name}/{photo_file.name}"
                        
                        if photo_path not in existing_photo_paths:
                            photo = ProductPhoto(
                                product_id=existing_product.id,
                                photo=photo_path,
                                is_main=(idx == 0 and len(existing_photos) == 0),
                                dependency=None,
                                with_glass=False,
                                orientation=None,
                                type_of_platband=None,
                                color_id=None,
                                size_id=None
                            )
                            session.add(photo)
                            new_photos_count += 1
                    
                    if new_photos_count > 0:
                        print(f"  📸 {product_name}: додано {new_photos_count} фото, оновлено опис")
                    else:
                        print(f"  ✏️  {product_name}: оновлено опис")
                    continue
                
                # Створи товар
                product = Product(
                    name=f"{class_name} {product_name}",
                    sku=sku,
                    price=price,
                    description=description,
                    category_id=category_id,
                    have_glass=has_glass,
                    material_choice=False,
                    type_of_platband_choice=False,
                    orientation_choice=has_orientation
                )
                
                session.add(product)
                await session.flush()
                
                # Створи ВСІ фото
                for idx, photo_file in enumerate(photo_files):
                    photo_path = f"/static/catalog/door/{class_name}/{product_name}/{photo_file.name}"
                    
                    photo = ProductPhoto(
                        product_id=product.id,
                        photo=photo_path,
                        is_main=(idx == 0),
                        dependency=None,
                        with_glass=False,
                        orientation=None,
                        type_of_platband=None,
                        color_id=None,
                        size_id=None
                    )
                    session.add(photo)
                
                count += 1
                print(f"  ✅ {product_name}: додано з {len(photo_files)} фото")
        
        await session.commit()
        print(f"\n🎉 Імпорт завершено! Додано {count} нових товарів")

if __name__ == "__main__":
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(import_catalog())