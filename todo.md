
# 🧾 To-Do List — Poker Project

## 🔐 Authentication & Registration

### 1. הוסף אימות מייל בהרשמה
**קבצים מעורבים:** `auth/routes.py`, `models/verification_token.py`, `utils/email.py`

- כאשר שחקן נרשם:
  - צור טוקן ייחודי ושמור אותו בטבלה חדשה בשם `email_verification_tokens` עם זמן תפוגה.
  - שלח לשחקן מייל עם קישור כמו: `https://yourdomain.com/verify?token=XYZ`.
  - צור route בשם `/verify` שיאמת את המשתמש אם הטוקן תקף.
  - חסום כניסה ב-`/login` אם `user.is_verified == False`.

**קוד לדוגמה:**

```python
# צור טוקן ושמור אותו בבסיס הנתונים
def generate_verification_token(user_id):
    token = some_token_generation_method()
    expiry = datetime.now() + timedelta(hours=24)
    new_token = VerificationToken(user_id=user_id, token=token, expiry=expiry)
    db.session.add(new_token)
    db.session.commit()
    send_verification_email(user_id, token)
````

### 2. הסר את הצ'יפים האוטומטיים של 1000 בעת ההרשמה

**קובץ:** `models/user.py`
**פעולה:** הסר את ברירת המחדל `1000` מעמודת הצ'יפים בבסיס הנתונים.

```python
# לפני:
chips = db.Column(db.Integer, default=1000)

# אחרי:
chips = db.Column(db.Integer, default=0)
```

* **סיבה:** אין להעניק אוטומטית 1000 צ'יפים בשעת ההרשמה. יש להעניק צ'יפים לאחר תשלום או בצורה ידנית על ידי המנהל.

**צור פונקציה ב-`utils/payments.py` או `services/chips.py` להענקת צ'יפים לאחר תשלום:**

```python
def grant_initial_chips(user_id, amount=1000):
    user = User.query.get(user_id)
    user.chips += amount
    db.session.commit()
```

---

## 🧭 Navigation & UI

### 3. הוסף Navbar שיציג את שם המשתמש והבלאנס, עם אפשרות להתחבר ולהתנתק

**קבצים מעורבים:** `components/Navbar.js`, `redux/actions.js`, `redux/reducers.js`

* הוסף navbar שמציג:

  * את שם המשתמש (`nickname`) ואת הבלאנס.
  * כפתור `Login` אם המשתמש לא מחובר.
  * כפתור `Logout` אם המשתמש מחובר.
  * קישורים להתחברות/הרשמה אם המשתמש לא מחובר.

**קוד לדוגמה ל-Navbar (React):**

```jsx
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from './redux/actions';  // פעולה ליציאה

const Navbar = () => {
  const dispatch = useDispatch();
  const user = useSelector(state => state.user);  // נניח שהמידע על המשתמש נמצא ב-Redux
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    if (user) {
      setBalance(user.balance);  // קביעת הבלאנס מתוך המידע על המשתמש
    }
  }, [user]);

  const handleLogout = () => {
    dispatch(logout());  // פעולה להתנתקות
  };

  return (
    <nav>
      <div className="navbar">
        {user ? (
          <div className="navbar-info">
            <span>{user.nickname}</span>
            <span>Balance: ${balance}</span>
            <button onClick={handleLogout}>Logout</button>
          </div>
        ) : (
          <div className="navbar-actions">
            <button onClick={() => window.location.href = '/login'}>Login</button>
            <button onClick={() => window.location.href = '/register'}>Register</button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
```

---

## 🧠 Game Logic

### 4. הפרד את הלוגיקה של כל סיבוב (פרה-פלופ, פלופ, טרן, ריבר)

מטרה: כל שלב (סיבוב) במשחק יהיה מטופל בפונקציה נפרדת.

**מבנה מוצע ב-`game/engine/turn_logic.py`:**

```python
def handle_preflop_betting(state):
    # לוגיקה של פרה-פלופ
    pass

def handle_flop_betting(state):
    # לוגיקה של פלופ
    pass

def handle_turn_betting(state):
    # לוגיקה של טרן
    pass

def handle_river_betting(state):
    # לוגיקה של ריבר
    pass
```

**שימוש בלוגיקה הראשית:**

```python
if state["stage"] == "preflop":
    handle_preflop_betting(state)
elif state["stage"] == "flop":
    handle_flop_betting(state)
elif state["stage"] == "turn":
    handle_turn_betting(state)
elif state["stage"] == "river":
    handle_river_betting(state)
```

לאחר כל פעולה, יש לבדוק אם סבב ההימורים צריך להסתיים ולהתקדם לשלב הבא.

### 5. טיפול בשואודאון ובדיקת עוצמת הידיים

* **לוגיקת שואודאון:** בסיום סבב ההימורים, יש לבדוק אם יש שואודאון, לחשוף את קלפי השחקנים ולבדוק מי הזוכה על פי עוצמת היד.
* **חישוב עוצמת היד:** יש לממש פונקציה להשוואת הידיים ולבדוק מי הזוכה (למשל, זוג, שלישייה, וכדומה).

**דוגמת פונקציה לחישוב עוצמת היד:**

```python
def evaluate_hand(player_hand, community_cards):
    # לוגיקה לחישוב עוצמת היד והחזרת דירוג היד
    pass
```

### 6. טיפול במצבי All-in וקופות צדדיות

* **לוגיקת All-in:** אם שחקן הולך על All-in, יש לחשב את הקופה הראשית ואת הקופות הצדדיות (אם יש כאלה).
* **טיפול בקופות צדדיות:** יש לוודא שהקופות הצדדיות יחולקו כראוי לפי הידיים של השחקנים הנותרים.

**דוגמה:**

```python
def handle_all_in(player, bet_amount):
    if player.chips <= bet_amount:
        # טיפול במצב All-in, עדכון הקופות בהתאם
        pass
```

---

## ⚠️ Player Disconnection & Leaving Table

### 7. טיפול בשחקן שעוזב את השולחן (באמצע יד או יציאה מהאתר)

* **שחקן עוזב באמצע יד:** אם שחקן עוזב את השולחן באמצע יד, יש להתייחס אליו כמי שפרש או לבצע אוטומטית פעולה של "Check".
* **שחקן שמתנתק:** אם שחקן מתנתק מהאתר באופן לא רשמי, יש לוודא שהוא יתייחס כמי שפרש או שהמשחק יעצור עד שיתחבר מחדש.
* **טיפול במצב חיבור מחדש:** יש לממש לוגיקה שתטפל במצב של שחקן שחוזר למשחק לאחר שהתנתק.

**דוגמה:**

```python
def handle_player_disconnect(player):
    if player.is_in_hand:
        # לפרוש את השחקן או להפסיק את המשחק עד שהוא יתחבר מחדש
        pass
```

---

🗓️ **Last updated:** June 23, 2025