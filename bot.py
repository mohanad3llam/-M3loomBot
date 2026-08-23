import os
import random
import sqlite3
import time
from threading import Lock

from telegram import Update, ChatPermissions
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# صاحب البوت: هنوزة
OWNER_ID = 7584024550
OWNER_NAME = "هنوزة"

DB_FILE = "ma3loom.db"

amira_last_reply = {}
db_lock = Lock()


# =========================
# Database
# =========================

def get_db():
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            name TEXT,
            xp INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, chat_id)
        )
    """)

    conn.commit()
    return conn


def add_xp(user, chat):
    try:
        with db_lock:
            conn = get_db()

            conn.execute("""
                INSERT INTO users(
                    user_id,
                    chat_id,
                    name,
                    xp
                )
                VALUES (?, ?, ?, 1)

                ON CONFLICT(user_id, chat_id)
                DO UPDATE SET
                    name=excluded.name,
                    xp=xp+1
            """, (
                user.id,
                chat.id,
                user.first_name or "عضو",
            ))

            conn.commit()
            conn.close()

    except Exception:
        pass


# =========================
# Helpers
# =========================

def normalize(text):
    text = text.lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return text.strip()


def is_owner(user):
    return user and user.id == OWNER_ID


async def is_admin(update, user_id):
    try:
        member = await update.effective_chat.get_member(user_id)

        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )

    except Exception:
        return False


async def bot_can_restrict(update):
    try:
        me = await update.effective_chat.get_member(
            update.get_bot().id
        )

        return (
            me.status == ChatMemberStatus.ADMINISTRATOR
            and getattr(
                me,
                "can_restrict_members",
                False,
            )
        )

    except Exception:
        return False


# =========================
# Owner Replies
# =========================

OWNER_REPLIES = [
    "أؤمر يا هنوزة 👑❤️",
    "من عيوني يا صاحب معلوم ❤️",
    "حاضر يا كبير 😂👑",
    "تحت أمرك يا باشا 🫡",
    "قلب معلوم تحت أمرك 😂❤️",
    "طلباتك أوامر يا هنوزة 👑",
    "البوت كله في خدمتك 😂❤️",
    "قول بس يا صاحب المكان 🔥",
]


async def owner_reply(update):
    await update.message.reply_text(
        random.choice(OWNER_REPLIES)
    )


# =========================
# Commands
# =========================

async def start(update, context):
    await update.message.reply_text(
        "🤖 أهلاً بيك في معلوم 😂❤️\n\n"
        "أنا بوت الجروب بتاع الألعاب والهزار "
        "والتفاعل والإدارة.\n\n"
        "اكتب /commands عشان تشوف كل حاجة."
    )


async def intro(update, context):
    await update.message.reply_text(
        "🤖 أنا معلوم 😂❤️\n"
        "بوت ألعاب + هزار + تفاعل + إدارة.\n\n"
        "👑 صاحب البوت: هنوزة"
    )


async def commands(update, context):
    await update.message.reply_text(
        """📋 أوامر معلوم

🤖 الأساسي
/start
/intro
/commands
/help

🎮 الألعاب
/quiz
/guess
/dice
/coin
/challenge
/roll
/choose
/duel

🏆 النقاط
/score
/rank
/level

🛡️ الإدارة
تحذير
كتم
فك كتم
حظر
فك حظر

😂 التفاعل
معلوم

