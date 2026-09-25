import smtplib
from email.message import EmailMessage

# ضع إيميلك هنا
sender_email = "zaid.said1109@gmail.com" 

app_password = "lcwxidolcaomsfia" 

msg = EmailMessage()
msg['Subject'] = 'تجربة إرسال إيميل من نظام الذكاء الاصطناعي'
msg['From'] = sender_email
msg['To'] = sender_email  
msg.set_content("إذا وصلك هذا الإيميل، فهذا يعني أن نظام المهام يعمل بنجاح!")

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)
    print("--- تم إرسال الإيميل بنجاح! تحقق من صندوق الوارد ---")
except Exception as e:
    print(f"--- حدث خطأ: {e} ---")