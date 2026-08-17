from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import math
import requests

app = Flask(__name__)
app.secret_key = 'super_secret_restaurant_key'

TELEGRAM_BOT_TOKEN = '8957930838:AAFXnwIwTnpYwy1kyHyGKC6NPTdZkRvQR24'
TELEGRAM_CHAT_ID = '1406917090'

елементи = []
global_reservations = []
global_orders = []

def send_telegram_notification(order):
    if TELEGRAM_CHAT_ID == 'ВСТАВТЕ_СЮДИ_ВАШ_CHAT_ID':
        print("⚠️ Увага: Не вказано TELEGRAM_CHAT_ID!")
        return

    items_text = ""
    for item in order['order_list']:
        items_text += f"• {item['name']} — {item['count']} шт. ({item['total']} грн)\n"

    message = (
        f"🔔 *НОВЕ ЗАМОВЛЕННЯ #{order['id']}!*\n\n"
        f"⏱ *Час:* {order['order_time']}\n"
        f"💰 *Загальна сума:* {order['total_price']} грн\n\n"
        f"📋 *Склад замовлення:*\n{items_text}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Помилка відправки в Telegram: {e}")


def send_telegram_reservation_notification(reservation):
    if TELEGRAM_CHAT_ID == 'ВСТАВТЕ_СЮДИ_ВАШ_CHAT_ID':
        return

    message = (
        f"🍷 *НОВЕ БРОНЮВАННЯ СТОЛИКА #{reservation['id']}!*\n\n"
        f"👤 *Ім'я клієнта:* {reservation['name']}\n"
        f"📞 *Телефон:* {reservation['phone']}\n"
        f"📅 *Дата:* {reservation['date']}\n"
        f"⏰ *Час:* {reservation['time']}\n"
        f"👥 *Кількість гостей:* {reservation['guests']}\n"
        f"⏱ *Час створення:* {reservation['created_at']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Помилка відправки бронювання в Telegram: {e}")


class AnonymousUser:
    is_authenticated = False
    is_admin = False
    nickname = "Гість"


class User:
    def __init__(self, id, nickname, email, role='Клієнт', is_admin=False, password='123'):
        self.id = id
        self.is_authenticated = True
        self.nickname = nickname
        self.email = email
        self.role = role
        self.is_admin = is_admin
        self.password = password


class Item:
    def __init__(self, id, name, description, price, weight, file_name, composition, category=None, is_active=True):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.weight = weight
        self.file_name = file_name
        self.composition = composition
        self.is_active = is_active

        if category:
            self.category = category
        else:
            name_lower = name.lower()
            if 'піца' in name_lower:
                self.category = 'Піца'
            elif 'бургер' in name_lower:
                self.category = 'Бургери'
            elif 'паста' in name_lower:
                self.category = 'Паста'
            elif 'салат' in name_lower:
                self.category = 'Салати'
            elif 'суші' in name_lower or 'маки' in name_lower:
                self.category = 'Суші'
            elif any(n in name_lower for n in
                     ['кола', 'спрайт', 'фанта', 'сік', 'лимонад', 'мохіто', 'вино', 'пиво', 'текіла', 'ром', 'віскі']):
                self.category = 'Напої'
            else:
                self.category = 'Основне'


