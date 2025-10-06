import telebot
import requests
import json
import random
import time
import threading
import os

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8404206641:AAEwYOgnkoo1USe7Ckqtxq7e0CXy-qBdEWQ")
ADMIN_IDS = [5218415209]  # Твой ID админа

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для сохранения данных
DATA_FILE = "user_data.json"

# БАЗА ДАННЫХ 10 ИГРОКОВ
DEFAULT_USER_DATA = {
    "balances": {
        "1241375637": 37231,
        "5218415209": 29520, 
        "7870057656": 22460,
        "7834416650": 20491,
        "7998824253": 20023,
        "8222625555": 19369,
        "973089312": 18268,
        "6167505435": 16717,
        "5281516992": 13183,
        "6382312148": 12390
    },
    "last_used": {
        "1241375637": 0,
        "5218415209": 0,
        "7870057656": 0,
        "7834416650": 0,
        "7998824253": 0,
        "8222625555": 0,
        "973089312": 0,
        "6167505435": 0,
        "5281516992": 0,
        "6382312148": 0
    }
}

# Функция загрузки данных
def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("✅ Данные игроков загружены!")
                return data
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    # Если файла нет, возвращаем дефолтную базу
    print("✅ Загружена дефолтная база данных 10 игроков")
    return DEFAULT_USER_DATA.copy()

