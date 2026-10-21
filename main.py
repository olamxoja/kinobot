import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# --- SOZLAMALAR ---
TOKEN = "8607847701:AAG7eq3ggyzso5u9_mqqtobDrnSGE0Olg2k"
ADMIN_ID = 7063407927  # O'z Telegram ID raqamingiz
KANAL_ID = -1004481075596  # Kino kanalingiz ID si
# ------------------

bot = Bot(TOKEN)
dp = Dispatcher()


# Ma'lumotlar bazasini yaratish funksiyasi
def init_db():
    db = sqlite3.connect("kino2.db")
    db.execute(
        "CREATE TABLE IF NOT EXISTS kinolar "
        "(kod INTEGER PRIMARY KEY, nomi TEXT, msg_id INTEGER)"
    )
    db.commit()
    db.close()


# Bot ishga tushganda bazani yaratib olamiz
init_db()


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "Salom! 🎬 Kino botiga xush kelibsiz.\n\n"
        "Kino kodini yuboring yoki kino nomidan qism yozib qidiring."
    )


# Kanalga video tashlanganda avtomatik bazaga qo'shish
@dp.channel_post(F.chat.id == KANAL_ID, F.video | F.document)
async def kanal_kino(m: Message):
    db = sqlite3.connect("kino2.db")
    qismlar = (m.caption or "").strip().split(maxsplit=1)

    if qismlar and qismlar[0].isdigit():
        kod = int(qismlar[0])
        nomi = qismlar[1] if len(qismlar) > 1 else f"Kino {kod}"
    else:
        eng_katta = db.execute("SELECT MAX(kod) FROM kinolar").fetchone()[0]
        kod = (eng_katta or 0) + 1
        nomi = " ".join(qismlar) or f"Kino {kod}"

    db.execute(
        "INSERT OR REPLACE INTO kinolar (kod, nomi, msg_id) VALUES (?, ?, ?)",
        (kod, nomi, m.message_id),
    )
    db.commit()
    db.close()

    await bot.send_message(ADMIN_ID, f"✅ Yangi kino saqlandi!\n\nKod: {kod}\nNomi: {nomi}")


# Admin uchun kinolar ro'yxati
@dp.message(Command("list"), F.from_user.id == ADMIN_ID)
async def royxat(m: Message):
    db = sqlite3.connect("kino2.db")
    qatorlar = db.execute("SELECT kod, nomi FROM kinolar ORDER BY kod").fetchall()
    db.close()

    if not qatorlar:
        await m.answer("Hali bazada kinolar yo'q.")
        return

    matn = "\n".join(f"{k} — {n}" for k, n in qatorlar)
    for i in range(0, len(matn), 4000):
        await m.answer(matn[i:i + 4000])


# Admin uchun kinoni o'chirish: /del 1
@dp.message(Command("del"), F.from_user.id == ADMIN_ID)
async def ochir(m: Message):
    qismlar = m.text.split()
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await m.answer("Ishlatish uchun namuna: /del 1", parse_mode="Markdown")
        return

    db = sqlite3.connect("kino2.db")
    db.execute("DELETE FROM kinolar WHERE kod = ?", (int(qismlar[1]),))
    db.commit()
    db.close()

    await m.answer("🗑 Kino bazadan muvaffaqiyatli o'chirildi.")


# Foydalanuvchi kod yuborganda yoki kino nomini yozganda
@dp.message(F.text)
async def kino(m: Message):
    matn = m.text.strip()
    db = sqlite3.connect("kino2.db")

    # Agar raqam (kod) kiritilgan bo'lsa
    if matn.isdigit():
        qator = db.execute(
            "SELECT nomi, msg_id FROM kinolar WHERE kod = ?", (int(matn),)
        ).fetchone()
        db.close()

        if qator:
            try:
                await bot.copy_message(
                    chat_id=m.chat.id,
                    from_chat_id=KANAL_ID,
                    message_id=qator[1],
                    caption=f"🎬 Kino: {qator[0]}",
                )
            except Exception as e:
                await m.answer("❌ Videoni yuborishda xatolik! Bot kanalga to'liq huquqli admin ekanligini tekshiring.")
                print(f"Xatolik tafsiloti: {e}")
        else:
            await m.answer("❌ Bunday kodli kino topilmadi.")
        return

    # Agar harf (nomi) kiritilgan bo'lsa qidirish
    topildi = db.execute(
        "SELECT kod, nomi FROM kinolar WHERE nomi LIKE ? LIMIT 10",
        (f"%{matn}%",),
    ).fetchall()
    db.close()

    if topildi:
        javob = "🔍 Topilgan kinolar:\n\n"
        for k, n in topildi:
            javob += f"Kodi: {k} — Nomi: {n}\n"
        javob += "\nKerakli kinoning kodini yuboring:"
        await m.answer(javob, parse_mode="Markdown")
    else:
        await m.answer("❌ Hech qanday kino topilmadi.")


async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())