елементи = [
    # --- Піца ---
    Item(id=1, name='Піца Маргарита', description='Класична піца з соковитими томатами та сиром моцарела', price=180,
         weight='450',
         file_name='https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500',
         composition='Томатний соус, моцарела, базилік, оливкова олія', category='Піца', is_active=True),
    Item(id=6, name='Піца Пеппероні', description='Гостра піца з соковитою ковбасою пеппероні та сиром моцарела',
         price=210, weight='480',
         file_name='https://images.unsplash.com/photo-1628840042765-356cda07504e?w=500',
         composition='Пеппероні, моцарела, томатний соус, орегано', category='Піца', is_active=True),
    Item(id=13, name='Піца Чотири Сири', description='Вишукане поєднання чотирьох елітних сирів для справжніх гурманів',
         price=240, weight='430',
         file_name='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500',
         composition='Сир моцарела, горгонзола, пармезан, дорблю, вершковий соус', category='Піца', is_active=True),
    Item(id=14, name='Піца Барбекю', description='Ароматна піца з куркою, соусом барбекю та червоною цибулею',
         price=225, weight='490',
         file_name='https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500',
         composition='Куряче філе, бекон, соус барбекю, моцарела, цибуля', category='Піца', is_active=True),
    Item(id=15, name='Піца Капричоза', description='Традиційна італійська піца з шинкою, грибами та артишоками',
         price=215, weight='460',
         file_name='https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=500',
         composition='Шинка, шампіньйони, моцарела, томатний соус, оливки', category='Піца', is_active=True),

    # --- Напої (безалкогольні та алкогольні) ---
    Item(id=10, name='Кока-Кола 250мл', description='Освіжаючий газований напій Coca-Cola в пляшці', price=45,
         weight='250',
         file_name='https://c4.wallpaperflare.com/wallpaper/912/293/109/coca-cola-cans-coca-cola-cans-wallpaper-preview.jpg',
         composition='Газована вода, цукор, карамельний колір, ортофосфорна кислота', category='Напої', is_active=True),
    Item(id=11, name='Спрайт 250мл', description='Освіжаючий газований напій зі смаком лимона та лайма', price=45,
         weight='250',
         file_name='https://www.shutterstock.com/image-photo/poznan-pol-apr-02-2025-260nw-2609175503.jpg',
         composition='Газована вода, цукор, лимонна кислота, натуральні ароматизатори', category='Напої',
         is_active=True),
    # Додано 2 безалкогольні напої:
    Item(id=16, name='Фірмовий Лимонад Імбир-М`ята',
         description='Освіжаючий охолоджений домашній лимонад із м`ятою та імбиром', price=75, weight='400',
         file_name='https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500',
         composition='Вода газована, сік лимона, фреш імбиру, м`ята, цукровий сироп', category='Напої', is_active=True),
    Item(id=17, name='Смузі Тропічний Манго',
         description='Густий та ніжний вітамінний мікс з манго та апельсинового соку', price=95, weight='300',
         file_name='https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=500',
         composition='Пюре манго, апельсиновий сік, банан, льоду крихта', category='Напої', is_active=True),
    # Додано 3 алкогольні напої:
    Item(id=18, name='Коктейль Апероль Шприц',
         description='Легкий іскраристий італійський алкогольний коктейль з апельсином', price=160, weight='250',
         file_name='https://images.unsplash.com/photo-1560512823-829485b8bf24?w=500',
         composition='Лікер Апероль, просеко, содова, апельсин, лід', category='Напої', is_active=True),
    Item(id=19, name='Вино Напівсолодке Червоне (Келих)',
         description='Витончене червоне столове вино з багатим фруктовим букетом', price=120, weight='150',
         file_name='https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500',
         composition='Виноградне витримане вино (червоне напівсолодке)', category='Напої', is_active=True),
    Item(id=20, name='Крафтове Пиво Світле',
         description='Холодне світле нефільтроване пиво з м`якою хмільною гірчинкою', price=90, weight='500',
         file_name='https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=500',
         composition='Вода, солод ячмінний, хміль, дріжджі пивні', category='Напої', is_active=True),

    # --- Бургери ---
    Item(id=2, name='Бургер Чіз', description='Соковита яловича котлета з сиром чеддер та соусом', price=150,
         weight='350',
         file_name='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500',
         composition='Яловича котлета, булочка, сир чеддер, мариновані огірки, соус', category='Бургери',
         is_active=True),
    Item(id=7, name='Курячий Бургер', description='Ніжне куряче філе в хрусткій паніровці з соусом та свіжими овочами',
         price=160, weight='360',
         file_name='https://images.unsplash.com/photo-1615297928064-24977384d0da?w=500',
         composition='Куряче філе, булочка, салат айсберг, томати, соус тар-тар', category='Бургери', is_active=True),
    Item(id=21, name='Подвійний Бекон Бургер',
         description='Дві потужні яловичі котлети з хрустким беконом та соусом BBQ', price=210, weight='440',
         file_name='https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=500',
         composition='Дві котлети з яловичини, бекон, сир чеддер, соус BBQ, цибуля фрі', category='Бургери',
         is_active=True),
    Item(id=22, name='Острий Мексиканський Бургер',
         description='Бургер з пікантним перцем халапеньо та гострим фірмовим соусом', price=175, weight='380',
         file_name='https://images.unsplash.com/photo-1550547660-d9450f859349?w=500',
         composition='Яловича котлета, перець халапеньо, сир, соус сальса, салат', category='Бургери', is_active=True),
    Item(id=23, name='Фірмовий Вегетаріанський Бургер',
         description='Овочева котлета з нуту та грибів зі свіжою зеленню і соусом песто', price=145, weight='320',
         file_name='https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500',
         composition='Котлета з нуту, соус песто, авокадо, рукола, томати', category='Бургери', is_active=True),

    # --- Паста ---
    Item(id=3, name='Паста Карбонара', description='Традиційна італійська паста з беконом та вершками', price=210,
         weight='300',
         file_name='https://images.unsplash.com/photo-1612874742237-6526221588e3?w=500',
         composition='Спагеті, бекон, вершки, пармезан, яєчний жовток', category='Паста', is_active=True),
    Item(id=24, name='Паста Болоньєзе', description='Класична паста з м`ясним соусом із соковитої яловичини та томатів',
         price=195, weight='350',
         file_name='https://cdn.lifehacker.ru/wp-content/uploads/2025/05/shutterstock_1128670595_1_1747032145.jpg',
         composition='Тальятелле, м`ясний фарш яловичий, томатний соус, пармезан', category='Паста', is_active=True),
    Item(id=25, name='Паста з Грибами та Трюфельною Олією',
         description='Ароматна паста з лісовими грибами у вершковому соусі', price=230, weight='320',
         file_name='https://images.unsplash.com/photo-1645112411341-6c4fd023714a?w=500',
         composition='Феттучіні, шампіньйони, білі гриби, вершки, трюфельна олія', category='Паста', is_active=True),
    Item(id=26, name='Паста з Керветками та Лососем у Вершках',
         description='Ніжна паста з морепродуктами під вершково-часниковим соусом', price=280, weight='340',
         file_name='https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500',
         composition='Тигрові креветки, шматочки лосося, вершки, часник, зелень', category='Паста', is_active=True),
    Item(id=27, name='Паста Чотири Сири (Кватро Формаджі)',
         description='Паста в густому насиченому соусі з чотирьох видів сиру', price=220, weight='310',
         file_name='https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=500',
         composition='Пенне, сир дорблю, моцарела, гауда, пармезан, вершки', category='Паста', is_active=True),

    # --- Салати ---
    Item(id=4, name='Салат Цезар', description='Свіжий салат з курячим філе, сухариками та соусом цезар', price=160,
         weight='280',
         file_name='https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=500',
         composition='Куряче філе, салат айсберг, сухарики, пармезан, соус цезар', category='Салати', is_active=True),
    Item(id=28, name='Грецький Салат', description='Класичний легкий салат зі свіжих овочів, сиром фета та оливками',
         price=140, weight='300',
         file_name='https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500',
         composition='Томати, огірки, болгарський перець, сир фета, оливки, оливкова олія', category='Салати',
         is_active=True),
    Item(id=29, name='Салат з Телятиною Гриль та Авокадо',
         description='Теплий салат з шматочками ніжної телятини, авокадо та міксом салатів', price=220, weight='290',
         file_name='https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500',
         composition='Вирізка телятини, авокадо, мікс салатів, чері, медово-гірчична заправка', category='Салати',
         is_active=True),
    Item(id=30, name='Салат Цезар з Креветками',
         description='Популярний салат Цезар з тигровими креветками та перепелиними яйцями', price=240, weight='280',
         file_name='https://img.povar.ru/mobile/77/b1/c3/41/salat_cezar_s_krevetkami_klassicheskii_prostoi-860505.jpg',
         composition='Тигрові креветки, айсберг, перепелині яйця, пармезан, сухарики', category='Салати',
         is_active=True),
    Item(id=31, name='Салат з Лососем та Шпинатом',
         description='Вишуканий салат зі слабосолоним лососем та свіжими листочками шпинату', price=250, weight='260',
         file_name='https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=500',
         composition='Лосось слабосолоний, шпинат, авокадо, кедрові горішки, лимонний соус', category='Салати',
         is_active=True),

    # --- Суші ---
    Item(id=5, name='Суші Сет Філадельфія', description='Великий асорті сет з лососем, крем-сиром та авокадо',
         price=420, weight='800',
         file_name='https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500',
         composition='Лосось, рис, норі, крем-сир, авокадо, огірок', category='Суші', is_active=True),
    Item(id=9, name='Запечені маки з креветкою',
         description='Гарячі хрусткі маки з тигровою креветкою та спайсі соусом', price=260, weight='230',
         file_name='https://assets.dots.live/misteram-public/018ef573-6bfd-7013-8929-319b6fea5097-826x0.png',
         composition='Тигрова креветка, вершковий сир, спайсі соус, рис, норі, сухарі панко', category='Суші',
         is_active=True),
    Item(id=32, name='Рол Каліфорнія з Вугром', description='Класичний рол в ікрі масаго з копченим вугром та авокадо',
         price=290, weight='250',
         file_name='https://images.unsplash.com/photo-1611143669185-af224c5e3252?w=500',
         composition='Вугор, авокадо, огірок, ікра масаго, майонез, рис, норі', category='Суші', is_active=True),
    Item(id=33, name='Рол Дракон Золотий', description='Елітний рол з подвійним шаром вугра, соусом унагі та кунжутом',
         price=340, weight='290',
         file_name='https://pizza-sushi.com.ua/sites/default/files/content/blyudo/blyudo-preview-images/sushi-zolotoy-drakon-roll-irpen-bucha-zakaz-dostavka-edy.jpg',
         composition='Вугор, креветка в темпурі, крем-сир, авокадо, соус унагі, кунжут', category='Суші',
         is_active=True),
    Item(id=34, name='Макі з Лососем', description='Легкі та класичні міні-роли з ніжним свіжим лососем', price=170,
         weight='180',
         file_name='https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=500',
         composition='Лосось, рис, норі', category='Суші', is_active=True),

    # --- Основне ---
    Item(id=35, name='Стейк із Свинини на Грилі',
         description='Соковитий м`ясний стейк на кістці з соусом ткемалі та зеленню', price=310, weight='350',
         file_name='https://images.unsplash.com/photo-1544025162-d76694265947?w=500',
         composition='Свинячий стейк на грилі, соус ткемалі, спеції, маринована цибуля', category='Основне',
         is_active=True),
    Item(id=36, name='Куряче Філе Су-Від з Овочами Гриль',
         description='Дієтичне куряче філе приготування су-від з гарніром з сезонних овочів', price=220, weight='330',
         file_name='https://shuba.life/static/content/thumbs/1040x650/a/ed/3hq7mi---c8x5x50px50p-up--29cc29cb731e94d91c1d9686eaf36eda.jpg',
         composition='Куряче філе, цукіні, болгарський перець, баклажани, соус песто', category='Основне',
         is_active=True),
    Item(id=37, name='Лосось на Грилі з Лимонним Соусом',
         description='Ніжне філе червоної риби на грилі з легким лимонно-вершковим соусом', price=380, weight='270',
         file_name='https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=500',
         composition='Філе лосося, лимон, вершки, зелень, спеції', category='Основне', is_active=True),
    Item(id=38, name='Медальйони з Телятини в Беконі',
         description='Преміальні м`які медальйони з телятини, обгорнуті хрустким беконом', price=390, weight='310',
         file_name='https://images.unsplash.com/photo-1558030006-450675393462?w=500',
         composition='Теляча вирізка, бекон, вершково-грибний соус, мікрогрін', category='Основне', is_active=True),
    Item(id=39, name='Картопля по-Селянськи з Трав`яним Соусом',
         description='Золотисті запечені часточки картоплі з часником та пряними травами', price=95, weight='250',
         file_name='https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500',
         composition='Картопля, часник, паприка, олія соняшникова, зелень, часниковий соус', category='Основне',
         is_active=True)
]

