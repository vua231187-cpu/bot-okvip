import telebot
import sqlite3
from telebot import types

# ========= CONFIG =========
buy_state = {}  # uid: "confirm_buy"
admin_add_mode = {}
pending_deposits = {}

BOT_TOKEN = "8327784731:AAFmxn2OfgAK9hMIKgVLs3acbvjkgRDCrOs"
ADMIN_IDS = [6500271609]  # thay bằng ID telegram admin
ACC_PRICE = 5000
MIN_DEPOSIT = 20000
ADMIN_SUPPORT = "@cskhokvip117"
import time

deposit_cooldown = {}  # uid: last_request_time
DEPOSIT_SPAM_TIME = 60  # 60 giây mới được gửi lại

bot = telebot.TeleBot(BOT_TOKEN)

# ========= DATABASE =========
def ensure_user(uid):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id, balance, total_deposit) VALUES (?, 0, 0)",
        (uid,)
    )
    conn.commit()
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

# ========= ADMIN UTILS =========
def is_admin(uid):
    return uid in ADMIN_IDS

admin_state = {}  # uid: "add_acc"

# ========= ADMIN MENU =========
def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Thêm acc", "📦 Kho acc")
    kb.row("💰 Cộng tiền", "➖ Trừ tiền")
    kb.row("📊 Thống kê")
    kb.add("⬅️ Thoát admin")
    return kb

@bot.message_handler(commands=["admin"])
def admin_start(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Bạn không có quyền admin")
        return

    bot.send_message(
        message.chat.id,
        "👑 ADMIN PANEL",
        reply_markup=admin_kb()
    )

# ========= ADD ACC =========
@bot.message_handler(func=lambda m: m.text == "➕ Thêm acc" and is_admin(m.from_user.id))
def admin_add_acc(message):
    admin_state[message.from_user.id] = "add_acc"
    bot.send_message(
        message.chat.id,
        "➕ THÊM ACC\nGửi theo dạng:\nuser|pass\n\nGửi ⬅️ để hủy"
    )

@bot.message_handler(func=lambda m: admin_state.get(m.from_user.id) == "add_acc")
def admin_save_acc(message):
    if message.text == "⬅️ Thoát admin":
        admin_state.pop(message.from_user.id, None)
        return

    if "|" not in message.text:
        bot.send_message(message.chat.id, "❌ Sai định dạng user|pass")
        return

    u, p = message.text.split("|", 1)
    cur.execute(
        "INSERT INTO accounts(username, password) VALUES (?, ?)",
        (u.strip(), p.strip())
    )
    conn.commit()

    admin_state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ Đã thêm acc", reply_markup=admin_kb())

# ========= KHO ACC =========
@bot.message_handler(func=lambda m: m.text == "📦 Kho acc" and is_admin(m.from_user.id))
def admin_stock(message):
    cur.execute("SELECT COUNT(*) FROM accounts WHERE sold=0")
    total = cur.fetchone()[0]
    bot.send_message(message.chat.id, f"📦 Acc chưa bán: {total}")

# ========= CỘNG / TRỪ TIỀN =========
@bot.message_handler(commands=["cong"])
def admin_add_money(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        ensure_user(uid)

        cur.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, uid)
        )
        conn.commit()

        bot.send_message(message.chat.id, "✅ Đã cộng tiền")
        bot.send_message(uid, f"💰 Bạn được cộng {amount}đ", reply_markup=user_menu())
    except:
        bot.send_message(message.chat.id, "❌ Dùng: /cong user_id số_tiền")

@bot.message_handler(commands=["tru"])
def admin_minus_money(message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        ensure_user(uid)

        cur.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id=?",
            (amount, uid)
        )
        conn.commit()

        bot.send_message(message.chat.id, "✅ Đã trừ tiền")
    except:
        bot.send_message(message.chat.id, "❌ Dùng: /tru user_id số_tiền")

# ========= THỐNG KÊ =========
@bot.message_handler(commands=["stats"])
def admin_stats(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT SUM(total_deposit) FROM users")
    total = cur.fetchone()[0] or 0

    bot.send_message(
        message.chat.id,
        f"📊 THỐNG KÊ\n"
        f"👥 User: {users}\n"
        f"💰 Tổng nạp: {total:,}đ"
    )

# ========= THOÁT ADMIN =========
@bot.message_handler(func=lambda m: m.text == "⬅️ Thoát admin")
def admin_exit(message):
    admin_state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "🏠 Menu user", reply_markup=user_menu())


