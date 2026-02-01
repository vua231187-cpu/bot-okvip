import telebot
import sqlite3
from telebot import types

# ========= CONFIG =========
buy_state = {}
admin_add_mode = {}
pending_deposits = {}

BOT_TOKEN = "8327784731:AAFmxn2OfgAK9hMIKgVLs3acbvjkgRDCrOs"
ADMIN_IDS = [6500271609]  # thay bằng ID telegram admin
ACC_PRICE = 5000
MIN_DEPOSIT = 20000
ADMIN_SUPPORT = "@cskhokvip117"

bot = telebot.TeleBot(BOT_TOKEN)

# ========= DATABASE =========
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    total_deposit INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    sold INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    user_id INTEGER,
    username TEXT,
    time TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    user_id INTEGER,
    amount INTEGER,
    time TEXT
)
""")

conn.commit()

# ========= MENU =========
def user_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Mua acc OKVIP")
    kb.add("💰 Nạp tiền")
    kb.add("📜 Lịch sử mua acc")
    kb.add("📥 Lịch sử nạp tiền")
    kb.add("🔐 Thuê OTP")
    kb.add("ℹ️ Thông tin")
    kb.add("🆘 Hỗ trợ")
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅️ Quay lại")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add acc OKVIP", "💳 Duyệt nạp tiền")
    kb.row("🔙 Quay lại admin")
    return kb

# ========= START =========
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id

    cur.execute(
        "INSERT OR IGNORE INTO users(user_id, balance, total_deposit) VALUES (?, 0, 0)",
        (uid,)
    )
    conn.commit()

    bot.send_message(
        message.chat.id,
        "🎉 Chào mừng đến với bot bán acc OKVIP",
        reply_markup=user_menu()
    )

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Bạn không có quyền admin")
        return

    bot.send_message(
        message.chat.id,
        "👮 ADMIN PANEL",
        reply_markup=admin_menu()
    )

# ========= MUA ACC =========
@bot.message_handler(func=lambda m: m.text == "🛒 Mua acc OKVIP")
def buy_acc(message):
    buy_state[message.from_user.id] = True

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Xác nhận mua", "❌ Hủy")
    kb.row("🔙 Quay lại")

    bot.send_message(
        message.chat.id,
        f"🛒 MUA ACC OKVIP\n\n💰 Giá: {ACC_PRICE} VND\n\n⚠️ Bấm Xác nhận để mua",
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == "✅ Xác nhận mua")
def confirm_buy(message):
    uid = message.from_user.id

    if uid not in buy_state:
        bot.send_message(
            message.chat.id,
            "❌ Bạn chưa chọn mua acc",
            reply_markup=user_menu()
        )
        return

    buy_state.pop(uid, None)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]

    if balance < ACC_PRICE:
        bot.send_message(message.chat.id, "❌ Số dư không đủ", reply_markup=user_menu())
        return

    cur.execute("SELECT id, username, password FROM accounts WHERE sold=0 LIMIT 1")
    acc = cur.fetchone()

    if not acc:
        bot.send_message(message.chat.id, "❌ Hết acc", reply_markup=user_menu())
        return

    acc_id, u, p = acc

    cur.execute("UPDATE accounts SET sold=1 WHERE id=?", (acc_id,))
    cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (ACC_PRICE, uid))
    cur.execute("INSERT INTO purchases VALUES (?, ?, datetime('now'))", (uid, u))
    conn.commit()

    bot.send_message(
        message.chat.id,
        f"✅ MUA THÀNH CÔNG\n\n👤 {u}\n🔑 {p}",
        reply_markup=user_menu()
    )

@bot.message_handler(func=lambda m: m.text == "➕ Add acc OKVIP")
def add_acc(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    admin_add_mode[message.from_user.id] = True

    bot.send_message(
        message.chat.id,
        "➕ ADD ACC OKVIP\n\nGửi theo dạng:\nuser|pass",
        reply_markup=back_kb()
    )
@bot.message_handler(func=lambda m: m.text == "❌ Hủy")
def cancel_buy(message):
    buy_state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "❌ Đã hủy mua", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.from_user.id in admin_add_mode and "|" in m.text)
def save_acc(message):
    if message.text == "⬅️ Quay lại":
        admin_add_mode.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "🔙 Admin menu", reply_markup=admin_menu())
        return

    try:
        user, pwd = message.text.split("|", 1)
        cur.execute(
            "INSERT INTO accounts(username, password) VALUES (?, ?)",
            (user.strip(), pwd.strip())
        )
        conn.commit()

        bot.send_message(message.chat.id, "✅ Đã thêm acc", reply_markup=admin_menu())
        admin_add_mode.pop(message.from_user.id, None)

    except:
        bot.send_message(message.chat.id, "❌ Sai định dạng, đúng là: user|pass")

# ========= NẠP TIỀN =========
@bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
def deposit_menu(message):
    uid = message.from_user.id
    pending_deposits[uid] = True

    text = (
        "💰 NẠP TIỀN\n\n"
        "📌 Quét mã QR admin để chuyển khoản\n"
        "📌 Nội dung chuyển khoản:\n"
        f"NAP {uid}\n\n"
        "⚠️ Lưu ý:\n"
        "– Nhập đúng nội dung để được duyệt nhanh\n"
        "– Nạp tối thiểu: 20000đ\n\n"
        "⏳ Sau khi chuyển xong, bấm nút bên dưới"
    )

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Tôi đã nạp tiền")
    kb.add("⬅️ Quay lại")

    # BÓNG CHAT 1: NỘI DUNG
    bot.send_message(message.chat.id, text, reply_markup=kb)

    # BÓNG CHAT 2: ẢNH QR ADMIN
    try:
        with open("qr_admin.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo)
    except:
        bot.send_message(
            message.chat.id,
            "⚠️ QR hiện đang lỗi\n"
            "Vui lòng liên hệ CSKH để nạp tiền\n"
            "👉 @cskhokvip117"
        )

@bot.message_handler(func=lambda m: m.text == "✅ Tôi đã nạp tiền")
def user_confirm_deposit(message):
    uid = message.from_user.id

    if uid not in pending_deposits:
        bot.send_message(
            message.chat.id,
            "❌ Bạn chưa tạo yêu cầu nạp tiền",
            reply_markup=user_menu()
        )
        return

    # Thông báo cho user
    bot.send_message(
        message.chat.id,
        "⏳ Đã ghi nhận yêu cầu nạp tiền\nVui lòng chờ admin duyệt 💳",
        reply_markup=user_menu()
    )

    # Thông báo cho admin
    for admin_id in ADMIN_IDS:
        bot.send_message(
            admin_id,
            f"💰 YÊU CẦU NẠP TIỀN\n\n"
            f"👤 User ID: {uid}\n"
            f"📌 Nội dung CK: NAP {uid}\n\n"
            f"Duyệt bằng:\n/duyet {uid} <số_tiền>"
        )

@bot.message_handler(commands=["duyet"])
def approve_deposit(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)

        if amount < MIN_DEPOSIT:
            bot.send_message(
                message.chat.id,
                f"❌ Số tiền tối thiểu là {MIN_DEPOSIT}đ"
            )
            return

        cur.execute(
            "UPDATE users SET balance = balance + ?, total_deposit = total_deposit + ? WHERE user_id = ?",
            (amount, amount, uid)
        )
        cur.execute(
            "INSERT INTO deposits VALUES (?, ?, datetime('now'))",
            (uid, amount)
        )
        conn.commit()

        pending_deposits.pop(uid, None)

        bot.send_message(message.chat.id, "✅ Duyệt nạp thành công")
        bot.send_message(
            uid,
            f"✅ Nạp thành công {amount}đ",
            reply_markup=user_menu()
        )

    except:
        bot.send_message(
            message.chat.id,
            "❌ Sai cú pháp\nVD: /duyet 123456789 20000"
        )

# =========LỊCH SỬ MUA HÀNG ======
@bot.message_handler(func=lambda m: m.text == "📜 Lịch sử mua acc")
def history_buy(message):
    uid = message.from_user.id

    cur.execute(
        "SELECT username, time FROM purchases WHERE user_id=? ORDER BY time DESC",
        (uid,)
    )
    rows = cur.fetchall()

    if not rows:
        bot.send_message(
            message.chat.id,
            "📭 Bạn chưa mua acc nào",
            reply_markup=back_kb()
        )
        return

    text = "📜 LỊCH SỬ MUA ACC\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. 👤 {row[0]}\n⏰ {row[1]}\n\n"

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_kb()
    )

# ========= LỊCH SỬ NẠP =========
@bot.message_handler(func=lambda m: m.text == "📥 Lịch sử nạp tiền")
def history_deposit(message):
    uid = message.from_user.id
    cur.execute(
        "SELECT amount, time FROM deposits WHERE user_id=? ORDER BY time DESC LIMIT 5",
        (uid,)
    )
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Chưa có giao dịch nạp", reply_markup=back_kb())
        return

    text = "📥 LỊCH SỬ NẠP TIỀN (5 GẦN NHẤT)\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. {r[0]} VND | {r[1]}\n"

    bot.send_message(message.chat.id, text, reply_markup=back_kb())

# ========= THUÊ OTP =========
@bot.message_handler(func=lambda m: m.text == "🔐 Thuê OTP")
def otp(message):
    bot.send_message(
        message.chat.id,
        "📱 THUÊ OTP\n\n(Đang cập nhật)",
        reply_markup=back_kb()
    )

# ========= THÔNG TIN =========
@bot.message_handler(func=lambda m: m.text == "ℹ️ Thông tin")
def info(message):
    uid = message.from_user.id

    cur.execute("SELECT balance, total_deposit FROM users WHERE user_id=?", (uid,))
    balance, total = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM purchases WHERE user_id=?", (uid,))
    total_acc = cur.fetchone()[0]

    text = (
        "ℹ️ THÔNG TIN TÀI KHOẢN\n\n"
        f"🆔 ID Telegram: `{uid}`\n"
        f"💰 Số dư: {balance} VND\n"
        f"🛒 Số acc đã mua: {total_acc}\n"
        f"💳 Tổng tiền nạp: {total} VND"
    )

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=back_kb())

# ========= HỖ TRỢ =========
@bot.message_handler(func=lambda m: m.text == "🆘 Hỗ trợ")
def support(message):
    bot.send_message(
        message.chat.id,
        f"🆘 HỖ TRỢ\n👉 Liên hệ admin {ADMIN_SUPPORT}",
        reply_markup=back_kb()
    )

# ========= QUAY LẠI =========
@bot.message_handler(func=lambda m: m.text == "🔙 Quay lại")
def back(message):
    bot.send_message(message.chat.id, "⬅️ Menu chính", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "⬅️ Quay lại")
def back_to_menu(message):
    bot.send_message(
        message.chat.id,
        "🏠 Menu chính",
        reply_markup=user_menu()
    )

# ========= RUN =========
@bot.message_handler(func=lambda m: m.text == "⬅️ Quay lại")
def back_to_menu(message):
    admin_add_mode.pop(message.from_user.id, None)
    buy_state.pop(message.from_user.id, None)
    pending_deposits.pop(message.from_user.id, None)

    bot.send_message(
        message.chat.id,
        "🏠 Menu chính",
        reply_markup=user_menu()
    )

bot.infinity_polling()