users_db = [
    User(1, 'Олександр (Admin)', 'admin@restaurant.com', role='Адміністратор', is_admin=True, password='admin123'),
]

@app.context_processor
def inject_user():
    user_data = session.get('user')
    if user_data:
        user = User(
            id=user_data.get('id', 1),
            nickname=user_data.get('nickname', 'Користувач'),
            email=user_data.get('email', 'user@mail.com'),
            role=user_data.get('role', 'Адміністратор' if user_data.get('is_admin') else 'Клієнт'),
            is_admin=user_data.get('is_admin', False)
        )
    else:
        user = AnonymousUser()
    return dict(current_user=user)


@app.route('/')
@app.route('/index')
def index():
    featured_items = [i for i in елементи if i.is_active][:3]
    return render_template('index.html', items=featured_items)

class Item:
    def __init__(self, id, name, description, price, weight, composition, category, file_name, is_active=True):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.weight = weight
        self.composition = composition
        self.category = category if category else 'Інше'
        self.file_name = file_name
        self.is_active = is_active  # За замовчуванням страва одразу активна

@app.route('/add_position', methods=['POST'])
def add_position():
    global елементи
    user_data = session.get('user')

    # Перевірка прав адміністратора
    if not user_data or not user_data.get('is_admin'):
        flash('Доступ заборонено!', 'danger')
        return redirect(url_for('index'))

    # Генерація унікального ID
    new_id = max([i.id for i in елементи], default=0) + 1 if елементи else 1

    # Отримуємо дані з форми
    name = request.form.get('name')
    description = request.form.get('description')

    try:
        price = float(request.form.get('price'))
    except (ValueError, TypeError):
        price = 0.0

    weight = request.form.get('weight')
    composition = request.form.get('composition')
    category = request.form.get('category')
    file_name = request.form.get('file_name')

    # Створюємо новий об'єкт із примусовим is_active=True
    new_item = Item(
        id=new_id,
        name=name,
        description=description,
        price=price,
        weight=weight,
        composition=composition,
        category=category,
        file_name=file_name,
        is_active=True
    )

    # Додаємо в глобальний список
    елементи.append(new_item)

    flash(f'Страву "{name}" успішно додано!', 'success')
    return redirect(url_for('menu_check'))

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = next((i for i in елементи if i.id == item_id), None)
    if not item:
        flash('Страву не знайдено!', 'danger')
        return redirect(url_for('menu'))
    return render_template('product.html', product=item)

