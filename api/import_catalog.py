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
    """
    Зчитує весь текст з docx БЕЗ припущень про структуру.
    Повертає чисті дані - фронтенд сам визначить як їх відображати.
    """
    if not DOCX_AVAILABLE:
        print("  ⚠️ python-docx недоступний")
        return "Опис відсутній", [], None, False, False
    
    if not file_path.exists():
        print(f"  ⚠️ Файл не знайдено: {file_path}")
        return "Файл опису відсутній", [], None, False, False

    try:
        doc = Document(file_path)
        # Очищаємо порожні рядки
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        if not lines:
            print(f"  ⚠️ Документ порожній: {file_path}")
            return "Опис порожній", [], None, False, False

        # ✅ ЗБЕРІГАЄМО ВСІ РЯДКИ
        details = []
        for line in lines:
            details.append({"value": line})
        
        print(f"  📄 Зчитано {len(details)} рядків з DOCX")

        # Флаги для функціональності (скло, орієнтація)
        full_text = " ".join(lines).lower()
        has_glass = any(kw in full_text for kw in ['скло', 'скла', 'glass', 'скління'])
        has_orientation = any(kw in full_text for kw in ['праве', 'ліве', 'правий', 'лівий', 'сторона'])
        
        # Покриття - шукаємо перший рядок з ключовими словами
        covering_text = None
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in [
                'пвх', 'шпон', 'ламінат', 'горіх', 'дуб', 'ясен', 
                'вільха', 'сосна', 'бук', 'покриття', 'білоцерків'
            ]):
                covering_text = line
                print(f"  🎨 Покриття: {covering_text}")
                break
        
        # Якщо не знайшли покриття по ключовим словам, беремо другий рядок (якщо є)
        if not covering_text and len(lines) > 1:
            covering_text = lines[1]

        # Основний текст опису - перші 3 рядки через розділювач
        summary_text = " • ".join(lines[:3]) if len(lines) >= 3 else " • ".join(lines)
        
        print(f"  📝 Summary: {summary_text[:50]}...")
        print(f"  🔧 Has glass: {has_glass}, Has orientation: {has_orientation}")
        
        return summary_text, details, covering_text, has_glass, has_orientation
        
    except Exception as e:
        print(f"  ❌ Помилка парсингу docx: {e}")
        import traceback
        traceback.print_exc()
        return "Помилка читання файлу", [], None, False, False

