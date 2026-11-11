import os
import resend


def send_verification_email(recipient, verification_url):
    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError("Resend API key is missing")

    sender = os.getenv(
        "RESEND_FROM_EMAIL",
        "onboarding@resend.dev"
    )

    resend.api_key = api_key

    params = {
        "from": sender,
        "to": [recipient],
        "subject": "Verify your Medi-One account",
        "html": f"""
            <h2>Welcome to Medi-One</h2>
            <p>Please verify your email address to activate your account.</p>
            <p>
                <a href="{verification_url}">
                    Verify My Email
                </a>
            </p>
            <p>If you did not create this account, ignore this email.</p>
        """
    }

    return resend.Emails.send(params)