@app.route('/menu')
def menu():
    active_items = [i for i in елементи if i.is_active]

    all_cats = sorted(list(set(i.category for i in active_items if i.category)))
    categories = []
    if 'Напої' in all_cats:
        categories.append('Напої')
        all_cats.remove('Напої')
    categories.extend(all_cats)

    selected_category = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip().lower()

    filtered_items = active_items

    if selected_category:
        filtered_items = [i for i in filtered_items if i.category and i.category.lower() == selected_category.lower()]

    if search_query:
        filtered_items = [
            i for i in filtered_items
            if search_query in i.name.lower() or (i.description and search_query in i.description.lower()) or (
                        i.composition and search_query in i.composition.lower())
        ]

    return render_template(
        'menu.html',
        items=filtered_items,
        categories=categories,
        selected_category=selected_category,
        search_query=search_query
    )



@app.route('/menu_check', methods=['GET', 'POST'])
def menu_check():
    global елементи, global_reservations, global_orders
    user_data = session.get('user')

    # 1. Перевірка адміна
    if not user_data or not user_data.get('is_admin'):
        flash('Ця сторінка доступна лише адміністратору!', 'danger')
        return redirect(url_for('index'))

    # 2. ЗАВЖДИ формуємо список бронювань
    session_res = session.get('reservations', [])
    combined_res = global_reservations.copy()
    for idx, r in enumerate(session_res, start=len(global_reservations) + 1):
        combined_res.append({
            'id': idx,
            'name': r.get('name'),
            'phone': r.get('phone'),
            'date': r.get('date'),
            'time': r.get('time'),
            'guests': r.get('guests'),
            'status': r.get('status', 'Підтверджено'),
            'created_at': r.get('created_at', '')
        })

    # 3. Обробка дій
    if request.method == 'POST':
        # --- Бронювання: зміна статусу ---
        if 'res_id' in request.form:
            res_id = int(request.form.get('res_id'))
            new_status = request.form.get('status')
            for r in global_reservations:
                if r['id'] == res_id:
                    r['status'] = new_status
                    flash(f'Статус броні #{res_id} змінено на "{new_status}"', 'info')
                    break
            return redirect(url_for('menu_check'))

        # --- Бронювання: повне видалення ---
        if 'delete_res_id' in request.form:
            del_res_id = int(request.form.get('delete_res_id'))
            global_len = len(global_reservations)

            if del_res_id <= global_len:
                global_reservations = [r for r in global_reservations if r['id'] != del_res_id]
            else:
                session_res_data = session.get('reservations', [])
                session_index = del_res_id - global_len - 1
                if 0 <= session_index < len(session_res_data):
                    session_res_data.pop(session_index)
                    session['reservations'] = session_res_data
                    session.modified = True

            flash(f'Бронювання #{del_res_id} успішно видалено!', 'danger')
            return redirect(url_for('menu_check'))

        # --- Замовлення: прийняти або видалити ---
        if 'order_id' in request.form:
            order_id = int(request.form.get('order_id'))
            order_action = request.form.get('order_action')
            for o in global_orders:
                if o['id'] == order_id:
                    if order_action == 'accept':
                        o['status'] = 'Прийнято'
                        flash(f'Замовлення #{order_id} прийнято!', 'success')
                    elif order_action == 'delete':
                        global_orders.remove(o)
                        flash(f'Замовлення #{order_id} видалено!', 'danger')
                    break
            return redirect(url_for('menu_check'))

        # --- Меню: активувати / деактивувати / видалити ---
        action = request.form.get('action')
        selected_ids = request.form.getlist('selected_items')
        selected_ids = [int(i) for i in selected_ids]

        if not selected_ids:
            flash('Не вибрано жодної позиції для дії!', 'warning')
        else:
            if action == 'activate':
                for item in елементи:
                    if item.id in selected_ids:
                        item.is_active = True
                flash(f'Активовано позицій: {len(selected_ids)}', 'success')
            elif action == 'deactivate':
                for item in елементи:
                    if item.id in selected_ids:
                        item.is_active = False
                flash(f'Деактивовано позицій: {len(selected_ids)}', 'warning')
            elif action == 'delete':
                елементи = [item for item in елементи if item.id not in selected_ids]
                flash(f'Видалено позицій: {len(selected_ids)}', 'danger')

        return redirect(url_for('menu_check'))

    # 4. GET-запит: підготовка даних для відображення
    search_query = request.args.get('q', '').strip().lower()
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 40  # Щоб усі страви поміщалися

    filtered_list = елементи
    if search_query:
        filtered_list = [
            i for i in filtered_list
            if search_query in i.name.lower() or (i.composition and search_query in i.composition.lower())
        ]

    if status_filter == 'active':
        filtered_list = [i for i in filtered_list if i.is_active]
    elif status_filter == 'inactive':
        filtered_list = [i for i in filtered_list if not i.is_active]

    total_items = len(filtered_list)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = filtered_list[start:end]

    return render_template(
        'menu_check.html',
        items=paginated_items,
        search_query=search_query,
        status_filter=status_filter,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        reservations=combined_res,
        orders=global_orders
    )


