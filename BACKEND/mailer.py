import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

# ✅ 配置 126 邮箱 (NetEase)
SMTP_SERVER = "smtp.126.com"
SMTP_PORT = 465
SMTP_LOGIN = "xinccp@126.com"
SMTP_PASSWORD = "ZSrv7U36s3CyxaU2" # 你的授权码
SENDER_EMAIL = SMTP_LOGIN          # 发件人通常就是登录账号
SENDER_NAME = "Cattle Match System"

def send_match_email(to_email: str, subject: str, match_details: Dict):
    """
发送 HTML 格式的匹配通知邮件 (适配 126 邮箱 SSL)
    """
    # 1. 简单校验
    if "@" not in to_email or "." not in to_email:
        print(f"⚠️ Skipped email for non-email contact: {to_email}")
        return

    try:
        # 2. 构建邮件对象
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = f"🔔 {subject}"

        # 3. 构建 HTML 内容
        html_content = f"""
<html>
<body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6;">
<div style="max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
<div style="background: #c0392b; color: white; padding: 20px; text-align: center;">
<h2 style="margin: 0;">Match Found</h2>
</div>
<div style="padding: 30px;">
<p>Hello,</p>
<p>Great news! The system has identified a potential match for your listing.</p>

<div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #c0392b;">
<h3 style="margin-top: 0; color: #2c3e50;">Match Details</h3>
<ul style="list-style: none; padding: 0;">
            <li><strong>Role:</strong> {match_details.get('role', 'Partner')}</li>
            <li><strong>Race:</strong> {match_details.get('race', 'N/A')}</li>
            <li><strong>Location:</strong> {match_details.get('location', 'N/A')}</li>
            <li><strong>Quantity:</strong> {match_details.get('qty', 'N/A')}</li>
</ul>
</div>

<p style="font-size: 0.9em; color: #666;">
Log in to your dashboard to view contact details.
</p>

<a href="https://bi.cool/full/project/tx7C2rt" style="display: inline-block; background: #2c3e50; color: white; text-decoration: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; margin-top: 10px;">Go to Dashboard</a>
</div>
</div>
</body>
</html>
            """

        msg.attach(MIMEText(html_content, 'html'))

        # 4. 连接服务器 (126邮箱专用逻辑：使用 SMTP_SSL)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_LOGIN, SMTP_PASSWORD)

        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()

        print(f"✅ Email sent successfully to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

# 本地测试
if __name__ == "__main__":
    # 在这里填入你的接收邮箱测试一下
    send_match_email("959489042@qq.com", "Test Subject", {"role": "Tester", "race": "Angus"})

def send_contact_info_email(to_email: str, listing_details: Dict):
    """
发送解锁后的联系方式给请求者
    """
    subject = "🔓 Unlocked: Contact Details for Your Interest"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        html_content = f"""
<html>
<body style="font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.6;">
<div style="max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
<div style="background: #34495e; color: white; padding: 20px; text-align: center;">
<h2 style="margin: 0;">Contact Details Unlocked</h2>
</div>
<div style="padding: 30px;">
<p>Hello,</p>
<p>You have successfully unlocked the contact information for the following listing:</p>

<div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #34495e;">
<ul style="list-style: none; padding: 0;">
            <li><strong>Listing Type:</strong> {listing_details.get('type')}</li>
            <li><strong>Race:</strong> {listing_details.get('race')}</li>
            <li><strong>Location:</strong> {listing_details.get('location')}</li>
<li style="margin-top: 10px; font-size: 1.1em; color: #c0392b;">
            <strong>📞 Contact: {listing_details.get('contact')}</strong>
</li>
</ul>
</div>

<p style="font-size: 0.9em; color: #666;">
Good luck with your negotiation!
</p>
</div>
</div>
</body>
</html>
            """

        msg.attach(MIMEText(html_content, 'html'))

        # 连接服务器 (复用上面的 SSL 配置)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Contact info sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send contact info: {e}") 