async def import_doors(session, category_id):
    """Імпорт дверей з файлової системи до БД"""
    catalog_path = Path("static/catalog/door")
    if not catalog_path.exists():
        print("❌ Каталог дверей не знайдено")
        return 0
    
    count = 0
    for class_dir in sorted(catalog_path.iterdir()):
        if not class_dir.is_dir():
            continue
        
        class_name = class_dir.name
        print(f"\n📂 Обробка класу: {class_name}")
        
        for product_dir in sorted(class_dir.iterdir()):
            if not product_dir.is_dir():
                continue
            
            product_folder_name = product_dir.name
            print(f"\n  📁 Папка: {product_folder_name}")
            
            # 1. ЗБІР ВСІХ ФОТО З ПАПКИ
            photo_extensions = ['*.webp', '*.png', '*.jpg', '*.jpeg', '*.WEBP', '*.PNG', '*.JPG', '*.JPEG']
            all_photos = []
            for ext in photo_extensions:
                all_photos.extend(list(product_dir.glob(ext)))
            
            # Видаляємо дублікати за назвою файлу
            all_photos = list({f.name.lower(): f for f in all_photos}.values())
            # Сортуємо для стабільного порядку
            all_photos = sorted(all_photos, key=lambda x: x.name)

            if not all_photos:
                print(f"  ⚠️  Фото не знайдено, пропускаємо")
                continue

            print(f"  📸 Знайдено фото: {len(all_photos)}")

            # 2. ОБРОБКА DOCX
            desc_file = product_dir / "description.docx"
            summary, details, cover, glass, orient = extract_docx_content(desc_file)

            # ✅ ФОРМУЄМО JSON ОПИСУ - ПЕРЕВІРЯЄМО details!
            if not details or len(details) == 0:
                print(f"  ⚠️ УВАГА: details порожні! Перевірте файл {desc_file}")
                details = [{"value": "Опис відсутній"}]  # Fallback
            
            description_json = {
                "text": summary,
                "details": details  # ✅ Завжди масив об'єктів
            }
            
            # Додаємо finishing тільки якщо є покриття
            if cover:
                description_json["finishing"] = {
                    "covering": {
                        "text": cover
                    }
                }
            
            print(f"  📋 Details в JSON: {len(details)} елементів")

            # Генеруємо SKU
            sku = f"DOOR-{class_name.replace(' ', '-')}-{product_folder_name}".upper()
            
            # 3. РОБОТА З БД - Продукт
            result = await session.execute(select(Product).where(Product.sku == sku))
            product = result.scalar_one_or_none()
            
            if not product:
                # Створюємо новий продукт
                product = Product(
                    sku=sku,
                    category_id=category_id,
                    price=50000,
                    name=f"{class_name} {product_folder_name}",
                    description=description_json,
                    have_glass=glass,
                    orientation_choice=orient
                )
                session.add(product)
                await session.flush()
                print(f"  ➕ Створено новий продукт: {sku}")
            else:
                # ✅ ПРИМУСОВЕ ОНОВЛЕННЯ існуючого продукту
                product.name = f"{class_name} {product_folder_name}"
                product.description = description_json  # ← Перезаписуємо опис!
                product.have_glass = glass
                product.orientation_choice = orient
                print(f"  🔄 Оновлено продукт: {sku}")
            
            # Зберігаємо зміни перед роботою з фото
            await session.flush()

            # 4. СИНХРОНІЗАЦІЯ ФОТО
            res_photos = await session.execute(
                select(ProductPhoto).where(ProductPhoto.product_id == product.id)
            )
            existing_photos = res_photos.scalars().all()
            existing_web_paths = {p.photo for p in existing_photos}
            
            # Додаємо нові фото
            new_photos_count = 0
            for idx, photo_file in enumerate(all_photos):
                web_path = f"/static/catalog/door/{class_name}/{product_folder_name}/{photo_file.name}"
                
                if web_path not in existing_web_paths:
                    # Головне фото - перше по порядку, якщо немає інших фото
                    is_main = (idx == 0 and len(existing_photos) == 0)
                    
                    session.add(ProductPhoto(
                        product_id=product.id,
                        photo=web_path,
                        is_main=is_main
                    ))
                    new_photos_count += 1
            
            if new_photos_count > 0:
                print(f"  📸 Додано нових фото: {new_photos_count}")
            
            total_photos = len(existing_photos) + new_photos_count
            print(f"  ✅ {sku}: Всього фото: {total_photos}, Опис: {len(details)} рядків")
            
            count += 1
            
    return count