@app.route('/admin/orders', methods=['GET', 'POST'])
def admin_orders():
    if request.method == 'POST':
        order_id = int(request.form.get('order_id'))
        action = request.form.get('action')
        for o in global_orders:
            if o['id'] == order_id:
                if action == 'accept': o['status'] = 'Прийнято'
                elif action == 'delete': global_orders.remove(o)
        return redirect(url_for('admin_orders'))
    return render_template('admin_orders.html', orders=global_orders)

@app.route('/admin/delete_reservation/<int:res_id>')
def delete_reservation(res_id):
    global global_reservations
    global_reservations = [r for r in global_reservations if r['id'] != res_id]
    flash('Бронювання видалено', 'danger')
    return redirect(url_for('reservations_check'))

@app.route('/edit_position/<int:item_id>', methods=['GET', 'POST'])
def edit_position(item_id):
    item = next((i for i in елементи if i.id == item_id), None)
    if not item:
        flash('Позицію не знайдено!', 'danger')
        return redirect(url_for('menu_check'))

    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.price = float(request.form.get('price', 0))
        item.weight = request.form.get('weight')
        item.file_name = request.form.get('file_name')
        item.composition = request.form.get('composition')
        item.is_active = True if request.form.get('is_active') else False

        flash(f'Позицію "{item.name}" успішно оновлено!', 'success')
        return redirect(url_for('menu_check'))

    return render_template('edit_position.html', item=item)