👑 صاحب البوت
هنوزة
"""
    )


async def help_command(update, context):
    await commands(update, context)


# =========================
# Quiz
# =========================

async def quiz(update, context):

    questions = [
        ("عاصمة مصر؟", "القاهرة"),
        ("كام يوم في الأسبوع؟", "7"),
        ("أكبر كوكب في المجموعة الشمسية؟", "المشتري"),
        ("كام شهر في السنة؟", "12"),
        ("عاصمة الإمارات؟", "أبوظبي"),
    ]

    question, answer = random.choice(questions)

    context.chat_data["quiz_answer"] = answer

    await update.message.reply_text(
        f"🎮 سؤال معلوم:\n\n"
        f"❓ {question}\n\n"
        f"اكتب الإجابة."
    )


# =========================
# Dice
# =========================

async def dice(update, context):
    number = random.randint(1, 6)

    await update.message.reply_text(
        f"🎲 النرد وقع على: {number}"
    )


# =========================
# Coin
# =========================

async def coin(update, context):

    result = random.choice([
        "🪙 صورة",
        "🪙 كتابة",
    ])

    await update.message.reply_text(
        f"🪙 النتيجة: {result}"
    )


# =========================
# Guess
# =========================

async def guess(update, context):

    number = random.randint(1, 10)

    context.chat_data["guess_number"] = number

    await update.message.reply_text(
        "🎯 خمنت رقم من 1 إلى 10!\n"
        "اكتب رقم وخمن 😂"
    )


# =========================
# Challenge
# =========================

async def challenge(update, context):

    challenges = [
        "😂 ابعت آخر إيموجي عندك.",
        "🎤 اكتب أول كلمة تيجي في دماغك.",
        "😎 قول مين أكتر شخص بيضحكك هنا.",
        "🔥 اختار شخص واعمله منشن.",
        "😂 اكتب نكتة في سطر واحد.",
    ]

    await update.message.reply_text(
        random.choice(challenges)
    )


# =========================
# Roll
# =========================

async def roll(update, context):

    number = random.randint(1, 100)

    await update.message.reply_text(
        f"🎲 الرقم العشوائي: {number}"
    )


# =========================
# Score
# =========================

async def score(update, context):

    conn = get_db()

    row = conn.execute("""
        SELECT xp, score
        FROM users
        WHERE user_id=? AND chat_id=?
    """, (
        update.effective_user.id,
        update.effective_chat.id,
    )).fetchone()

    conn.close()

    if not row:
        await update.message.reply_text(
            "لسه معندكش نقاط 😂"
        )
        return

    xp, score_value = row

    await update.message.reply_text(
        f"🏆 نقاطك: {score_value}\n"
        f"⭐ XP: {xp}"
    )


# =========================
# Rank
# =========================

async def rank(update, context):

    conn = get_db()

    rows = conn.execute("""
        SELECT name, xp
        FROM users
        WHERE chat_id=?
        ORDER BY xp DESC
        LIMIT 10
    """, (
        update.effective_chat.id,
    )).fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text(
            "لسه مفيش ترتيب 😂"
        )
        return

    text = "🏆 ترتيب الجروب\n\n"

    for i, (name, xp) in enumerate(rows, 1):
        text += f"{i}. {name} — ⭐ {xp} XP\n"

    await update.message.reply_text(text)


# =========================
# Level
# =========================

async def level(update, context):

    conn = get_db()

    row = conn.execute("""
        SELECT xp
        FROM users
        WHERE user_id=? AND chat_id=?
    """, (
        update.effective_user.id,
        update.effective_chat.id,
    )).fetchone()

    conn.close()

    if not row:
        xp = 0
    else:
        xp = row[0]

    current_level = (xp // 10) + 1

    await update.message.reply_text(
        f"⭐ XP: {xp}\n"
        f"🏆 مستواك: {current_level}"
    )


# =========================
# Choose
# =========================

async def choose(update, context):

    if not context.args:
        await update.message.reply_text(
            "استخدمها كده:\n"
            "/choose بيتزا برجر كشري"
        )
        return

    choice = random.choice(context.args)

    await update.message.reply_text(
        f"🎯 اختياري هو: {choice}"
    )


# =========================
# Duel
# =========================

async def duel(update, context):

    reply = update.message.reply_to_message

    if not reply:
        await update.message.reply_text(
            "اعمل Reply على الشخص اللي عايز تتحداه 😂"
        )
        return

    target = reply.from_user

    winner = random.choice([
        update.effective_user,
        target,
    ])

    await update.message.reply_text(
        f"⚔️ التحدي بدأ!\n\n"
        f"🏆 الفائز: {winner.first_name} 😂🔥"
    )


# =========================
# Welcome
# =========================

async def welcome(update, context):

    if not update.chat_member:
        return

    old = update.chat_member.old_chat_member
    new = update.chat_member.new_chat_member

    if (
        old.status in ("left", "kicked")
        and new.status == "member"
    ):

        await update.effective_chat.send_message(
            f"👋 نورت يا {new.user.first_name} 😂❤️"
        )


# =========================
# Moderation
# =========================

async def moderation(update, context):

    if not update.message:
        return

    text = normalize(
        update.message.text or ""
    )

    moderation_words = (
        "تحذير",
        "كتم",
        "فك كتم",
        "حظر",
        "فك حظر",
    )

    if text not in moderation_words:
        return

    if not is_owner(update.effective_user):

        if not await is_admin(
            update,
            update.effective_user.id
        ):
            await update.message.reply_text(
                "👮 الأمر ده للمشرفين بس."
            )
            return

    reply = update.message.reply_to_message

    if not reply:
        await update.message.reply_text(
            "اعمل Reply على الشخص الأول."
        )
        return

    target = reply.from_user
    chat = update.effective_chat

    # تحذير

    if text == "تحذير":

        conn = get_db()

        row = conn.execute("""
            SELECT warnings
            FROM users
            WHERE user_id=? AND chat_id=?
        """, (
            target.id,
            chat.id,
        )).fetchone()

        warnings = (row[0] if row else 0) + 1

        conn.execute("""
            INSERT INTO users(
                user_id,
                chat_id,
                name,
                warnings
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id, chat_id)
            DO UPDATE SET
                warnings=excluded.warnings
        """, (
            target.id,
            chat.id,
            target.first_name,
            warnings,
        ))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"⚠️ تحذير لـ {target.first_name}\n"
            f"التحذيرات: {warnings}/3"
        )

        if warnings >= 3:

            if await bot_can_restrict(update):

                await chat.restrict_member(
                    target.id,
                    permissions=ChatPermissions(
                        can_send_messages=False
                    )
                )

                await update.message.reply_text(
                    f"🔇 {target.first_name} "
                    f"اتكتم بسبب 3 تحذيرات."
                )

        return

    # كتم

    if text == "كتم":

        if not await bot_can_restrict(update):

            await update.message.reply_text(
                "ارفعني Admin واديني صلاحية "
                "تقييد الأعضاء."
            )
            return

        await chat.restrict_member(
            target.id,
            permissions=ChatPermissions(
                can_send_messages=False
            )
        )

        await update.message.reply_text(
            f"🔇 تم كتم {target.first_name}"
        )

        return

    # فك كتم

    if text == "فك كتم":

        if not await bot_can_restrict(update):

            await update.message.reply_text(
                "ارفعني Admin واديني صلاحية "
                "تقييد الأعضاء."
            )
            return

        await chat.restrict_member(
            target.id,
            permissions=ChatPermissions(
                can_send_messages=True
            )
        )

        await update.message.reply_text(
            f"🔊 تم فك الكتم عن "
            f"{target.first_name}"
        )

        return

    # حظر

    if text == "حظر":

        await chat.ban_member(
            target.id
        )

        await update.message.reply_text(
            f"🚫 تم حظر {target.first_name}"
        )

        return

    # فك حظر

    if text == "فك حظر":

        await chat.unban_member(
            target.id
        )

        await update.message.reply_text(
            f"✅ تم فك الحظر عن "
            f"{target.first_name}"
        )


# =========================
# Special Names
# =========================

def special_reply(text):

    if text in (
        "اميره",
        "اميرة",
        "اميره",
    ):

        return random.choice([
            "قلب هنونة ❤️",
            "نن عين هنونة ❤️",
            "روح قلب هنونة ❤️",
            "روح نن عين قلب اللي جاب هنونة ❤️",
            "يا حتة من قلب هنونة ❤️",
        ])

    if text in (
        "يوكاس",
        "يوكا",
    ):

        return random.choice([
            "اممممماي 😂❤️",
            "ست الحبايب ❤️",
            "يا يوكا يا ست الكل 😂",
        ])

    if text in (
        "توحا",
        "تتح",
        "توحه",
        "توحه",
        "تتوحه",
    ):

        return random.choice([
            "حربوقة 😂",
            "حموكشة 😂",
            "150 سانتي 📏😂",
            "يا توحا يا مصيبة 😂",
        ])

    if text in (
        "اسلام",
        "سلوكه",
        "اسلاو",
    ):

        return random.choice([
            "الأصفر 🟡😂",
            "لامؤاخذة يا اسلااااوو 😂",
            "الفنان 🎨😂",
            "سلوكة يا معلم 😂",
        ])

    if text in (
        "دانتي",
        "دانيت",
        "دانتوته",
        "دانو",
    ):

        return random.choice([
            "كينجايتنا 👑",
            "الكينجاية 👑",
            "Queen ❤️",
        ])

    return None


# =========================
# General Messages
# =========================

async def messages(update, context):

    if not update.message:
        return

    if not update.message.text:
        return

    text = normalize(
        update.message.text
    )

    user = update.effective_user

    add_xp(
        user,
        update.effective_chat
    )

    # =====================
    # Owner
    # =====================

    if is_owner(user):

        if (
            "معلوم" in text
            or "يا بوت" in text
            or "بوت" == text
        ):

            await owner_reply(update)
            return

        if (
            "مين صاحب البوت" in text
            or "مين صاحبك" in text
            or "صاحب البوت مين" in text
        ):

            await update.message.reply_text(
                "👑 صاحب معلوم هو هنوزة ❤️😂\n"
                "ده الباشا وصاحب المكان."
            )

            return

    # =====================
    # Amira username
    # =====================

    username = (
        user.username or ""
    ).lower()

    if username == "amira_sadek_77":

        now = time.time()
        chat_id = update.effective_chat.id

        last = amira_last_reply.get(
            chat_id,
            0
        )

        if now - last >= 900:

            amira_last_reply[
                chat_id
            ] = now

            await update.message.reply_text(
                random.choice([
                    "👑 برنسيسة الشات ❤️",
                    "🌙 القمر وصل",
                    "❤️ الشات نور",
                    "👸 يا برنسيسة",
                    "😂❤️ القمر منور",
                ])
            )

        return

    # =====================
    # Special names
    # =====================

    reply = special_reply(text)

    if reply:

        await update.message.reply_text(
            reply
        )

        return

    # =====================
    # Calling Ma3loom
    # =====================

    if (
        text == "معلوم"
        or text.startswith("معلوم ")
        or "يا معلوم" in text
    ):

        await update.message.reply_text(
            random.choice([
                "❤️ قلب معلوم",
                "أبشر 😂❤️",
                "أؤمر يا نجم 👑",
                "من عيوني ❤️",
                "تحت أمرك 😂",
                "حاضر يا كبير 🔥",
            ])
        )

        return

    # =====================
    # Requests
    # =====================

    request_words = (
        "ممكن",
        "عايز",
        "عاوز",
        "محتاج",
        "هات",
        "هاتلي",
        "اعمل",
        "اعملي",
        "ساعدني",
        "ساعد",
        "جيب",
        "جيبلي",
    )

    if any(
        word in text
        for word in request_words
    ):

        await update.message.reply_text(
            random.choice([
                "أبشر 😂❤️",
                "أبشر يا نجم ❤️",
                "من عيوني 😂",
                "حاضر يا كبير 👑",
                "تحت أمرك يا معلم 😂",
            ])
        )


# =========================
# Main
# =========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN غير موجود "
            "في Environment Variables."
        )

    get_db().close()

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Commands

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "intro",
            intro
        )
    )

    app.add_handler(
        CommandHandler(
            "commands",
            commands
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "quiz",
            quiz
        )
    )

    app.add_handler(
        CommandHandler(
            "guess",
            guess
        )
    )

    app.add_handler(
        CommandHandler(
            "dice",
            dice
        )
    )

    app.add_handler(
        CommandHandler(
            "coin",
            coin
        )
    )

    app.add_handler(
        CommandHandler(
            "challenge",
            challenge
        )
    )

    app.add_handler(
        CommandHandler(
            "roll",
            roll
        )
    )

    app.add_handler(
        CommandHandler(
            "choose",
            choose
        )
    )

    app.add_handler(
        CommandHandler(
            "duel",
            duel
        )
    )

    app.add_handler(
        CommandHandler(
            "score",
            score
        )
    )

    app.add_handler(
        CommandHandler(
            "rank",
            rank
        )
    )

    app.add_handler(
        CommandHandler(
            "level",
            level
        )
    )

    # Welcome

    app.add_handler(
        ChatMemberHandler(
            welcome,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    # Normal messages

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        ),
        group=0
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderation
        ),
        group=1
    )

    print(
        "Ma3loom is running... OWNER: هنوزة"
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
    