import asyncio
import sys
import os
from pathlib import Path

# Додаємо шлях до кореня проекту
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
    print("⚠️ python-docx не встановлено. Описи .docx не будуть зчитані.")

async def import_doors(session, category_id):
    """Імпорт дверей з трирівневої структури: Клас -> Артикул -> Файли"""
    catalog_path = Path("static/catalog/door")
    if not catalog_path.exists():
        print(f"❌ Папка {catalog_path} не знайдена!")
        return 0
    
    count = 0
    # 1 рівень: Класи (напр., "Клас 2G", "Клас G+")
    for class_dir in sorted(catalog_path.iterdir()):
        if not class_dir.is_dir():
            continue
        
        class_name = class_dir.name
        print(f"\n📁 Обробка класу дверей: {class_name}")
        
        # 2 рівень: Артикули (напр., "art_14", "art_15")
        for product_dir in sorted(class_dir.iterdir()):
            if not product_dir.is_dir():
                continue
            
            product_name = product_dir.name # Артикул, напр. art_14
            
            # Пошук фото (пріоритет .webp після оптимізації)
            photo_files = []
            for ext in ['.webp', '.png', '.jpg', '.jpeg']:
                photo_files.extend(list(product_dir.glob(f"*{ext}")))
            
            if not photo_files:
                print(f"  ⚠️ {product_name}: немає фото, пропускаю")
                continue

            # Читання опису з docx
            description_details = []
            covering_text = None
            has_glass = False
            has_orientation = False
            
            desc_file = product_dir / "description.docx"
            if desc_file.exists() and DOCX_AVAILABLE:
                try:
                    doc = Document(desc_file)
                    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                    
                    if len(lines) >= 5:
                        description_details = [
                            {"label": "Артикул", "value": lines[0]},
                            {"label": "Модель", "value": lines[1]},
                            {"label": "Колір", "value": lines[2]},
                            {"label": "Виріб", "value": lines[3]},
                            {"label": "Розмір", "value": lines[4]}
                        ]
                        covering_text = lines[2]
                        
                        # Додаткові параметри (скло, сторона)
                        for extra in lines[5:]:
                            low_extra = extra.lower()
                            if any(side in low_extra for side in ['праве', 'ліве', 'правий', 'лівий']):
                                description_details.append({"label": "Сторона", "value": extra})
                                has_orientation = True
                            else:
                                description_details.append({"label": "Скло", "value": extra})
                                has_glass = True
                except Exception as e:
                    print(f"  ⚠️ {product_name}: помилка читання docx - {e}")

            # Формування JSON опису
            description = {
                "uk": f"Двері {class_name} - {product_name}",
                "details": description_details,
                "finishing": {"covering": {"text": covering_text}} if covering_text else None
            }
            
            # Унікальний SKU
            sku = f"DOOR-{class_name.replace(' ', '-')}-{product_name}".upper()
            
            # Перевірка наявності в БД
            result = await session.execute(select(Product).where(Product.sku == sku))
            product = result.scalar_one_or_none()
            
            if not product:
                product = Product(
                    name=f"{class_name} {product_name}",
                    sku=sku,
                    price=50000,
                    category_id=category_id
                )
                session.add(product)
                await session.flush()
            
            product.description = description
            product.have_glass = has_glass
            product.orientation_choice = has_orientation

            # Оновлення фото
            result = await session.execute(select(ProductPhoto).where(ProductPhoto.product_id == product.id))
            existing_paths = {p.photo for p in result.scalars().all()}
            
            for idx, f in enumerate(photo_files):
                # Формуємо шлях для вебу
                web_path = f"/static/catalog/door/{class_name}/{product_name}/{f.name}"
                if web_path not in existing_paths:
                    new_photo = ProductPhoto(
                        product_id=product.id,
                        photo=web_path,
                        is_main=(idx == 0 and not existing_paths)
                    )
                    session.add(new_photo)
            
            count += 1
            print(f"  ✅ {product_name}: оброблено")
            
    return count

async def import_mouldings(session, category_id):
    """Імпорт молдингів (дворівнева структура)"""
    catalog_path = Path("static/catalog/mouldings")
    if not catalog_path.exists(): return 0
    
    count = 0
    for product_dir in sorted(catalog_path.iterdir()):
        if not product_dir.is_dir(): continue
        
        product_name = product_dir.name
        photo_files = []
        for ext in ['.webp', '.png', '.jpg']:
            photo_files.extend(list(product_dir.glob(f"*{ext}")))
            
        if not photo_files: continue
        
        sku = f"MLD-{product_name}".upper()
        result = await session.execute(select(Product).where(Product.sku == sku))
        product = result.scalar_one_or_none()
        
        if not product:
            product = Product(name=f"Молдинг {product_name}", sku=sku, price=15000, category_id=category_id)
            session.add(product)
            await session.flush()
            
        # Фото для молдингів
        result = await session.execute(select(ProductPhoto).where(ProductPhoto.product_id == product.id))
        existing_paths = {p.photo for p in result.scalars().all()}
        
        for f in photo_files:
            web_path = f"/static/catalog/mouldings/{product_name}/{f.name}"
            if web_path not in existing_paths:
                session.add(ProductPhoto(product_id=product.id, photo=web_path, is_main=True))
        
        count += 1
        print(f"  ✅ Молдинг {product_name}: додано")
        
    return count

async def main():
    # Отримуємо URL бази даних безпосередньо як рядок
    db_url = str(settings.db.url)
    
    # Переконуємося, що використовується правильний драйвер для асинхронності
    if 'postgresql://' in db_url and 'asyncpg' not in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Отримуємо або створюємо категорії
        res = await session.execute(select(Category).where(Category.name == "Двері"))
        cat_door = res.scalar_one_or_none()
        if not cat_door:
            cat_door = Category(
                name="Двері", 
                is_glass_available=True, 
                have_orientation_choice=True
            )
            session.add(cat_door)
            await session.flush()
            
        res = await session.execute(select(Category).where(Category.name == "Молдинги"))
        cat_mld = res.scalar_one_or_none()
        if not cat_mld:
            cat_mld = Category(name="Молдинги")
            session.add(cat_mld)
            await session.flush()

        print("🚀 Початок імпорту...")
        # Виклик функцій імпорту, які ми адаптували під трирівневу структуру
        d_count = await import_doors(session, cat_door.id)
        m_count = await import_mouldings(session, cat_mld.id)
        
        await session.commit()
        print(f"\n🎉 ЗАВЕРШЕНО! Дверей оброблено: {d_count}, Молдингів: {m_count}")

if __name__ == "__main__":
    # Для Python 3.14+ та WindowsSelectorEventLoopPolicy краще використовувати стандартний запуск
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass