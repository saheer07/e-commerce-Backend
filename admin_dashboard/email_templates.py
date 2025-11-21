# admin_dashboard/email_templates.py
# Create this new file for email templates

from django.conf import settings
from django.utils import timezone


def get_block_email_template(user, custom_message=None):
    """Get HTML email template for blocking user"""
    if custom_message:
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 40px 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ padding: 40px 30px; }}
        .alert-box {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .message-box {{ background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .message-box h3 {{ margin-top: 0; color: #1f2937; }}
        .contact-support {{ background-color: #dbeafe; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        .contact-support a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
        .footer {{ background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Account Suspended</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user.username}</strong>,</p>
            <div class="alert-box">
                <p><strong>Your account access has been suspended by our administration team.</strong></p>
            </div>
            <div class="message-box">
                <h3>Message from Admin:</h3>
                <p>{custom_message}</p>
            </div>
            <div class="contact-support">
                <p><strong>Need Help?</strong></p>
                <p>If you have questions or concerns, please contact our support team:</p>
                <p><a href="mailto:{settings.DEFAULT_FROM_EMAIL}">{settings.DEFAULT_FROM_EMAIL}</a></p>
            </div>
        </div>
        <div class="footer">
            <p><strong>Admin Team</strong></p>
            <p>This is an automated message. Please do not reply to this email.</p>
            <p style="margin-top: 15px; font-size: 12px;">© {timezone.now().year} Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    else:
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 40px 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ padding: 40px 30px; }}
        .alert-box {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .alert-box h2 {{ color: #dc2626; margin: 0 0 10px 0; font-size: 20px; }}
        .info-section {{ background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .info-section h3 {{ color: #1f2937; margin: 0 0 15px 0; font-size: 16px; }}
        .info-section ul {{ margin: 0; padding-left: 20px; }}
        .info-section li {{ margin: 8px 0; color: #4b5563; }}
        .contact-support {{ background-color: #dbeafe; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        .contact-support a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
        .footer {{ background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Account Suspended</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user.username}</strong>,</p>
            <div class="alert-box">
                <h2>Your Account Has Been Suspended</h2>
                <p>We regret to inform you that your account access has been temporarily suspended by our administration team.</p>
            </div>
            <div class="info-section">
                <h3>What This Means:</h3>
                <ul>
                    <li>You will not be able to log in to your account</li>
                    <li>Your active orders and cart items are preserved</li>
                    <li>Your account data remains secure</li>
                    <li>This action may be reviewed and reversed</li>
                </ul>
            </div>
            <div class="contact-support">
                <p><strong>Need Help?</strong></p>
                <p>If you believe this is a mistake or would like more information, please contact our support team:</p>
                <p><a href="mailto:{settings.DEFAULT_FROM_EMAIL}">{settings.DEFAULT_FROM_EMAIL}</a></p>
            </div>
            <p style="margin-top: 30px;">We appreciate your understanding and cooperation.</p>
        </div>
        <div class="footer">
            <p><strong>Admin Team</strong></p>
            <p>This is an automated message. Please do not reply to this email.</p>
            <p style="margin-top: 15px; font-size: 12px;">© {timezone.now().year} Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    return template


def get_unblock_email_template(user, custom_message=None):
    """Get HTML email template for unblocking user"""
    if custom_message:
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 40px 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ padding: 40px 30px; }}
        .success-box {{ background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .message-box {{ background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .message-box h3 {{ margin-top: 0; color: #1f2937; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .footer {{ background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Account Restored</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user.username}</strong>,</p>
            <div class="success-box">
                <p><strong>Your account access has been restored!</strong></p>
            </div>
            <div class="message-box">
                <h3>Message from Admin:</h3>
                <p>{custom_message}</p>
            </div>
            <div style="text-align: center;">
                <a href="#" class="cta-button">Login to Your Account</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>Admin Team</strong></p>
            <p>If you have any questions, contact us at <a href="mailto:{settings.DEFAULT_FROM_EMAIL}" style="color: #2563eb;">{settings.DEFAULT_FROM_EMAIL}</a></p>
            <p style="margin-top: 15px; font-size: 12px;">© {timezone.now().year} Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    else:
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 40px 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ padding: 40px 30px; }}
        .success-box {{ background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .success-box h2 {{ color: #16a34a; margin: 0 0 10px 0; font-size: 20px; }}
        .info-section {{ background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .info-section h3 {{ margin-top: 0; color: #1f2937; }}
        .info-section ul {{ margin: 0; padding-left: 20px; color: #4b5563; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .footer {{ background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb; }}
        .footer p {{ margin: 5px 0; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Account Restored</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{user.username}</strong>,</p>
            <div class="success-box">
                <h2>Your Account Has Been Restored!</h2>
                <p>We're pleased to inform you that your account access has been fully restored.</p>
            </div>
            <div class="info-section">
                <h3>You Can Now:</h3>
                <ul>
                    <li>Log in to your account</li>
                    <li>Access all features and services</li>
                    <li>Continue shopping and placing orders</li>
                    <li>Manage your cart and wishlist</li>
                </ul>
            </div>
            <div style="text-align: center;">
                <a href="#" class="cta-button">Login to Your Account</a>
            </div>
            <p style="margin-top: 30px;">Thank you for your patience and understanding.</p>
        </div>
        <div class="footer">
            <p><strong>Admin Team</strong></p>
            <p>If you have any questions, contact us at <a href="mailto:{settings.DEFAULT_FROM_EMAIL}" style="color: #2563eb;">{settings.DEFAULT_FROM_EMAIL}</a></p>
            <p style="margin-top: 15px; font-size: 12px;">© {timezone.now().year} Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    return template