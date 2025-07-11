import redis

# פרטי ההתחברות
REDIS_HOST = "redis-14215.c258.us-east-1-4.ec2.redns.redis-cloud.com"
REDIS_PORT = 14215
REDIS_PASSWORD = "4Bv9zP9ZWbxqJUdJcptJ7ECFOk0HUM6D"

# התחברות
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# בדיקת התחברות
try:
    print("🔄 מנסה להתחבר ל-Redis...")
    redis_client.ping()
    print("✅ התחברת בהצלחה ל-Redis!")

    # איפוס הנתונים
    redis_client.flushdb()
    print("🧹 בסיס הנתונים של Redis אופס בהצלחה.")

except redis.exceptions.ConnectionError as e:
    print("❌ שגיאת התחברות ל-Redis:", str(e))
except redis.exceptions.AuthenticationError as e:
    print("❌ שגיאת אימות ל-Redis (סיסמה לא נכונה?):", str(e))