# ========= MUA ACC =========
@bot.message_handler(func=lambda m: m.text == "🛒 Mua acc OKVIP")
def buy_acc(message):
    uid = message.from_user.id
    buy_state[uid] = "confirm_buy"

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Xác nhận mua", "❌ Hủy")
    kb.add("⬅️ Quay lại")

    bot.send_message(
        message.chat.id,
        f"🛒 MUA ACC OKVIP\n\n💰 Giá: {ACC_PRICE} VND\n\n⚠️ Bấm Xác nhận để mua",
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == "✅ Xác nhận mua")
def confirm_buy(message):
    uid = message.from_user.id

    if buy_state.get(uid) != "confirm_buy":
        bot.send_message(
            message.chat.id,
            "❌ Phiên mua không hợp lệ\nVui lòng mua lại từ đầu",
            reply_markup=user_menu()
        )
        return

    # XÓA STATE NGAY SAU KHI KIỂM TRA
    buy_state.pop(uid, None)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if not row or row[0] < ACC_PRICE:
        bot.send_message(
            message.chat.id,
            "❌ Số dư không đủ",
            reply_markup=user_menu()
        )
        return

    cur.execute("SELECT id, username, password FROM accounts WHERE sold=0 LIMIT 1")
    acc = cur.fetchone()

    if not acc:
        bot.send_message(
            message.chat.id,
            "❌ Hết acc",
            reply_markup=user_menu()
        )
        return

    acc_id, u, p = acc

    cur.execute("UPDATE accounts SET sold=1 WHERE id=?", (acc_id,))
    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (ACC_PRICE, uid))
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

@bot.message_handler(func=lambda m: m.from_user.id in admin_add_mode)
def save_acc(message):
    if message.text in ["⬅️ Quay lại", "🔙 Quay lại"]:
        admin_add_mode.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "🔙 Admin menu", reply_markup=admin_menu())
        return

    if "|" not in message.text:
        bot.send_message(message.chat.id, "❌ Sai định dạng, đúng là: user|pass")
        return

    user, pwd = message.text.split("|", 1)
    cur.execute(
        "INSERT INTO accounts(username, password) VALUES (?, ?)",
        (user.strip(), pwd.strip())
    )
    conn.commit()

    admin_add_mode.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ Đã thêm acc", reply_markup=admin_menu())

# ========= NẠP TIỀN =========
@bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
def deposit_menu(message):
    uid = message.from_user.id
    ensure_user(uid)   # ✅ ĐÚNG CHỖ


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
    
    pending_deposits[uid] = "waiting"

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

    # GỬI CHO ADMIN + NÚT TỪ CHỐI
    for admin_id in ADMIN_IDS:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                text="❌ Từ chối nạp",
                callback_data=f"reject_deposit:{uid}"
            )
        )

        bot.send_message(
            admin_id,
            f"💰 YÊU CẦU NẠP TIỀN\n\n"
            f"👤 User ID: {uid}\n"
            f"📌 Nội dung CK: NAP {uid}\n\n"
            f"Duyệt bằng:\n/duyet {uid} <số_tiền>",
            reply_markup=kb
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
    ensure_user(uid)   # ✅ ĐÚNG CHỖ

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

    # 🔐 đảm bảo user luôn tồn tại
    ensure_user(uid)

    cur.execute(
        "SELECT balance, total_deposit FROM users WHERE user_id=?",
        (uid,)
    )
    balance, total = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) FROM purchases WHERE user_id=?",
        (uid,)
    )
    total_acc = cur.fetchone()[0]

    text = (
        "ℹ️ THÔNG TIN TÀI KHOẢN\n\n"
        f"🆔 ID Telegram: `{uid}`\n"
        f"💰 Số dư: {balance} VND\n"
        f"🛒 Số acc đã mua: {total_acc}\n"
        f"💳 Tổng tiền nạp: {total} VND"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=back_kb()
    )

# ========= HỖ TRỢ =========
@bot.message_handler(func=lambda m: m.text == "🆘 Hỗ trợ")
def support(message):
    bot.send_message(
        message.chat.id,
        f"🆘 HỖ TRỢ\n👉 Liên hệ admin {ADMIN_SUPPORT}",
        reply_markup=back_kb()
    )

# ========= QUAY LẠI =========
@bot.message_handler(func=lambda m: m.text in ["⬅️ Quay lại", "🔙 Quay lại", "❌ Hủy"])
def back_to_menu(message):
    uid = message.from_user.id

    buy_state.pop(uid, None)
    admin_add_mode.pop(uid, None)

    bot.send_message(
        message.chat.id,
        "🏠 Menu chính",
        reply_markup=user_menu()
    )

# ========= RUN =========
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_deposit:"))
def reject_deposit(call):
    admin_id = call.from_user.id
    if admin_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Bạn không có quyền")
        return

    uid = int(call.data.split(":")[1])

    # Xóa trạng thái chờ nạp
    pending_deposits.pop(uid, None)

    # Thông báo cho user
    bot.send_message(
        uid,
        "❌ YÊU CẦU NẠP TIỀN BỊ TỪ CHỐI\n\n"
        "📌 Lý do có thể:\n"
        "– Chưa nhận được tiền\n"
        "– Sai nội dung chuyển khoản\n\n"
        "👉 Vui lòng liên hệ admin để được hỗ trợ"
    )

    # Cập nhật tin nhắn admin
    bot.edit_message_text(
        "❌ ĐÃ TỪ CHỐI YÊU CẦU NẠP TIỀN",
        call.message.chat.id,
        call.message.message_id
    )

    bot.answer_callback_query(call.id, "Đã từ chối")

bot.infinity_polling()