@app.route('/all_users')
def all_users():
    return render_template('all_users.html', users=users_db)


@app.route('/reservations_check', methods=['GET', 'POST'])
def reservations_check():
    if request.method == 'POST':
        res_id = int(request.form.get('res_id'))
        new_status = request.form.get('status')
        for r in global_reservations:
            if r['id'] == res_id:
                r['status'] = new_status
                flash(f'Статус броні #{res_id} змінено на "{new_status}"', 'info')
                break
        return redirect(url_for('reservations_check'))

    session_res = session.get('reservations', [])
    combined = global_reservations.copy()
    for idx, r in enumerate(session_res, start=len(global_reservations) + 1):
        combined.append({
            'id': idx,
            'name': r.get('name'),
            'phone': r.get('phone'),
            'date': r.get('date'),
            'time': r.get('time'),
            'guests': r.get('guests'),
            'status': r.get('status', 'Підтверджено'),
            'created_at': r.get('created_at', '')
        })

    return render_template('reservations_check.html', reservations=combined)


@app.route('/update_order_status/<int:order_id>/<string:new_status>')
def update_order_status(order_id, new_status):
    # Шукаємо замовлення за ID та змінюємо статус
    for order in global_orders:
        if order['id'] == order_id:
            order['status'] = new_status
            flash(f'Статус замовлення #{order_id} змінено на: "{new_status}"', 'success')
            break
    return redirect(url_for('menu_check'))


@app.route('/update_reservation_status_post', methods=['POST'])
def update_reservation_status_post():
    res_id = request.form.get('res_id')
    new_status = request.form.get('status')

    if res_id and new_status:
        for res in global_reservations:
            if str(res.get('id')) == str(res_id):
                res['status'] = new_status
                flash(f'Статус бронювання #{res_id} змінено на "{new_status}"', 'success')
                break

    return redirect(url_for('menu_check'))

@app.route('/update_order_status_post', methods=['POST'])
def update_order_status_post():
    order_id = request.form.get('order_id')
    new_status = request.form.get('status')

    if order_id and new_status:
        for order in global_orders:
            if str(order.get('id')) == str(order_id):
                order['status'] = new_status
                flash(f'Статус замовлення #{order_id} змінено на "{new_status}"', 'success')
                break

    return redirect(url_for('menu_check'))


