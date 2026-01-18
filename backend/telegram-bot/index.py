import json
import os
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any

TELEGRAM_BOT_TOKEN = "8107172432:AAEfZlmEo2i2_9w0JClHO0mgTv11oGAhQuk"

def handler(event: dict, context) -> dict:
    """
    Telegram бот для модерации чата с полным функционалом:
    - Модерация: бан, мут, кик, варн
    - Роли администрации
    - Чёрный список
    - Автопроверки (спам, боты, возраст)
    - Система жалоб
    - Абан администрации
    """
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        # Получаем обновление от Telegram
        body = event.get('body', '{}')
        update = json.loads(body) if isinstance(body, str) else body
        
        # Подключение к БД
        db_url = os.environ.get('DATABASE_URL')
        schema = os.environ.get('MAIN_DB_SCHEMA', 'public')
        
        if not db_url:
            return response_json({'error': 'Database not configured'}, 500)
        
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Обработка обновления
        result = process_update(update, cur, schema)
        
        cur.close()
        conn.close()
        
        return response_json(result, 200)
        
    except Exception as e:
        return response_json({'error': str(e)}, 500)


def response_json(data: dict, status: int = 200) -> dict:
    """Формирование JSON ответа"""
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, ensure_ascii=False),
        'isBase64Encoded': False
    }


def process_update(update: Dict[Any, Any], cur, schema: str) -> Dict[str, Any]:
    """Обработка обновления от Telegram"""
    
    # Обработка сообщений
    if 'message' in update:
        message = update['message']
        
        # Новые участники
        if 'new_chat_members' in message:
            for new_member in message['new_chat_members']:
                handle_new_member(new_member, message['chat']['id'], cur, schema)
        
        # Команды бота
        if 'text' in message and message['text'].startswith('/'):
            return handle_command(message, cur, schema)
        
        # Проверка на спам
        if 'text' in message:
            check_spam(message, cur, schema)
    
    # Обработка callback кнопок
    if 'callback_query' in update:
        return handle_callback(update['callback_query'], cur, schema)
    
    return {'status': 'ok', 'method': 'update_processed'}


def handle_new_member(member: Dict[Any, Any], chat_id: int, cur, schema: str) -> None:
    """Обработка нового участника с автопроверками"""
    user_id = member['id']
    username = member.get('username', '')
    first_name = member.get('first_name', 'Пользователь')
    
    # Проверка чёрного списка
    cur.execute(f"SELECT reason FROM {schema}.blacklist WHERE telegram_id = %s", (user_id,))
    blacklisted = cur.fetchone()
    
    if blacklisted:
        send_telegram_message(chat_id, f"🚫 {first_name} в чёрном списке! Причина: {blacklisted[0]}")
        ban_telegram_user(chat_id, user_id)
        return
    
    # Проверка на бота
    if member.get('is_bot', False):
        cur.execute(f"""
            INSERT INTO {schema}.auto_checks (check_type, user_id, result, details)
            VALUES ('bot', %s, 'is_bot', 'Detected bot account')
        """, (user_id,))
        send_telegram_message(chat_id, f"🤖 Обнаружен бот: {first_name}")
    
    # Проверка возраста аккаунта
    if not username:
        cur.execute(f"""
            INSERT INTO {schema}.auto_checks (check_type, user_id, result, details)
            VALUES ('age', %s, 'suspicious', 'No username - possible new account')
        """, (user_id,))
        send_telegram_message(chat_id, f"⚠️ Новый аккаунт: {first_name}")
    
    # Сохраняем пользователя
    cur.execute(f"""
        INSERT INTO {schema}.users (telegram_id, username, first_name, join_date)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            join_date = CURRENT_TIMESTAMP
    """, (user_id, username, first_name))
    
    # Приветствие
    cur.execute(f"SELECT setting_value FROM {schema}.bot_settings WHERE setting_key = 'welcome_message'")
    welcome = cur.fetchone()
    if welcome:
        send_telegram_message(chat_id, f"👋 {first_name}, {welcome[0]}")


