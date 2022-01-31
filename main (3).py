import logging
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    Filters,
    CallbackQueryHandler,
    ShippingQueryHandler,
    PreCheckoutQueryHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)

BOT_TOKEN = ""
PAYMENT_TOKEN = ""

MAIN, MENU, CART, ACTIONS, MENU_SHOW = range(5)

PRODUCTS = {
    "Шаурма": [
        {
            "id": 1,
            "name": "Шаурма из курицы в лаваше",
            "description": "Лаваш, мясо курицы, огурец, помидор, морковь, свекла, картофель, аджика, соус от шефа",
            "image": "https://cafesahara.ru/upload/resize_cache/iblock/850/1200_1200_1/8509bac28e2282daec8de13ad34ae8f5.jpg",
            "price": "10",
        },
        {
            "id": 2,
            "name": " Шаурма из телятины в лаваше",
            "description": "Лаваш, мясо телятины, огурец, помидор, морковь, свекла, аджика, соус от шефа",
            "image": "https://cafesahara.ru/upload/resize_cache/iblock/9f6/1200_1200_1/9f60fb8ba4bacefa841162a2bcd80dc6.jpg",
            "price": "10",
        },
        {
            "id": 7,
            "name": " Шаурма из телятины в лаваше",
            "description": "Лаваш, мясо телятины, огурец, помидор, морковь, свекла, аджика, соус от шефа",
            "image": "https://cafesahara.ru/upload/resize_cache/iblock/9f6/1200_1200_1/9f60fb8ba4bacefa841162a2bcd80dc6.jpg",
            "price": "10",
        },
    ],
    "Люля-кебаб": [
        {
            "id": 3,
            "name": "Люля-кебаб из осетрины",
            "description": "Фарш осетрины, морковь по-корейски, лук",
            "image": "https://cafesahara.ru/upload/resize_cache/iblock/c96/1200_1200_1/c96448c15a9bc6f2226a25bba5b0ed41.jpg",
            "price": "10",
        },
        {
            "id": 4,
            "name": "Люля-кебаб из утки",
            "description": "Утиный фарш, лук, морковь по-корейски",
            "image": "https://cafesahara.ru/upload/resize_cache/iblock/6d6/1200_1200_1/6d619e4da86de7815877ecb23c7809bd.jpg",
            "price": "10",
        },
    ],
    "Напитки": [
        {
            "id": 5,
            "name": "Кола",
            "image": "https://cafesahara.ru/upload/iblock/b8c/b8cd5a1c5b86ba419772e0422f59ee4a.jpg",
            "price": "10",
        },
        {
            "id": 6,
            "name": "Спрайт",
            "image": "https://cafesahara.ru/upload/iblock/fec/fecae63f380a57b682a1ccab8943f2f2.jpg",
            "price": "10",
        },
    ],
}

PRODUCTS_BY_ID = {p["id"]: {**p, "type": c} for c in PRODUCTS for p in PRODUCTS[c]}

CART_DATA = {}


def menu(update, context):
    keyboard = [
        [KeyboardButton(x) for x in PRODUCTS],
        [
            KeyboardButton("Назад"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Наше меню", reply_markup=reply_markup)
    return MENU


def menu_show(update, context):
    type_ = update.message.text
    for p in PRODUCTS.get(type_, []):
        keyboard = [
            [
                InlineKeyboardButton("Добавить в корзину", callback_data=f'{p["id"]}'),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_photo(
            p["image"],
            caption=p["name"]
            + "\n\n"
            + p.get("description", "")
            + "\n\nЦена: "
            + p["price"],
            reply_markup=reply_markup,
        )
    update.message.reply_text(
        "Делайте ваш заказ",
        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("Назад"),
                ]
            ],
            resize_keyboard=True,
        ),
    )
    return MENU_SHOW


def add_to_cart(update, context):
    query = update.callback_query
    query.answer()
    CART_DATA[query.from_user.id] = CART_DATA.get(query.from_user.id, [])
    CART_DATA[query.from_user.id].append(query.data)
    return MENU_SHOW


def delete_from_cart(update, context):
    query = update.callback_query
    query.answer()
    CART_DATA[query.from_user.id].remove(query.data)
    query.delete_message()
    return CART


def cart(update, context):
    message = [
        PRODUCTS_BY_ID[int(p)] for p in CART_DATA.get(update.message.from_user.id, [])
    ]
    price = sum([int(p["price"]) for p in message])

    text = f"Сумма: {price}" if message else "Корзина пуста"
    for p in message:
        keyboard = [
            [
                InlineKeyboardButton("Удалить", callback_data=f'{p["id"]}'),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(p["name"], reply_markup=reply_markup)

    keyboard = [
        [
            KeyboardButton("Оплатить"),
            KeyboardButton("Очистить"),
        ],
        [
            KeyboardButton("Назад"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(text, reply_markup=reply_markup)
    return CART


def checkout(update, context):
    message = [
        PRODUCTS_BY_ID[int(p)] for p in CART_DATA.get(update.message.from_user.id, [])
    ]
    price = sum([int(p["price"]) for p in message])

    chat_id = update.message.chat_id
    title = "Оплата заказа"
    description = "\n".join([p["name"] for p in message])
    payload = "Custom-Payload"
    currency = "USD"
    prices = [LabeledPrice("Оплатить", price * 100)]
    context.bot.send_invoice(
        chat_id,
        title,
        description,
        payload,
        PAYMENT_TOKEN,
        currency,
        prices,
        need_name=True,
        need_phone_number=True,
        need_email=False,
        is_flexible=True,
    )
    return CART


def precheckout(update, context):
    query = update.pre_checkout_query
    query.answer(ok=True)
    return CART


def shipping(update, context):
    query = update.shipping_query
    query.answer(ok=True)
    return CART


def successful_payment(update, context):
    update.message.reply_text("Ваш заказ принят. Спасибо")
    return MAIN


def clear(update, context):
    CART_DATA.get(update.message.from_user.id, []).clear()
    update.message.reply_text("Корзина очищена")
    return CART


def actions(update, context):
    keyboard = [
        [
            KeyboardButton("Назад"),
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Акции", reply_markup=reply_markup)
    return ACTIONS


def start(update, context):
    keyboard = [
        [
            KeyboardButton("Меню"),
            KeyboardButton("Корзина"),
            KeyboardButton("Акции"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Вас приветствует кафе Метраж\n"
        "Воспользуйтесь клавиатурой внизу чтобы сделать свой заказ",
        reply_markup=reply_markup,
    )
    return MAIN


def main():
    updater = Updater(BOT_TOKEN)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [
                MessageHandler(Filters.regex("Меню"), menu),
                MessageHandler(Filters.regex("Корзина"), cart),
                MessageHandler(Filters.regex("Акции"), actions),
            ],
            MENU: [
                MessageHandler(Filters.regex("Назад"), start),
                MessageHandler(
                    Filters.regex(f"({'|'.join(PRODUCTS.keys())})"), menu_show
                ),
            ],
            CART: [
                MessageHandler(Filters.regex("Назад"), start),
                MessageHandler(Filters.regex("Оплатить"), checkout),
                MessageHandler(Filters.regex("Очистить"), clear),
                CallbackQueryHandler(delete_from_cart),
                ShippingQueryHandler(shipping),
                PreCheckoutQueryHandler(precheckout),
                MessageHandler(Filters.successful_payment, successful_payment),
            ],
            ACTIONS: [
                MessageHandler(Filters.regex("Назад"), start),
            ],
            MENU_SHOW: [
                CallbackQueryHandler(add_to_cart),
                MessageHandler(Filters.regex("Назад"), menu),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