@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    global елементи
    # Знаходимо та видаляємо страву за її id
    елементи = [item for item in елементи if item.id != item_id]
    flash('Страву успішно видалено з меню!', 'success')
    return redirect(url_for('menu_check'))


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    global елементи
    user_data = session.get('user')

    # Перевірка прав адміністратора
    if not user_data or not user_data.get('is_admin'):
        flash('Доступ заборонено!', 'danger')
        return redirect(url_for('index'))

    # Знаходимо страву за її ID
    item = next((i for i in елементи if i.id == item_id), None)
    if not item:
        flash('Страву не знайдено!', 'danger')
        return redirect(url_for('menu_check'))

    if request.method == 'POST':
        # Оновлюємо дані
        item.name = request.form.get('name')
        item.description = request.form.get('description')

        # Обробка ціни з перевіркою на число
        try:
            item.price = float(request.form.get('price'))
        except (ValueError, TypeError):
            pass

        item.weight = request.form.get('weight')
        item.composition = request.form.get('composition')
        item.category = request.form.get('category')
        item.file_name = request.form.get('file_name')

        # Обробка чекбокса "Активна страва"
        # Чекбокс надсилає 'on', якщо він відмічений, і нічого, якщо ні
        item.is_active = True if request.form.get('is_active') == 'on' else False

        flash(f'Страву "{item.name}" успішно оновлено!', 'success')
        return redirect(url_for('menu_check'))

    # Якщо GET-запит, просто показуємо сторінку редагування
    return render_template('edit_item.html', item=item)


@app.route('/cart')
def cart():
    cart_data = session.get('cart', {})
    items_in_cart = []
    total_price = 0

    for item_id, quantity in list(cart_data.items()):
        item = next((i for i in елементи if str(i.id) == str(item_id)), None)
        if item:
            item_total = item.price * quantity
            total_price += item_total
            items_in_cart.append({
                'item': item,
                'quantity': quantity,
                'total_price': item_total
            })

    return render_template('cart.html', items=items_in_cart, total_price=total_price)


@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    cart = session.get('cart', {})
    str_id = str(item_id)
    current_qty = cart.get(str_id, 0)

    if current_qty < 10:
        cart[str_id] = current_qty + 1
        flash('Страва додана до кошика!', 'success')
    else:
        flash('Максимальна кількість однієї страви — 10 шт.', 'warning')

    session['cart'] = cart
    session.modified = True
    return redirect(request.referrer or url_for('menu'))


@app.route('/cart/update/<int:item_id>/<string:action>', methods=['GET', 'POST'])
@app.route('/cart/update/<int:item_id>', methods=['GET', 'POST'])
def update_cart_quantity(item_id, action=None):
    cart = session.get('cart', {})
    str_id = str(item_id)

    if not action:
        action = request.form.get('action')

    if str_id in cart:
        if action == 'increase':
            if cart[str_id] < 10:
                cart[str_id] += 1
            else:
                flash('Максимальна кількість однієї страви — 10 шт.', 'warning')
        elif action == 'decrease':
            if cart[str_id] > 1:
                cart[str_id] -= 1
            else:
                del cart[str_id]
                flash('Страва видалена з кошика.', 'info')

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:item_id>', methods=['GET', 'POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    str_id = str(item_id)

    if str_id in cart:
        del cart[str_id]
        session['cart'] = cart
        session.modified = True
        flash('Страва видалена з кошика.', 'info')

    return redirect(url_for('cart'))

@app.route('/make_order', methods=['GET', 'POST'])
def make_order():
    cart_data = session.get('cart', {})
    if not cart_data:
        flash('Ваш кошик порожній!', 'warning')
        return redirect(url_for('menu'))

    # Визначаємо ім'я поточного користувача через сесію або клас User
    user_data = session.get('user')
    if isinstance(user_data, dict):
        username = user_data.get('nickname') or user_data.get('name') or user_data.get('login') or 'Гість'
    else:
        username = 'Гість'

    order_items = []
    total_price = 0
    for item_id, quantity in cart_data.items():
        # Шукаємо страву у вашому списку `елементи` (або `items` залежно від того, як названа глобальна змінна списку страв)
        item = next((i for i in елементи if str(i.id) == str(item_id)), None)
        if item:
            item_total = item.price * quantity
            total_price += item_total
            order_items.append({
                'name': item.name,
                'price': item.price,
                'count': quantity,
                'total': item_total
            })

    new_order_id = len(global_orders) + 1
    order_time_str = datetime.now().strftime('%d.%m.%Y %H:%M')

    new_order = {
        'id': new_order_id,
        'user_name': username,
        'order_time': order_time_str,
        'order_list': order_items,
        'total_price': total_price,
        'status': 'В обробці'
    }

    global_orders.append(new_order)
    session.pop('cart', None)
    session.modified = True

    # --- ВИКОРИСТОВУЄМО ВАШУ ФУНКЦІЮ ДЛЯ TELEGRAM ---
    send_telegram_notification(new_order)
    # -----------------------------------------------

    flash(f'Замовлення #{new_order_id} успішно створено!', 'success')
    return redirect(url_for('my_history'))


