import asyncio
import sys
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
    print("⚠️ python-docx не встановлено.")

def extract_docx_content(file_path):
    """Зчитує весь текст з docx та намагається розпарсити його в деталі"""
    if not DOCX_AVAILABLE or not file_path.exists():
        return "Опис відсутній", [], None, False, False

    try:
        doc = Document(file_path)
        # Очищаємо порожні рядки
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        if not lines:
            return "Опис порожній", [], None, False, False

        details = []
        covering_text = None
        has_glass = False
        has_orientation = False

        # Карта заголовків для перших 5 стандартних полів
        labels = ["Артикул", "Модель", "Колір", "Виріб", "Розмір"]
        
        for i, line in enumerate(lines):
            low_line = line.lower()
            
            # Обробка перших 5 стандартних полів
            if i < len(labels):
                details.append({"label": labels[i], "value": line})
                if i == 2: # Колір
                    covering_text = line
            else:
                # Все що після 5-го рядка — додаткові характеристики
                if any(kw in low_line for kw in ['скло', 'скла', 'glass']):
                    details.append({"label": "Скло", "value": line})
                    has_glass = True
                elif any(kw in low_line for kw in ['праве', 'ліве', 'правий', 'лівий', 'сторона']):
                    details.append({"label": "Сторона", "value": line})
                    has_orientation = True
                else:
                    details.append({"label": f"Характеристика {i+1}", "value": line})

        # Основний текст опису (об'єднуємо все для пошуку/візуалізації)
        summary_text = f"Клас: {lines[1] if len(lines)>1 else ''}. {lines[0] if lines else ''}"
        
        return summary_text, details, covering_text, has_glass, has_orientation
    except Exception as e:
        print(f"  ❌ Помилка парсингу docx: {e}")
        return "Помилка читання файлу", [], None, False, False

async def import_doors(session, category_id):
    catalog_path = Path("static/catalog/door")
    if not catalog_path.exists(): return 0
    
    count = 0
    for class_dir in sorted(catalog_path.iterdir()):
        if not class_dir.is_dir(): continue
        
        class_name = class_dir.name
        for product_dir in sorted(class_dir.iterdir()):
            if not product_dir.is_dir(): continue
            
            product_folder_name = product_dir.name
            
            # 1. Збір абсолютно ВСІХ фото з папки
            photo_extensions = ['*.webp', '*.png', '*.jpg', '*.jpeg', '*.WEBP', '*.PNG', '*.JPG']
            all_photos = []
            for ext in photo_extensions:
                all_photos.extend(list(product_dir.glob(ext)))
            
            # Видаляємо дублікати за назвою файлу (якщо glob знайде одне й те саме)
            all_photos = list({f.name: f for f in all_photos}.values())

            if not all_photos:
                print(f"  ⚠️ {product_folder_name}: фото не знайдено")
                continue

            # 2. Обробка DOCX (Отримуємо весь контент)
            desc_file = product_dir / "description.docx"
            summary, details, cover, glass, orient = extract_docx_content(desc_file)

            description_json = {
                "text": summary,
                "details": details,
                "finishing": {"covering": {"text": cover}} if cover else None
            }

            sku = f"DOOR-{class_name.replace(' ', '-')}-{product_folder_name}".upper()
            
            # 3. Робота з БД
            result = await session.execute(select(Product).where(Product.sku == sku))
            product = result.scalar_one_or_none()
            
            if not product:
                product = Product(sku=sku, category_id=category_id, price=50000)
                session.add(product)
                await session.flush()

            # Оновлюємо характеристики
            product.name = f"{class_name} {product_folder_name}"
            product.description = description_json
            product.have_glass = glass
            product.orientation_choice = orient

            # 4. СИНХРОНІЗАЦІЯ ФОТО (Додаємо ті, яких немає)
            res_photos = await session.execute(select(ProductPhoto).where(ProductPhoto.product_id == product.id))
            existing_web_paths = {p.photo for p in res_photos.scalars().all()}
            
            for idx, photo_file in enumerate(all_photos):
                # Важливо: використовуємо реальне ім'я файлу photo_file.name
                web_path = f"/static/catalog/door/{class_name}/{product_folder_name}/{photo_file.name}"
                
                if web_path not in existing_web_paths:
                    is_main = (idx == 0 and not existing_web_paths)
                    session.add(ProductPhoto(
                        product_id=product.id,
                        photo=web_path,
                        is_main=is_main
                    ))
            
            count += 1
            print(f"  ✅ {sku}: Фото: {len(all_photos)}, Опис зчитано")
            
    return count

# ... (import_mouldings аналогічно до дверей з оновленим пошуком фото)

async def main():
    db_url = str(settings.db.url).replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Категорії
        res = await session.execute(select(Category).where(Category.name == "Двері"))
        cat_door = res.scalar_one_or_none() or Category(name="Двері", is_glass_available=True)
        if not cat_door.id: session.add(cat_door)
        
        await session.flush()
        
        print("🚀 Початок глибокого імпорту...")
        d_count = await import_doors(session, cat_door.id)
        
        await session.commit()
        print(f"🎉 Завершено! Оброблено об'єктів: {d_count}")

if __name__ == "__main__":
    asyncio.run(main())