# Функция сохранения данных
def save_user_data():
    try:
        if hasattr(farm_money, 'user_balances') and hasattr(farm_money, 'last_used'):
            data = {
                "balances": farm_money.user_balances,
                "last_used": farm_money.last_used
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("💾 Данные сохранены!")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

# Функция автосохранения
def autosave_worker():
    while True:
        time.sleep(300)  # Сохраняем каждые 5 минут
        save_user_data()

# Обновленная система боссов с авто-спавном
boss_data = {
    "active": False,
    "hp": 0,
    "max_hp": 0,
    "name": "", 
    "reward": 0,
    "attackers": {},
    "stunned_players": {},
    "already_stunned": set(),  # Игроки, которых уже оглушали
    "message_id": None,
    "chat_id": None,
    "last_spawn_time": 0
}

# Словари для отслеживания активности
chat_last_activity = {}
user_activity = {}
top_last_used = {}
attack_last_used = {}
casino_last_used = {}
race_last_used = {}

# Загрузка данных при запуске
user_data = load_user_data()

# Функция авто-спавна босса
def auto_spawn_boss():
    while True:
        try:
            current_time = time.time()
            
            # Спавним каждые 25 минут (1500 секунд)
            if not boss_data["active"] and current_time - boss_data["last_spawn_time"] > 1500:
                # Получаем активные чаты (где была активность за последний час)
                active_chats = []
                for chat_id, last_activity in chat_last_activity.items():
                    if current_time - last_activity < 3600:  # 1 час
                        active_chats.append(chat_id)
                
                if active_chats:
                    # Выбираем случайный активный чат
                    chat_id = random.choice(active_chats)
                    
                    # Создаем улучшенного босса
                    bosses = [
                        {"name": "🔥 Огненный Дракон", "hp": 10000, "reward": 5000},
                        {"name": "❄️ Ледяной Гигант", "hp": 8000, "reward": 4000},
                        {"name": "⚡ Электро Голем", "hp": 12000, "reward": 6000},
                        {"name": "🌪️ Вихревой Демон", "hp": 9000, "reward": 4500},
                        {"name": "💀 Король Теней", "hp": 15000, "reward": 7500}
                    ]
                    
                    boss = random.choice(bosses)
                    boss_data.update({
                        "active": True,
                        "hp": boss["hp"],
                        "max_hp": boss["hp"],
                        "name": boss["name"],
                        "reward": boss["reward"],
                        "attackers": {},
                        "stunned_players": {},
                        "already_stunned": set(),
                        "message_id": None,
                        "chat_id": chat_id,
                        "last_spawn_time": current_time
                    })
                    
                    # Создаем сообщение с кнопкой атаки
                    markup = telebot.types.InlineKeyboardMarkup()
                    attack_button = telebot.types.InlineKeyboardButton(
                        text="⚔️ АТАКОВАТЬ БОССА", 
                        callback_data="boss_attack"
                    )
                    markup.add(attack_button)
                    
                    boss_text = f"""🎯 *ПОЯВИЛСЯ БОСС!*

*{boss['name']}*
❤️ HP: `{boss['hp']}/{boss['hp']}`
💰 Награда: `{boss['reward']}₽`

_Нажми кнопку ниже чтобы атаковать!_"""
                    sent_message = bot.send_message(chat_id, boss_text, reply_markup=markup, parse_mode='Markdown')
                    boss_data["message_id"] = sent_message.message_id
                    
                    print(f"🦖 Босс заспавнился в чате {chat_id}")
                    
                    # Запускаем систему оглушения
                    start_stun_system()
            
            time.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            print(f"❌ Ошибка в авто-спавне босса: {e}")
            time.sleep(60)

# Система оглушения игроков - 3 игрока каждые 25 секунд
def start_stun_system():
    def stun_worker():
        stun_round = 0
        while boss_data["active"] and stun_round < 10:  # Максимум 10 раундов оглушения
            try:
                # Ждем 25 секунд между оглушениями
                time.sleep(25)
                
                if boss_data["active"] and boss_data["attackers"]:
                    # Выбираем 3 случайных атакующих для оглушения (кроме уже оглушенных)
                    attackers_list = [uid for uid in boss_data["attackers"].keys() 
                                    if uid not in boss_data["already_stunned"]]
                    
                    if len(attackers_list) >= 3:
                        stunned_players = random.sample(attackers_list, 3)
                    elif attackers_list:
                        stunned_players = attackers_list
                    else:
                        continue
                    
                    stun_messages = []
                    for stunned_player in stunned_players:
                        # Оглушаем на 20 секунд
                        stun_end_time = time.time() + 20
                        boss_data["stunned_players"][stunned_player] = stun_end_time
                        boss_data["already_stunned"].add(stunned_player)
                        
                        # Получаем информацию об игроке
                        try:
                            user_info = bot.get_chat(int(stunned_player))
                            username = user_info.first_name
                        except:
                            username = f"Игрок {stunned_player}"
                        
                        stun_messages.append(f"💫 *{username}* оглушен на 20 секунд!")
                        print(f"💫 Игрок {stunned_player} оглушен")
                    
                    # Отправляем одно сообщение со всеми оглушенными
                    if stun_messages:
                        stun_message = "⚡ *БОСС ОГЛУШИЛ ИГРОКОВ!*\n\n" + "\n".join(stun_messages)
                        bot.send_message(boss_data["chat_id"], stun_message, parse_mode='Markdown')
                    
                    stun_round += 1
                
            except Exception as e:
                print(f"❌ Ошибка в системе оглушения: {e}")
                time.sleep(5)
    
    # Запускаем оглушение в отдельном потоке
    stun_thread = threading.Thread(target=stun_worker, daemon=True)
    stun_thread.start()

# Обработчик кнопки атаки
@bot.callback_query_handler(func=lambda call: call.data == "boss_attack")
def handle_boss_attack(call):
    try:
        if not boss_data["active"]:
            bot.answer_callback_query(call.id, "❌ Босс уже побежден!")
            return
        
        user_id = str(call.from_user.id)  # Преобразуем в строку
        current_time = time.time()
        
        # Проверяем оглушение
        if user_id in boss_data["stunned_players"]:
            stun_remaining = boss_data["stunned_players"][user_id] - current_time
            if stun_remaining > 0:
                bot.answer_callback_query(
                    call.id, 
                    f"❌ Вы оглушены! Ждите {int(stun_remaining)} секунд", 
                    show_alert=True
                )
                return
        
        # Проверка кд атаки (3 секунды)
        if user_id in attack_last_used:
            time_passed = current_time - attack_last_used[user_id]
            if time_passed < 3:
                bot.answer_callback_query(call.id, "❌ Атака перезаряжается!", show_alert=True)
                return
        
        attack_last_used[user_id] = current_time
        
        # Урон от 100 до 500
        damage = random.randint(100, 500)
        boss_data["hp"] -= damage
        
        # Записываем урон игрока
        if user_id not in boss_data["attackers"]:
            boss_data["attackers"][user_id] = {"damage": 0, "username": call.from_user.first_name}
        
        boss_data["attackers"][user_id]["damage"] += damage
        
        # Обновляем сообщение с боссом
        hp_percent = (boss_data["hp"] / boss_data["max_hp"]) * 100
        progress_bar = "█" * int(hp_percent / 10) + "░" * (10 - int(hp_percent / 10))
        
        # Создаем обновленную клавиатуру
        markup = telebot.types.InlineKeyboardMarkup()
        attack_button = telebot.types.InlineKeyboardButton(
            text="⚔️ АТАКОВАТЬ БОССА", 
            callback_data="boss_attack"
        )
        markup.add(attack_button)
        
        boss_text = f"""🎯 *БОСС АТАКУЕТ!*

*{boss_data['name']}*
{progress_bar} `{boss_data['hp']}/{boss_data['max_hp']} HP`
💰 Награда: `{boss_data['reward']}₽`

_Нажми кнопку чтобы атаковать!_"""
        
        try:
            bot.edit_message_text(
                chat_id=boss_data["chat_id"],
                message_id=boss_data["message_id"],
                text=boss_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        except:
            pass
        
        # Проверяем победу
        if boss_data["hp"] <= 0:
            # Награждаем всех атакующих
            winners_text = f"""🎉 *БОСС ПОБЕЖДЕН!*

*{boss_data['name']} уничтожен!*

🏆 *Победители:*\n"""
            total_reward = boss_data["reward"]
            
            for attacker_id, data in boss_data["attackers"].items():
                reward = total_reward + data["damage"] // 5
                if attacker_id not in farm_money.user_balances:
                    farm_money.user_balances[attacker_id] = 0
                farm_money.user_balances[attacker_id] += reward
                
                try:
                    user_info = bot.get_chat(int(attacker_id))
                    username = user_info.first_name
                except:
                    username = data["username"]
                
                winners_text += f"👤 {username} +{reward}₽ (урон: {data['damage']})\n"
            
            bot.send_message(boss_data["chat_id"], winners_text, parse_mode='Markdown')
            boss_data["active"] = False
            
            # Сохраняем данные после победы над боссом
            save_user_data()
        
        bot.answer_callback_query(call.id, f"✅ Нанесено {damage} урона!")
        
    except Exception as e:
        print(f"❌ Ошибка в атаке босса: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка атаки!")

# Функция напоминания
def reminder_worker():
    while True:
        try:
            current_time = time.time()
            for chat_id, last_activity in list(chat_last_activity.items()):
                # Проверяем прошло ли 10 минут (600 секунд)
                if current_time - last_activity > 600:
                    try:
                        bot.send_message(chat_id, "💤 Что-то вы давно мною не пользовались...\nВведите /farma чтобы начать фармить!")
                        # Обновляем время чтобы не спамить
                        chat_last_activity[chat_id] = current_time
                    except:
                        # Если чат не найден или ошибка - удаляем из отслеживания
                        if chat_id in chat_last_activity:
                            del chat_last_activity[chat_id]
            time.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            print(f"❌ Ошибка в напоминаниях: {e}")
            time.sleep(60)

# Запуск потоков
reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
reminder_thread.start()

boss_auto_spawn_thread = threading.Thread(target=auto_spawn_boss, daemon=True)
boss_auto_spawn_thread.start()

autosave_thread = threading.Thread(target=autosave_worker, daemon=True)
autosave_thread.start()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = """👋 *Добро пожаловать в Flipper Zero Bot!*

💎 Фарми деньги на крутые гаджеты
⚔️ Сражайся с боссами
🎰 Испытай удачу в казино
🏎️ Участвуй в гонках

📋 *Доступные команды:*
/farma - Фармить деньги
/top - Топ фармеров  
/casino - Казино
/race - Гонки
/help - Помощь

_Добавь бота в группу для большего веселья!_"""
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Ошибка в /start: {e}")

# Команда /add
@bot.message_handler(commands=['add'])
def add_to_chat(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        url_button = telebot.types.InlineKeyboardButton(
            text="➕ Добавить в чат", 
            url="https://t.me/Dodsterchat203_bot?startgroup=true"
        )
        markup.add(url_button)
        bot.send_message(
            message.chat.id, 
            "🎯 *Добавь бота в свой чат для полного функционала!*", 
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ Ошибка в /add: {e}")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        help_text = """🛠️ *Доступные команды:*

💰 *Фарминг:*
/farma - Фармить деньги (4 мин КД)
/top - Топ 35 фармеров

🎮 *Игры:*
/casino - Казино (30 сек КД)
/race - Гонки (60 сек КД)

⚔️ *Боссы:*
Боссы появляются автоматически каждые 25 минут!
Оглушают 3 случайных игроков каждые 25 секунд

🎯 *Особенности:*
• Максимальный баланс: 60,000₽
• Минимальная ставка в казино: 100₽
• Награды за боссов: до 7,500₽"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Ошибка в /help: {e}")

# Команда /top с кд 25 секунд (35 ИГРОКОВ)
@bot.message_handler(commands=['top'])
def show_top_users(message):
    try:
        user_id = str(message.from_user.id)  # Преобразуем в строку
        current_time = time.time()
        
        # Проверка кд
        if user_id in top_last_used:
            time_passed = current_time - top_last_used[user_id]
            if time_passed < 25:
                remaining_time = 25 - int(time_passed)
                bot.reply_to(message, f"⏳ *Топ обновляется раз в 25 секунд*\n_Подожди еще {remaining_time} секунд_", parse_mode='Markdown')
                return
        
        top_last_used[user_id] = current_time
        
        # Обновляем активность чата
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
        
        # Сортируем пользователей по балансу (35 ИГРОКОВ)
        if hasattr(farm_money, 'user_balances') and farm_money.user_balances:
            sorted_users = sorted(farm_money.user_balances.items(), key=lambda x: x[1], reverse=True)[:35]
            
            top_text = "🏆 *ТОП 35 ФАРМЕРОВ*\n\n"
            medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 36)]
            
            for i, (user_id, balance) in enumerate(sorted_users, 1):
                try:
                    user_info = bot.get_chat(int(user_id))  # Преобразуем обратно для получения данных
                    username = user_info.first_name  # Только имя, без @
                    # Обрезаем длинные имена
                    if len(username) > 15:
                        username = username[:15] + "..."
                    medal = medals[i-1] if i-1 < len(medals) else f"{i}."
                    top_text += f"{medal} {username} - `{balance}₽`\n"
                except:
                    medal = medals[i-1] if i-1 < len(medals) else f"{i}."
                    top_text += f"{medal} ID:{user_id} - `{balance}₽`\n"
        else:
            top_text = "📊 *Пока никто не фармил.*\n_Будь первым! Введи_ /farma"
        
        bot.reply_to(message, top_text, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Ошибка в /top: {e}")

# Команда /casino
@bot.message_handler(commands=['casino'])
def casino_game(message):
    try:
        # Проверка кд 30 секунд
        user_id = str(message.from_user.id)  # Преобразуем в строку
        current_time = time.time()
        
        if user_id in casino_last_used:
            time_passed = current_time - casino_last_used[user_id]
            if time_passed < 30:
                remaining_time = 30 - int(time_passed)
                bot.reply_to(message, f"🎰 *Казино перезаряжается!*\n_Жди {remaining_time} секунд_", parse_mode='Markdown')
                return
        
        casino_last_used[user_id] = current_time
        
        # Получаем баланс пользователя
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        if balance < 100:
            bot.reply_to(message, "❌ *Минимальная ставка - 100₽*\n_Сначала поднакопи!_", parse_mode='Markdown')
            return
        
        # Создаем клавиатуру со ставками
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            telebot.types.InlineKeyboardButton("🎯 100₽", callback_data="casino_bet:100"),
            telebot.types.InlineKeyboardButton("💎 500₽", callback_data="casino_bet:500"),
            telebot.types.InlineKeyboardButton("🔥 1000₽", callback_data="casino_bet:1000"),
            telebot.types.InlineKeyboardButton("⚡ 2000₽", callback_data="casino_bet:2000"),
            telebot.types.InlineKeyboardButton("💰 5000₽", callback_data="casino_bet:5000"),
            telebot.types.InlineKeyboardButton("🚀 ВСЁ", callback_data="casino_bet:all")
        ]
        markup.add(*buttons)
        
        casino_text = f"""🎰 *КАЗИНО Flipper Zero*

💵 Твой баланс: `{balance}₽`
🎯 Минимальная ставка: `100₽`

_Выбери ставку:_"""
        bot.send_message(message.chat.id, casino_text, reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ Ошибка в /casino: {e}")

# Обработчик ставок в казино
@bot.callback_query_handler(func=lambda call: call.data.startswith('casino_bet:'))
def handle_casino_bet(call):
    try:
        user_id = str(call.from_user.id)  # Преобразуем в строку
        bet_data = call.data.split(':')[1]
        
        # Получаем текущий баланс
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        # Определяем сумму ставки
        if bet_data == "all":
            bet_amount = balance
        else:
            bet_amount = int(bet_data)
        
        # Проверяем возможность ставки
        if bet_amount < 100:
            bot.answer_callback_query(call.id, "❌ Минимальная ставка - 100₽!", show_alert=True)
            return
        
        if bet_amount > balance:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return
        
        if bet_amount > 10000:
            bot.answer_callback_query(call.id, "❌ Максимальная ставка - 10,000₽!", show_alert=True)
            return
        
        # Игровой процесс
        result = random.random()
        
        if result < 0.45:
            outcome = "lose"
            multiplier = 0
            win_amount = -bet_amount
            result_text = "💔 ПРОИГРЫШ"
            emoji = "💔"
        
        elif result < 0.90:
            outcome = "win"
            multiplier = 1
            win_amount = bet_amount
            result_text = "✅ ВЫИГРЫШ x1"
            emoji = "✅"
        
        elif result < 0.98:
            outcome = "double"
            multiplier = 2
            win_amount = bet_amount * 2
            result_text = "🎉 УДВОЕНИЕ x2"
            emoji = "🎉"
        
        else:
            outcome = "jackpot"
            multiplier = 5
            win_amount = bet_amount * 5
            result_text = "🎰 ДЖЕКПОТ x5"
            emoji = "🎰"
        
        # Обновляем баланс
        farm_money.user_balances[user_id] += win_amount
        new_balance = farm_money.user_balances[user_id]
        
        # СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ИГРЫ
        save_user_data()
        
        # Формируем результат
        if win_amount > 0:
            result_message = f"""{emoji} *{result_text}*

💰 Ставка: `{bet_amount}₽`
🎁 Выигрыш: `+{win_amount}₽`

💵 Новый баланс: `{new_balance}₽`"""
        else:
            result_message = f"""{emoji} *{result_text}*

💰 Ставка: `{bet_amount}₽`
📉 Проигрыш: `{win_amount}₽`

💵 Новый баланс: `{new_balance}₽`"""
        
        # Обновляем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=result_message,
            parse_mode='Markdown'
        )
        
        bot.answer_callback_query(call.id, f"Результат: {result_text}")
        
    except Exception as e:
        print(f"❌ Ошибка в обработке ставки: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка в казино!", show_alert=True)

# Команда /race - новая игра гонки
@bot.message_handler(commands=['race'])
def start_race(message):
    try:
        # Проверка кд 60 секунд
        user_id = str(message.from_user.id)  # Преобразуем в строку
        current_time = time.time()
        
        if user_id in race_last_used:
            time_passed = current_time - race_last_used[user_id]
            if time_passed < 60:
                remaining_time = 60 - int(time_passed)
                bot.reply_to(message, f"🏎️ *Гонки перезаряжаются!*\n_Жди {remaining_time} секунд_", parse_mode='Markdown')
                return
        
        race_last_used[user_id] = current_time
        
        # Получаем баланс пользователя
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        if balance < 500:
            bot.reply_to(message, "❌ *Для участия в гонках нужно минимум 500₽*\n_Фарми больше!_", parse_mode='Markdown')
            return
        
        # Создаем клавиатуру с выбором машины
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            telebot.types.InlineKeyboardButton("🚗 Стандарт (500₽)", callback_data="race_car:500"),
            telebot.types.InlineKeyboardButton("🏎️ Спорт (1000₽)", callback_data="race_car:1000"),
            telebot.types.InlineKeyboardButton("🔥 Суперкар (2000₽)", callback_data="race_car:2000"),
            telebot.types.InlineKeyboardButton("💎 Люкс (5000₽)", callback_data="race_car:5000")
        ]
        markup.add(*buttons)
        
        race_text = f"""🏎️ *ГОНКИ Flipper Zero*

💵 Твой баланс: `{balance}₽`
🎯 Выбери машину:

🚗 Стандарт - 500₽ (шанс x1.5)
🏎️ Спорт - 1000₽ (шанс x2.0)  
🔥 Суперкар - 2000₽ (шанс x3.0)
💎 Люкс - 5000₽ (шанс x5.0)"""
        bot.send_message(message.chat.id, race_text, reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ Ошибка в /race: {e}")

# Обработчик выбора машины для гонки
@bot.callback_query_handler(func=lambda call: call.data.startswith('race_car:'))
def handle_race_car(call):
    try:
        user_id = str(call.from_user.id)  # Преобразуем в строку
        bet_amount = int(call.data.split(':')[1])
        
        # Получаем текущий баланс
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        balance = farm_money.user_balances[user_id]
        
        # Проверяем возможность ставки
        if bet_amount > balance:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств!", show_alert=True)
            return
        
        # Определяем множитель в зависимости от машины
        multipliers = {
            500: 1.5,
            1000: 2.0,
            2000: 3.0,
            5000: 5.0
        }
        multiplier = multipliers[bet_amount]
        
        # Симуляция гонки
        car_names = {
            500: "🚗 Стандарт",
            1000: "🏎️ Спорт", 
            2000: "🔥 Суперкар",
            5000: "💎 Люкс"
        }
        
        # Шанс на победу зависит от машины
        win_chance = 0.3 + (multiplier * 0.1)  # От 40% до 80%
        result = random.random()
        
        if result < win_chance:
            # Победа
            win_amount = int(bet_amount * multiplier)
            farm_money.user_balances[user_id] += win_amount
            new_balance = farm_money.user_balances[user_id]
            
            # Анимация гонки
            race_track = "🏁" + "─" * 20 + "🎯"
            car_positions = [
                f"{car_names[bet_amount]}━{' ' * random.randint(5, 15)}🚗",
                f"Соперник 1━{' ' * random.randint(3, 12)}🚙", 
                f"Соперник 2━{' ' * random.randint(2, 10)}🚕",
                f"Соперник 3━{' ' * random.randint(1, 8)}🚓"
            ]
            
            race_message = f"""🏎️ *ГОНКА НАЧАЛАСЬ!*

{race_track}
{chr(10).join(car_positions)}

⏱️ _Гонка продолжается..._"""
            
            msg = bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=race_message,
                parse_mode='Markdown'
            )
            
            time.sleep(2)
            
            # Финальное сообщение
            result_message = f"""🎉 *ПОБЕДА В ГОНКЕ!*

🏆 Ты занял 1 место!
🚗 Машина: {car_names[bet_amount]}
💰 Ставка: `{bet_amount}₽`
🎁 Выигрыш: `+{win_amount}₽` (x{multiplier})

💵 Новый баланс: `{new_balance}₽`"""
            
        else:
            # Проигрыш
            farm_money.user_balances[user_id] -= bet_amount
            new_balance = farm_money.user_balances[user_id]
            
            result_message = f"""💔 *ПОРАЖЕНИЕ В ГОНКЕ*

🚗 Машина: {car_names[bet_amount]}
🏁 Ты занял {random.randint(2, 4)} место
💰 Проигрыш: `{bet_amount}₽`

💵 Новый баланс: `{new_balance}₽`"""
        
        # СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ГОНКИ
        save_user_data()
        
        # Обновляем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=result_message,
            parse_mode='Markdown'
        )
        
        bot.answer_callback_query(call.id, "Гонка завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка в гонке: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка в гонках!", show_alert=True)