@app.route('/my_history', endpoint='my_history')
def user_history_page():
    user_data = session.get('user')
    if not user_data:
        flash('Будь ласка, увійдіть у систему.', 'warning')
        return redirect(url_for('index'))

    # Визначаємо ім'я користувача
    if isinstance(user_data, dict):
        username = user_data.get('nickname') or user_data.get('name') or user_data.get('login') or 'Гість'
    else:
        username = 'Гість'

    # Фільтруємо замовлення та бронювання для поточного користувача
    my_orders = [o for o in global_orders if o.get('user_name') == username]
    my_res = [r for r in global_reservations if r.get('name') == username]

    return render_template('my_history.html', orders=my_orders, reservations=my_res)

@app.route('/my_orders')
def my_orders():
    orders = session.get('orders', [])
    return render_template('my_orders.html', orders=orders)


@app.route('/my_order/<int:id>')
def my_order(id):
    orders = session.get('orders', [])
    order = next((o for o in orders if o['id'] == id), None)

    if not order:
        flash('Замовлення не знайдено!', 'danger')
        return redirect(url_for('my_orders'))

    return render_template('my_order.html', order=order)


@app.route('/delete_order/<int:id>')
def delete_order(id):
    orders = session.get('orders', [])
    updated_orders = [o for o in orders if o['id'] != id]

    if len(orders) == len(updated_orders):
        flash('Замовлення не знайдено!', 'danger')
    else:
        session['orders'] = updated_orders
        session.modified = True
        flash(f'Замовлення #{id} успішно скасовано та видалено!', 'success')

    return redirect(url_for('my_orders'))


@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        date = request.form.get('date')
        time = request.form.get('time')
        guests = request.form.get('guests')

        res_entry = {
            'id': len(global_reservations) + 1,
            'name': name,
            'phone': phone,
            'date': date,
            'time': time,
            'guests': guests,
            'status': 'Підтверджено',
            'created_at': datetime.now().strftime('%d.%m.%Y %H:%M')
        }

        reservations = session.get('reservations', [])
        reservations.append(res_entry)
        session['reservations'] = reservations
        global_reservations.append(res_entry)
        session.modified = True

        send_telegram_reservation_notification(res_entry)

        flash(f'Столик успішно заброньовано на {date} о {time}!', 'success')
        return redirect(url_for('reservation'))

    user_reservations = session.get('reservations', [])
    return render_template('reservation.html', reservations=user_reservations)


@app.route('/login', methods=['GET', 'POST'])
def login():
    redirect_url = request.form.get('next') or request.referrer or url_for('index')

    if request.method == 'POST':
        email_or_nickname = (
                request.form.get('login') or
                request.form.get('email') or
                request.form.get('username') or ''
        ).strip()

        password = request.form.get('password', '').strip()

        user = next(
            (u for u in users_db if (
                    u.email.lower() == email_or_nickname.lower() or
                    u.nickname.lower() == email_or_nickname.lower()
            ) and u.password == password),
            None
        )

        if user:
            session.pop('show_auth_modal', None)
            session['user'] = {
                'id': user.id,
                'nickname': user.nickname,
                'email': user.email,
                'role': user.role,
                'is_admin': user.is_admin
            }
            flash(f'Вітаємо, {user.nickname}!', 'success')
            return redirect(redirect_url)
        else:
            session['show_auth_modal'] = True
            session['auth_tab'] = 'login'
            flash('Невірний e-mail / логін або пароль!', 'danger')
            return redirect(redirect_url)

    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    redirect_url = request.form.get('next') or request.referrer or url_for('index')

    if request.method == 'POST':
        nickname = (request.form.get('nickname') or '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not nickname or not email or not password:
            session['show_auth_modal'] = True
            session['auth_tab'] = 'register'
            flash('Будь ласка, заповніть всі поля!', 'warning')
            return redirect(redirect_url)

        existing_user = next(
            (u for u in users_db if u.email.lower() == email.lower() or u.nickname.lower() == nickname.lower()),
            None
        )
        if existing_user:
            session['show_auth_modal'] = True
            session['auth_tab'] = 'register'
            flash('Користувач з таким email або нікнеймом вже існує!', 'warning')
            return redirect(redirect_url)

        new_id = max([u.id for u in users_db], default=0) + 1
        new_user = User(new_id, nickname, email, role='Клієнт', is_admin=False, password=password)
        users_db.append(new_user)

        session.pop('show_auth_modal', None)
        session['user'] = {
            'id': new_user.id,
            'nickname': new_user.nickname,
            'email': new_user.email,
            'role': new_user.role,
            'is_admin': new_user.is_admin
        }
        flash('Реєстрація успішна! Ласкаво просимо.', 'success')
        return redirect(redirect_url)

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Ви вийшли з акаунта.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)