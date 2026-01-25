# 📄 CV Templates Generator

Генератор профессиональных резюме и сопроводительных писем для Premium пользователей.

## 🎨 Доступные шаблоны:

### 1. **Klasyczny** (Традиционный)
- Для: банки, корпорации, консервативные компании
- Стиль: строгий, профессиональный
- Цвета: синий, черный, белый
- Структура: стандартная, без излишеств

### 2. **Nowoczesny** (Современный) [В разработке]
- Для: IT, стартапы, технологические компании
- Стиль: современный, минималистичный
- Цвета: серый, синий, акценты
- Структура: модульная, визуально привлекательная

### 3. **Kreatywny** (Креативный) [Планируется]
- Для: дизайн, маркетинг, креативные индустрии
- Стиль: яркий, нестандартный
- Цвета: разноцветные акценты
- Структура: свободная, с графическими элементами

### 4. **Minimalny** (Минималистичный) [Планируется]
- Для: менеджмент, консалтинг
- Стиль: чистый, лаконичный
- Цвета: черно-белый с акцентом
- Структура: максимально простая

### 5. **Europass** [Планируется]
- Для: европейские компании, международные организации
- Стиль: стандартизированный
- Формат: Europass CV
- Структура: согласно стандарту ЕС

---

## 📋 Структура данных:

```python
CV_DATA = {
    # Osobiste
    'imie': 'Jan',
    'nazwisko': 'Kowalski',
    'email': 'jan@example.com',
    'telefon': '+48 123 456 789',
    'miasto': 'Warszawa',
    'data_urodzenia': '01.01.1990',  # opcjonalne
    
    # Cel
    'stanowisko': 'Python Developer',
    
    # O sobie
    'o_sobie': 'Krótki opis (2-3 zdania)...',
    
    # Doświadczenie
    'doswiadczenie': [
        {
            'stanowisko': 'Stanowisko',
            'firma': 'Nazwa firmy',
            'okres': '2020 - 2023',
            'opis': 'Opis obowiązków...'
        }
    ],
    
    # Wykształcenie
    'wyksztalcenie': [
        {
            'uczelnia': 'Nazwa uczelni',
            'kierunek': 'Kierunek studiów',
            'stopien': 'Inżynier / Magister / Licencjat',
            'okres': '2015 - 2019'
        }
    ],
    
    # Umiejętności
    'umiejetnosci': ['Python', 'SQL', 'Git'],
    
    # Języki
    'jezyki': [
        {'jezyk': 'Polski', 'poziom': 'Ojczysty'},
        {'jezyk': 'Angielski', 'poziom': 'B2'}
    ],
    
    # Zainteresowania
    'zainteresowania': ['Programowanie', 'Sport']
}
```

---

## 🚀 Użycie:

```python
from templates_cv.cv_generator import CVGenerator

generator = CVGenerator()

# Generowanie CV
cv_path = generator.generate_klasyczny(CV_DATA)
print(f"CV zapisane: {cv_path}")

# Generowanie listu motywacyjnego
letter_data = {
    'miasto': 'Warszawa',  # opcjonalne
    'tresc': 'Własna treść listu...'  # opcjonalne (auto-generacja jeśli puste)
}
letter_path = generator.generate_list_motywacyjny(letter_data, CV_DATA)
print(f"List zapisany: {letter_path}")
```

---

## 📁 Struktura:

```
templates_cv/
├── cv_generator.py       # Główny generator
├── templates/            # Szablony DOCX (przyszłość)
├── generated/            # Wygenerowane pliki
└── README.md            # Ta dokumentacja
```

---

## ✨ Funkcje:

- ✅ Automatyczne formatowanie
- ✅ Profesjonalne układy
- ✅ Wsparcie dla polskich znaków
- ✅ Klauzula RODO
- ✅ Data generowania
- ✅ Ikony emoji (📧 📱 📍 💼 🎓)
- ✅ Export do DOCX
- ⏳ Export do PDF (planowane)
- ⏳ Edycja w przeglądarce (planowane)

---

## 🎯 Integracja z Premium:

Po zakupie Premium (39 zł):
1. Użytkownik wypełnia formularz z danymi
2. System generuje CV + List motywacyjny
3. Pliki wysyłane na email
4. Możliwość pobrania z panelu

---

## 📧 Email po zakupie Premium:

```
Temat: Twoje szablony CV - cv-konwerter.pl

Cześć [Imię]!

Dziękujemy za zakup Premium! 🎉

W załącznikach znajdziesz:
✅ CV w stylu Klasycznym
✅ List motywacyjny

Możesz edytować pliki w Microsoft Word lub Google Docs.

Powodzenia w poszukiwaniu pracy!

Zespół cv-konwerter.pl
```

---

## 🔧 Rozwój:

### Faza 1 (DONE):
- ✅ Szablon Klasyczny
- ✅ List motywacyjny
- ✅ Generator DOCX

### Faza 2 (TODO):
- ⏳ Szablon Nowoczesny
- ⏳ Szablon Kreatywny
- ⏳ Integracja z web_app.py
- ⏳ Formularz na stronie

### Faza 3 (TODO):
- ⏳ Email sending
- ⏳ Przelewy24 integration
- ⏳ Panel użytkownika
- ⏳ Historia generowanych CV

---

**Utworzono:** 2026-01-25  
**Status:** ✅ MVP Ready
