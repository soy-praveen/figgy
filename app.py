from flask import Flask, jsonify, request
import random
import string
import sqlite3
import time
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

app = Flask(__name__)

# Telegram bot setup
TELEGRAM_TOKEN = "1234"  # Replace with your actual token
bot = Bot(token=TELEGRAM_TOKEN)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            referral_link TEXT,
            referred_by TEXT,
            earnings REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Generate unique referral link for the user
@app.route('/api/generate-referral', methods=['GET'])
def generate_referral():
    user_id = request.args.get('user_id', ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
    referral_link = f'https://yourwebsite.com/register?ref={user_id}'
    
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    c.execute('INSERT OR IGNORE INTO users (user_id, referral_link) VALUES (?, ?)', (user_id, referral_link))
    conn.commit()
    conn.close()
    
    return jsonify({"referralLink": referral_link})

# Track referral signups
@app.route('/register', methods=['GET'])
def register_user():
    referred_by = request.args.get('ref')
    new_user_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Insert the new user and associate them with the referrer
    c.execute('INSERT INTO users (user_id, referred_by) VALUES (?, ?)', (new_user_id, referred_by))
    conn.commit()
    conn.close()
    
    return "You have successfully registered! Start earning now!"

# Function to update referrer earnings
def update_earnings():
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Fetch all users and their referrers
    c.execute('SELECT u1.user_id, u2.referred_by, u1.earnings FROM users u1 INNER JOIN users u2 ON u1.user_id = u2.referred_by')
    referrals = c.fetchall()
    
    # Add 10% of referred user's earnings to the referrer
    for referral in referrals:
        referrer_id, referee_id, referee_earnings = referral
        bonus = 0.1 * referee_earnings
        
        c.execute('UPDATE users SET earnings = earnings + ? WHERE user_id = ?', (bonus, referrer_id))
        conn.commit()
    
    conn.close()

# Schedule earnings update every minute
scheduler = BackgroundScheduler()
scheduler.add_job(update_earnings, 'interval', minutes=1)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
