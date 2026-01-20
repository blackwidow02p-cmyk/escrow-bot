import asyncio
import aiosqlite
import qrcode
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
UPI_ID = os.getenv("UPI_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB = "database.db"

class EscrowForm(StatesGroup):
    buyer = State()
    seller = State()
    currency = State()
    amount = State()

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer TEXT,
            seller TEXT,
            currency TEXT,
            amount TEXT,
            status TEXT
        )
        """)
        await db.commit()

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Create Escrow", callback_data="create_escrow")
    kb.adjust(1)

    await message.answer(
        "🤖 PAGAL Escrow Bot\n\n🛡️ Secure Escrow for INR + Crypto",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "create_escrow")
async def create_escrow(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter Buyer Username:")
    await state.set_state(EscrowForm.buyer)

@dp.message(EscrowForm.buyer)
async def buyer_step(message: Message, state: FSMContext):
    await state.update_data(buyer=message.text)
    await message.answer("Enter Seller Username:")
    await state.set_state(EscrowForm.seller)

@dp.message(EscrowForm.seller)
async def seller_step(message: Message, state: FSMContext):
    await state.update_data(seller=message.text)

    kb = InlineKeyboardBuilder()
    kb.button(text="🇮🇳 INR", callback_data="currency_INR")
    kb.button(text="🪙 CRYPTO", callback_data="currency_CRYPTO")
    kb.adjust(2)

    await message.answer("Choose Escrow Type:", reply_markup=kb.as_markup())
    await state.set_state(EscrowForm.currency)

@dp.callback_query(F.data.startswith("currency_"))
async def currency_step(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    await callback.message.answer("Enter Amount:")
    await state.set_state(EscrowForm.amount)

@dp.message(EscrowForm.amount)
async def amount_step(message: Message, state: FSMContext):
    data = await state.get_data()

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO deals (buyer, seller, currency, amount, status) VALUES (?, ?, ?, ?, ?)",
            (data["buyer"], data["seller"], data["currency"], message.text, "PENDING")
        )
        await db.commit()

    if data["currency"] == "INR":
        text = f"Pay ₹{message.text} to UPI:\n{UPI_ID}"
    else:
        text = f"Send {message.text} USDT to:\nYOUR_CRYPTO_WALLET"

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Release", callback_data="release")

    await message.answer(text, reply_markup=kb.as_markup())
    await state.clear()

@dp.callback_query(F.data == "release")
async def release(callback: CallbackQuery):
    await callback.message.answer("✅ Payment Released. Deal Completed.")
    await callback.answer()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