async def import_mouldings(session, category_id):
    """Імпорт лиштв з файлової системи до БД"""
    catalog_path = Path("static/catalog/mouldings")
    if not catalog_path.exists():
        print("❌ Каталог лиштв не знайдено")
        return 0
    
    count = 0
    for class_dir in sorted(catalog_path.iterdir()):
        if not class_dir.is_dir():
            continue
        
        class_name = class_dir.name
        print(f"\n📂 Обробка класу лиштв: {class_name}")
        
        for product_dir in sorted(class_dir.iterdir()):
            if not product_dir.is_dir():
                continue
            
            product_folder_name = product_dir.name
            print(f"\n  📁 Папка: {product_folder_name}")
            
            # Збір фото
            photo_extensions = ['*.webp', '*.png', '*.jpg', '*.jpeg', '*.WEBP', '*.PNG', '*.JPG', '*.JPEG']
            all_photos = []
            for ext in photo_extensions:
                all_photos.extend(list(product_dir.glob(ext)))
            
            all_photos = list({f.name.lower(): f for f in all_photos}.values())
            all_photos = sorted(all_photos, key=lambda x: x.name)

            if not all_photos:
                print(f"  ⚠️  Фото не знайдено, пропускаємо")
                continue
            
            print(f"  📸 Знайдено фото: {len(all_photos)}")

            # Обробка DOCX
            desc_file = product_dir / "description.docx"
            summary, details, cover, glass, orient = extract_docx_content(desc_file)

            if not details or len(details) == 0:
                print(f"  ⚠️ УВАГА: details порожні! Перевірте файл {desc_file}")
                details = [{"value": "Опис відсутній"}]
            
            description_json = {
                "text": summary,
                "details": details
            }
            
            if cover:
                description_json["finishing"] = {
                    "covering": {
                        "text": cover
                    }
                }
            
            print(f"  📋 Details в JSON: {len(details)} елементів")

            sku = f"MOULDING-{class_name.replace(' ', '-')}-{product_folder_name}".upper()
            
            # Робота з БД
            result = await session.execute(select(Product).where(Product.sku == sku))
            product = result.scalar_one_or_none()
            
            if not product:
                product = Product(
                    sku=sku,
                    category_id=category_id,
                    price=5000,
                    name=f"{class_name} {product_folder_name}",
                    description=description_json,
                    have_glass=False,
                    orientation_choice=False
                )
                session.add(product)
                await session.flush()
                print(f"  ➕ Створено нову лиштву: {sku}")
            else:
                product.name = f"{class_name} {product_folder_name}"
                product.description = description_json
                print(f"  🔄 Оновлено лиштву: {sku}")
            
            await session.flush()

            # Синхронізація фото
            res_photos = await session.execute(
                select(ProductPhoto).where(ProductPhoto.product_id == product.id)
            )
            existing_photos = res_photos.scalars().all()
            existing_web_paths = {p.photo for p in existing_photos}
            
            new_photos_count = 0
            for idx, photo_file in enumerate(all_photos):
                web_path = f"/static/catalog/moulding/{class_name}/{product_folder_name}/{photo_file.name}"
                
                if web_path not in existing_web_paths:
                    is_main = (idx == 0 and len(existing_photos) == 0)
                    
                    session.add(ProductPhoto(
                        product_id=product.id,
                        photo=web_path,
                        is_main=is_main
                    ))
                    new_photos_count += 1
            
            if new_photos_count > 0:
                print(f"  📸 Додано нових фото: {new_photos_count}")
            
            total_photos = len(existing_photos) + new_photos_count
            print(f"  ✅ {sku}: Всього фото: {total_photos}, Опис: {len(details)} рядків")
            
            count += 1
            
    return count

async def main():
    """Головна функція імпорту"""
    db_url = str(settings.db.url).replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 60)
        print("🚀 ПОЧАТОК ІМПОРТУ КАТАЛОГУ")
        print("=" * 60)
        
        # Створення/отримання категорій
        res_door = await session.execute(select(Category).where(Category.name == "Двері"))
        cat_door = res_door.scalar_one_or_none()
        
        if not cat_door:
            cat_door = Category(name="Двері", is_glass_available=True)
            session.add(cat_door)
            await session.flush()
            print("✅ Створено категорію: Двері")
        else:
            print("✅ Знайдено категорію: Двері")
        
        res_moulding = await session.execute(select(Category).where(Category.name == "Лиштви"))
        cat_moulding = res_moulding.scalar_one_or_none()
        
        if not cat_moulding:
            cat_moulding = Category(name="Лиштви", is_glass_available=False)
            session.add(cat_moulding)
            await session.flush()
            print("✅ Створено категорію: Лиштви")
        else:
            print("✅ Знайдено категорію: Лиштви")
        
        print("\n" + "=" * 60)
        print("📂 ІМПОРТ ДВЕРЕЙ")
        print("=" * 60)
        door_count = await import_doors(session, cat_door.id)
        
        print("\n" + "=" * 60)
        print("📂 ІМПОРТ ЛИШТВ")
        print("=" * 60)
        moulding_count = await import_mouldings(session, cat_moulding.id)
        
        # Збереження змін
        await session.commit()
        
        print("\n" + "=" * 60)
        print("🎉 ІМПОРТ ЗАВЕРШЕНО!")
        print("=" * 60)
        print(f"📊 Статистика:")
        print(f"   - Дверей оброблено: {door_count}")
        print(f"   - Лиштв оброблено: {moulding_count}")
        print(f"   - Всього продуктів: {door_count + moulding_count}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())