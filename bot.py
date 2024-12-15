from aiogram import Bot, Dispatcher, Router
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton

from loader import BOT_TOKEN, MERCHANT_DOMAIN, db

from functions import add_user_to_channel, check_user_in_subs

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.chat_join_request()
async def handle_join_request(chat_join_request: ChatJoinRequest):
    try:
        chat_id = chat_join_request.chat.id
        user_id = int(chat_join_request.from_user.id)
        username = chat_join_request.from_user.username
        first_name = chat_join_request.from_user.first_name

        print(f"Обробка запиту на приєднання користувача: {user_id}")

        if check_user_in_subs(user_id):
            print(f"Користувач {user_id} має підписку. Додаємо в канал.")
            add_user_to_channel(user_id)
        else:
            print(f"Користувач {user_id} не має підписки. Надсилаємо посилання на оплату.")
            await send_payment_link(user_id)

        add_user_to_database(user_id, username, first_name)
    except Exception as e:
        print(f"Помилка при обробці запиту на приєднання користувача {user_id}: {e}")
        print(f"Трасування помилки: {e}")


async def send_payment_link(user_id):
    text = (
        "Вітаю! 🤍Я адміністратор закритого каналу FestiveLookbook від Світлани Косовської."
        "Після оплати ви отримаєте доступ до наших святкових образів і вашого натхнення."
        "Чекаємо на вас у нашій спільноті!\n\n"
        "<a href='https://umovivikoristanyafestiveoutfit.my.canva.site'>Умови використання</a>\n"
        "<a href='https://umovivikoristanyafestiveoutfit.my.canva.site/1-1-1-tessslegram-lookbook-daily'>Договір оферти</a>\n"
        "<a href='https://umovivikoristanyafestiveoutfit.my.canva.site/festivelookboosk-pdf'>Політика конфіденційності</a>\n"
        "<a href='https://umovivikoristanyafestiveoutfit.my.canva.site/lookbook-sssdaily-1-1-1-lookbook-1-2'>Політика повернення</a>"
    )
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатити", url=f"{MERCHANT_DOMAIN}/pay/{user_id}")]
        ]
    )
    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=reply_markup)
        print(f"Посилання на оплату надіслано користувачу {user_id}")
    except Exception as e:
        print(f"Помилка при надсиланні посилання на оплату користувачу {user_id}: {e}")


def add_user_to_database(user_id, username, first_name):
    try:
        if not db.user_exists(user_id):
            print(f"Користувач {user_id} не існує в базі. Додаємо користувача.")
            db.add_user(user_id, username, first_name)
        else:
            print(f"Користувач {user_id} вже існує в базі.")
    except Exception as e:
        print(f"Помилка при додаванні користувача {user_id} в базу: {e}")





async def main():
    await dp.start_polling(bot)


dp.include_router(router)


if __name__ == '__main__':
    import asyncio
    print("Bot started")
    asyncio.run(main())