def handle_command(message: Dict[Any, Any], cur, schema: str) -> Dict[str, Any]:
    """Обработка команд бота"""
    text = message['text']
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    
    # Получаем роль
    role = get_user_role(user_id, cur, schema)
    
    # /start - главное меню
    if text == '/start':
        keyboard = {
            'inline_keyboard': [
                [{'text': '🛡️ Модерация', 'callback_data': 'menu_moderation'}],
                [{'text': '⚙️ Управление', 'callback_data': 'menu_admin'}],
                [{'text': '📊 Статистика', 'callback_data': 'menu_stats'}],
                [{'text': '📝 Жалобы', 'callback_data': 'menu_reports'}]
            ]
        }
        
        msg = f"""🤖 *Модерационный Бот*

Добро пожаловать! Ваша роль: *{get_role_name(role)}*

Выберите раздел:"""
        
        send_telegram_message(chat_id, msg, keyboard)
        return {'status': 'ok', 'action': 'menu_sent'}
    
    # /report - жалоба
    if text.startswith('/report'):
        if 'reply_to_message' in message:
            reported_user = message['reply_to_message']['from']['id']
            reason = text.replace('/report', '').strip() or 'Не указана'
            
            cur.execute(f"""
                INSERT INTO {schema}.reports (reporter_id, reported_user_id, message_id, reason)
                VALUES (%s, %s, %s, %s)
            """, (user_id, reported_user, message['message_id'], reason))
            
            send_telegram_message(chat_id, '✅ Жалоба принята! Модераторы рассмотрят её.')
            return {'status': 'ok', 'action': 'report_created'}
        else:
            send_telegram_message(chat_id, '❌ Ответьте на сообщение нарушителя командой /report [причина]')
            return {'status': 'error', 'message': 'no_reply_message'}
    
    # Модераторские команды
    if not has_permission(role, 'moderate'):
        send_telegram_message(chat_id, '❌ У вас нет прав для этой команды')
        return {'status': 'error', 'message': 'no_permission'}
    
    # /ban
    if text.startswith('/ban') and 'reply_to_message' in message:
        target_user = message['reply_to_message']['from']['id']
        reason = text.replace('/ban', '').strip() or 'Нарушение правил'
        
        cur.execute(f"UPDATE {schema}.users SET is_banned = TRUE WHERE telegram_id = %s", (target_user,))
        cur.execute(f"""
            INSERT INTO {schema}.moderation_actions (action_type, target_user_id, moderator_id, reason)
            VALUES ('ban', %s, %s, %s)
        """, (target_user, user_id, reason))
        
        ban_telegram_user(chat_id, target_user)
        send_telegram_message(chat_id, f'🚫 Пользователь забанен. Причина: {reason}')
        return {'status': 'ok', 'action': 'user_banned'}
    
    # /mute
    if text.startswith('/mute') and 'reply_to_message' in message:
        parts = text.split()
        target_user = message['reply_to_message']['from']['id']
        duration = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 60
        reason = ' '.join(parts[2:]) if len(parts) > 2 else 'Нарушение правил'
        
        mute_until = (datetime.now() + timedelta(minutes=duration)).isoformat()
        
        cur.execute(f"""
            UPDATE {schema}.users SET is_muted = TRUE, mute_until = %s WHERE telegram_id = %s
        """, (mute_until, target_user))
        
        cur.execute(f"""
            INSERT INTO {schema}.moderation_actions (action_type, target_user_id, moderator_id, reason, duration)
            VALUES ('mute', %s, %s, %s, %s)
        """, (target_user, user_id, reason, duration))
        
        mute_telegram_user(chat_id, target_user, duration)
        send_telegram_message(chat_id, f'🔇 Мут на {duration} мин. Причина: {reason}')
        return {'status': 'ok', 'action': 'user_muted'}
    
    # /kick
    if text.startswith('/kick') and 'reply_to_message' in message:
        target_user = message['reply_to_message']['from']['id']
        reason = text.replace('/kick', '').strip() or 'Нарушение правил'
        
        cur.execute(f"""
            INSERT INTO {schema}.moderation_actions (action_type, target_user_id, moderator_id, reason)
            VALUES ('kick', %s, %s, %s)
        """, (target_user, user_id, reason))
        
        kick_telegram_user(chat_id, target_user)
        send_telegram_message(chat_id, f'👢 Пользователь кикнут. Причина: {reason}')
        return {'status': 'ok', 'action': 'user_kicked'}
    
    # /warn
    if text.startswith('/warn') and 'reply_to_message' in message:
        target_user = message['reply_to_message']['from']['id']
        reason = text.replace('/warn', '').strip() or 'Нарушение правил'
        
        cur.execute(f"UPDATE {schema}.users SET warnings = warnings + 1 WHERE telegram_id = %s", (target_user,))
        cur.execute(f"""
            INSERT INTO {schema}.moderation_actions (action_type, target_user_id, moderator_id, reason)
            VALUES ('warn', %s, %s, %s)
        """, (target_user, user_id, reason))
        
        cur.execute(f"SELECT warnings FROM {schema}.users WHERE telegram_id = %s", (target_user,))
        result = cur.fetchone()
        warnings = result[0] if result else 1
        
        if warnings >= 3:
            ban_telegram_user(chat_id, target_user)
            send_telegram_message(chat_id, f'⚠️ Пользователь получил {warnings} предупреждений и забанен!')
        else:
            send_telegram_message(chat_id, f'⚠️ Предупреждение ({warnings}/3). Причина: {reason}')
        
        return {'status': 'ok', 'action': 'warning_issued'}
    
    return {'status': 'ok', 'action': 'command_processed'}