# Команда /farma
@bot.message_handler(commands=['farma'])
def farm_money(message):
    try:
        # Инициализация структур данных ИЗ ФАЙЛА
        if not hasattr(farm_money, 'user_balances'):
            farm_money.user_balances = user_data.get("balances", {})
        if not hasattr(farm_money, 'last_used'):
            farm_money.last_used = user_data.get("last_used", {})
        
        # Обновляем активность пользователя
        user_id = str(message.from_user.id)  # Преобразуем в строку
        if user_id not in user_activity:
            user_activity[user_id] = 0
        user_activity[user_id] += 1
        
        # Обновляем активность чата
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
        
        current_time = time.time()
        
        # Проверка кд
        if user_id in farm_money.last_used:
            time_passed = current_time - farm_money.last_used[user_id]
            if time_passed < 240:
                remaining_time = 240 - int(time_passed)
                bot.reply_to(message, f"⏳ *Фарминг перезаряжается!*\n_Подожди {remaining_time} секунд_", parse_mode='Markdown')
                return
        
        # Начисление денег
        farmed_amount = random.randint(800, 1900)
        
        if user_id not in farm_money.user_balances:
            farm_money.user_balances[user_id] = 0
        
        # Обновляем баланс
        new_balance = farm_money.user_balances[user_id] + farmed_amount
        if new_balance > 60000:
            new_balance = 60000
            farmed_amount = 60000 - farm_money.user_balances[user_id]
        
        farm_money.user_balances[user_id] = new_balance
        farm_money.last_used[user_id] = current_time
        
        # СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ИЗМЕНЕНИЯ
        save_user_data()
        
        response_text = f"""💰 *УСПЕШНЫЙ ФАРМИНГ!*

🎯 Заработано: `{farmed_amount}₽`
💵 Твой баланс: `{new_balance}₽/60000₽`

_Продолжай в том же духе!_ 🚀"""
        bot.reply_to(message, response_text, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Ошибка в /farma: {e}")

# Приветствие при добавлении бота в группу
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    try:
        for new_member in message.new_chat_members:
            if new_member.id == bot.get_me().id:
                welcome_text = """👋 *Бот Flipper Zero добавлен в чат!*

💎 Фарми деньги на крутые гаджеты
⚔️ Сражайся с боссами  
🎰 Испытай удачу в казино
🏎️ Участвуй в гонках

📋 Основные команды:
/farma - Фармить деньги
/top - Топ фармеров
/casino - Казино
/race - Гонки
/help - Помощь

_Приятной игры!_ 🎮"""
                bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
                chat_last_activity[message.chat.id] = time.time()
                break
    except Exception as e:
        print(f"❌ Ошибка в приветствии: {e}")

# Обновляем активность при любой команде в групповом чате
@bot.message_handler(func=lambda message: True)
def update_activity(message):
    try:
        if message.chat.type in ['group', 'supergroup']:
            chat_last_activity[message.chat.id] = time.time()
    except Exception as e:
        print(f"❌ Ошибка в обновлении активности: {e}")

# Запуск бота
if __name__ == "__main__":
    print("🤖 Бот Minerdodster203 запускается...")
    
    while True:
        try:
            print("🔗 Подключаемся к Telegram API...")
            bot.polling(
                none_stop=True,
                timeout=30,
                long_polling_timeout=30
            )
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка подключения: {e}")
            print("🔄 Перезапуск через 15 секунд...")
            time.sleep(15)
        except Exception as e:
            print(f"❌ Неизвестная ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)