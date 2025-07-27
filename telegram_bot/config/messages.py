"""
User Messages Configuration
All user-facing messages organized by language and context
"""

MESSAGES = {
    'welcome': {
        'en': "🎉 Welcome to StockBot!\n\nI'm here to help you with stock analysis and market insights. Let's get started!",
        'he': "🎉 ברוכים הבאים ל-StockBot!\n\nאני כאן כדי לעזור לכם עם ניתוח מניות ותובנות שוק. בואו נתחיל!"
    },
    
    'first_connection': {
        'en': "👋 Welcome! This is your first time here.\n\nI'll help you track and analyze your favorite stocks. Let's set up your account!",
        'he': "👋 ברוכים הבאים! זו הפעם הראשונה שלכם כאן.\n\nאני אעזור לכם לעקוב ולנתח את המניות האהובות עליכם. בואו נגדיר את החשבון שלכם!"
    },
    
    'menu': {
        'en': "📊 Here is the menu:\n\n1️⃣ Stock Analysis - Get analysis for your tickers\n2️⃣ Technical Analysis - Advanced charts and indicators\n3️⃣ Settings - Manage your account and preferences\n4️⃣ Payment - Upgrade your plan",
        'he': "📊 הנה התפריט:\n\n1️⃣ ניתוח מניות - קבל ניתוח עבור הטיקרים שלך\n2️⃣ ניתוח טכני - גרפים ואינדיקטורים מתקדמים\n3️⃣ הגדרות - נהל את החשבון והעדפות שלך\n4️⃣ תשלום - שדרג את התוכנית שלך"
    },
    
    'daily_analysis': {
        'en': "📈 Here's today's analysis, have a great day!\n\n",
        'he': "📈 הנה הניתוח של היום, יום טוב!\n\n"
    },
    
    'authentication': {
        'sign_in_prompt': {
            'en': "🔐 Please sign in to continue.\n\nEnter your email:",
            'he': "🔐 אנא התחבר כדי להמשיך.\n\nהזן את האימייל שלך:"
        },
        'sign_up_prompt': {
            'en': "📝 New user? Let's create your account.\n\nEnter your email:",
            'he': "📝 משתמש חדש? בואו ניצור את החשבון שלך.\n\nהזן את האימייל שלך:"
        },
        'phone_prompt': {
            'en': "📱 Please enter your phone number (with country code):",
            'he': "📱 אנא הזן את מספר הטלפון שלך (עם קוד מדינה):"
        },
        'success': {
            'en': "✅ Authentication successful! Welcome back!",
            'he': "✅ ההתחברות הצליחה! ברוכים השבים!"
        },
        'failed': {
            'en': "❌ Authentication failed. Please try again.",
            'he': "❌ ההתחברות נכשלה. אנא נסה שוב."
        },
        'cooldown': {
            'en': "⏰ Too many attempts. Please wait 30 minutes before trying again.",
            'he': "⏰ יותר מדי ניסיונות. אנא המתן 30 דקות לפני שתנסה שוב."
        }
    },
    
    'analysis': {
        'ticker_prompt': {
            'en': "📊 Enter a stock ticker (e.g., AAPL, TSLA):",
            'he': "📊 הזן טיקר מניה (למשל, AAPL, TSLA):"
        },
        'analysis_ready': {
            'en': "📈 Analysis ready for {ticker}:\n\n{analysis_text}",
            'he': "📈 הניתוח מוכן עבור {ticker}:\n\n{analysis_text}"
        },
        'ticker_not_found': {
            'en': "❌ Ticker '{ticker}' not found. Please check the symbol and try again.",
            'he': "❌ הטיקר '{ticker}' לא נמצא. אנא בדוק את הסמל ונסה שוב."
        },
        'technical_analysis': {
            'en': "📊 Technical Analysis for {ticker}:\n\n{analysis_text}",
            'he': "📊 ניתוח טכני עבור {ticker}:\n\n{analysis_text}"
        }
    },
    
    'error': {
        'en': "❌ An error occurred. Please try again later.",
        'he': "❌ אירעה שגיאה. אנא נסה שוב מאוחר יותר."
    },
    
    'errors': {
        'general': {
            'en': "❌ An error occurred. Please try again later.",
            'he': "❌ אירעה שגיאה. אנא נסה שוב מאוחר יותר."
        },
        'invalid_input': {
            'en': "❌ Invalid input. Please try again.",
            'he': "❌ קלט לא תקין. אנא נסה שוב."
        },
        'rate_limit': {
            'en': "⏰ Too many requests. Please wait a moment.",
            'he': "⏰ יותר מדי בקשות. אנא המתן רגע."
        }
    },
    
    'settings': {
        'menu': {
            'en': "⚙️ Settings Menu:\n\n1️⃣ Change Language\n2️⃣ Update Details\n3️⃣ Manage Stocks\n4️⃣ Adjust Weights\n5️⃣ Back to Main Menu",
            'he': "⚙️ תפריט הגדרות:\n\n1️⃣ שנה שפה\n2️⃣ עדכן פרטים\n3️⃣ נהל מניות\n4️⃣ התאם משקולות\n5️⃣ חזור לתפריט הראשי"
        },
        'language_prompt': {
            'en': "🌐 Choose your language:\n\n1️⃣ English\n2️⃣ עברית",
            'he': "🌐 בחר את השפה שלך:\n\n1️⃣ English\n2️⃣ עברית"
        },
        'ticker_add_prompt': {
            'en': "📈 Enter a ticker to add to your portfolio:",
            'he': "📈 הזן טיקר להוספה לתיק שלך:"
        },
        'ticker_remove_prompt': {
            'en': "🗑️ Choose a ticker to remove:\n\n{tickers_list}",
            'he': "🗑️ בחר טיקר להסרה:\n\n{tickers_list}"
        },
        'ticker_limit_reached': {
            'en': "⚠️ You've reached your ticker limit ({current}/{max}). Please remove a ticker first or upgrade your plan.",
            'he': "⚠️ הגעת למגבלת הטיקרים שלך ({current}/{max}). אנא הסר טיקר קודם או שדרג את התוכנית שלך."
        },
        'ticker_already_exists': {
            'en': "ℹ️ '{ticker}' is already in your portfolio.",
            'he': "ℹ️ '{ticker}' כבר בתיק שלך."
        },
        'ticker_added': {
            'en': "✅ '{ticker}' added to your portfolio!",
            'he': "✅ '{ticker}' נוסף לתיק שלך!"
        },
        'weights_prompt': {
            'en': "⚖️ Set weights for your tickers:\n\n{tickers_list}\n\nEnter weights as percentages (e.g., 40,30,30):",
            'he': "⚖️ הגדר משקולות עבור הטיקרים שלך:\n\n{tickers_list}\n\nהזן משקולות כאחוזים (למשל, 40,30,30):"
        },
        'weights_not_available': {
            'en': "⚠️ Weights feature is not available in your current plan.",
            'he': "⚠️ תכונת המשקולות אינה זמינה בתוכנית הנוכחית שלך."
        },
        'ticker_removed': {
            'en': "✅ '{ticker}' removed from your portfolio!",
            'he': "✅ '{ticker}' הוסר מהתיק שלך!"
        },
        'weights_prompt': {
            'en': "⚖️ Enter weights for your stocks (total should be 100%):\n\n{tickers_list}",
            'he': "⚖️ הזן משקולות עבור המניות שלך (הסכום צריך להיות 100%):\n\n{tickers_list}"
        },
        'weights_updated': {
            'en': "✅ Weights updated successfully!",
            'he': "✅ המשקולות עודכנו בהצלחה!"
        },
        'weights_not_available': {
            'en': "⚠️ Weights feature is not available in your current plan. Please upgrade to use this feature.",
            'he': "⚠️ תכונת המשקולות אינה זמינה בתוכנית הנוכחית שלך. אנא שדרג כדי להשתמש בתכונה זו."
        }
    },
    
    'payment': {
        'menu': {
            'en': "💳 Payment & Plans:\n\n1️⃣ View Current Plan\n2️⃣ Upgrade Plan\n3️⃣ Enter Coupon\n4️⃣ Back to Main Menu",
            'he': "💳 תשלום ותוכניות:\n\n1️⃣ צפה בתוכנית הנוכחית\n2️⃣ שדרג תוכנית\n3️⃣ הזן קופון\n4️⃣ חזור לתפריט הראשי"
        },
        'plan_expired': {
            'en': "⚠️ Your plan has expired. Please renew to continue using premium features.",
            'he': "⚠️ התוכנית שלך פגה. אנא חדש כדי להמשיך להשתמש בתכונות פרימיום."
        },
        'available_plans': {
            'en': "📋 Available Plans:\n\n{plans_list}",
            'he': "📋 תוכניות זמינות:\n\n{plans_list}"
        },
        'coupon_prompt': {
            'en': "🎫 Enter your coupon code (or skip by sending 'skip'):",
            'he': "🎫 הזן את קוד הקופון שלך (או דלג על ידי שליחת 'skip'):"
        },
        'coupon_applied': {
            'en': "✅ Coupon applied! Discount: {discount}%",
            'he': "✅ הקופון הוחל! הנחה: {discount}%"
        },
        'coupon_invalid': {
            'en': "❌ Invalid coupon code. Please try again or skip.",
            'he': "❌ קוד קופון לא חוקי. אנא נסה שוב או דלג."
        },
        'payment_summary': {
            'en': "💰 Payment Summary:\n\nPlan: {plan}\nPrice: ${price}\nDiscount: {discount}%\nFinal Price: ${final_price}\n\nProceed with payment?",
            'he': "💰 סיכום תשלום:\n\nתוכנית: {plan}\nמחיר: ${price}\nהנחה: {discount}%\nמחיר סופי: ${final_price}\n\nהמשך לתשלום?"
        },
        'payment_success': {
            'en': "✅ Payment successful! Your plan has been upgraded. Thank you!",
            'he': "✅ התשלום הצליח! התוכנית שלך שודרגה. תודה!"
        },
        'payment_failed': {
            'en': "❌ Payment failed. Please try again or contact support.",
            'he': "❌ התשלום נכשל. אנא נסה שוב או פנה לתמיכה."
        }
    },
    
    'errors': {
        'general': {
            'en': "❌ Something went wrong. Please try again later.",
            'he': "❌ משהו השתבש. אנא נסה שוב מאוחר יותר."
        },
        'invalid_input': {
            'en': "❌ Invalid input. Please check your message and try again.",
            'he': "❌ קלט לא חוקי. אנא בדוק את ההודעה שלך ונסה שוב."
        },
        'database_error': {
            'en': "❌ Database error. Please try again later.",
            'he': "❌ שגיאת מסד נתונים. אנא נסה שוב מאוחר יותר."
        },
        'rate_limit': {
            'en': "⏰ Too many requests. Please wait a moment before trying again.",
            'he': "⏰ יותר מדי בקשות. אנא המתן רגע לפני שתנסה שוב."
        }
    },
    
    'navigation': {
        'back': {
            'en': "⬅️ Back",
            'he': "⬅️ חזור"
        },
        'main_menu': {
            'en': "🏠 Main Menu",
            'he': "🏠 תפריט ראשי"
        },
        'cancel': {
            'en': "❌ Cancel",
            'he': "❌ ביטול"
        }
    }
}

def get_message(key: str, language: str = 'en', **kwargs) -> str:
    """
    Get a message by key and language, with optional formatting
    
    Args:
        key: Message key (e.g., 'welcome', 'menu')
        language: Language code ('en' or 'he')
        **kwargs: Format parameters for the message
    
    Returns:
        Formatted message string
    """
    try:
        # Navigate nested keys (e.g., 'authentication.sign_in_prompt')
        keys = key.split('.')
        message = MESSAGES
        for k in keys:
            message = message[k]
        
        # Get message for language
        if language in message:
            msg = message[language]
        else:
            msg = message['en']  # Fallback to English
        
        # Format with kwargs if provided
        if kwargs:
            msg = msg.format(**kwargs)
        
        return msg
    except (KeyError, AttributeError):
        # Fallback to error message
        return MESSAGES['errors']['general'][language] 