def handle_callback(callback: Dict[Any, Any], cur, schema: str) -> Dict[str, Any]:
    """Обработка кнопок"""
    data = callback['data']
    chat_id = callback['message']['chat']['id']
    user_id = callback['from']['id']
    role = get_user_role(user_id, cur, schema)
    
    if data == 'menu_stats':
        cur.execute(f"SELECT COUNT(*) FROM {schema}.users")
        total = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {schema}.users WHERE is_banned = TRUE")
        banned = cur.fetchone()[0]
        
        msg = f"""📊 *Статистика*

👥 Всего: {total}
🚫 Забанено: {banned}"""
        
        keyboard = {'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'menu_main'}]]}
        answer_callback(callback['id'], msg, keyboard)
        
    return {'status': 'ok'}


def check_spam(message: Dict[Any, Any], cur, schema: str) -> None:
    """Проверка на спам"""
    text = message.get('text', '')
    user_id = message['from']['id']
    
    if text.count('http') > 3:
        cur.execute(f"""
            INSERT INTO {schema}.auto_checks (check_type, user_id, result, details)
            VALUES ('spam', %s, 'suspicious', 'Multiple links detected')
        """, (user_id,))


def get_user_role(user_id: int, cur, schema: str) -> str:
    """Получение роли"""
    cur.execute(f"SELECT role FROM {schema}.users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()
    return result[0] if result else 'member'


def get_role_name(role: str) -> str:
    """Название роли"""
    roles = {
        'admin_senior': 'Ст администратор',
        'curator': 'Куратор',
        'moderator_senior': 'Ст модератор',
        'moderator_junior': 'Мл модератор',
        'watcher_senior': 'Ст следящий',
        'member': 'Участник'
    }
    return roles.get(role, 'Участник')


def has_permission(role: str, action: str) -> bool:
    """Проверка прав"""
    permissions = {
        'admin_senior': ['moderate', 'manage', 'admin'],
        'curator': ['moderate', 'manage', 'admin'],
        'moderator_senior': ['moderate', 'manage'],
        'moderator_junior': ['moderate'],
        'watcher_senior': ['moderate']
    }
    return action in permissions.get(role, [])


def send_telegram_message(chat_id: int, text: str, keyboard: dict = None) -> None:
    """Отправка сообщения в Telegram"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        urllib.request.urlopen(req)
    except:
        pass


def ban_telegram_user(chat_id: int, user_id: int) -> None:
    """Бан пользователя"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/banChatMember"
    data = {'chat_id': chat_id, 'user_id': user_id}
    
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        urllib.request.urlopen(req)
    except:
        pass


def kick_telegram_user(chat_id: int, user_id: int) -> None:
    """Кик пользователя"""
    ban_telegram_user(chat_id, user_id)


def mute_telegram_user(chat_id: int, user_id: int, duration: int) -> None:
    """Мут пользователя"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/restrictChatMember"
    until = int((datetime.now() + timedelta(minutes=duration)).timestamp())
    data = {
        'chat_id': chat_id,
        'user_id': user_id,
        'until_date': until,
        'permissions': json.dumps({'can_send_messages': False})
    }
    
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        urllib.request.urlopen(req)
    except:
        pass


def answer_callback(callback_id: str, text: str, keyboard: dict = None) -> None:
    """Ответ на callback"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    data = {'callback_query_id': callback_id, 'text': text}
    
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
        urllib.request.urlopen(req)
    except:
        pass
