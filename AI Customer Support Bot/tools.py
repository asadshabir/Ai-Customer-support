from agents import function_tool
import difflib
import ddgs as DDGS
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



with open("faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

@function_tool
def web_search(query: str) -> str:
    """Fetch latest info from DuckDuckGo search."""
    try:
        with DDGS() as ddgs:
            results = [r["body"] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results)
    except Exception as e:
        return f"❌ Web search failed: {e}"


@function_tool
def get_faqs(query: str) -> str:
    """Get the FAQs for the product"""
    best_match = None
    highest_ratio = 0.0
    
    for faq in faqs:
        ratio = difflib.SequenceMatcher(None, faq["question"].lower(), query.lower()).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = faq
    
    if best_match and highest_ratio > 0.5:  # 50% similarity threshold
        return best_match["answer"]



@function_tool
def send_user_email(user_email: str, subject: str, body: str) -> str:
    """
    Sends an email from your Gmail to the user's email address.
    """
    try:
        sender_email = "asadshabir505@gmail.com"   # 👈 apni Gmail
        app_password = "doeqgaztlxkduwyg"          # 👈 App Password (16-char)

        # Email format
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["Reply-To"] = sender_email
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()

        
        return f"✅ Email sent to {user_email} with subject: {subject}"

    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"
    

