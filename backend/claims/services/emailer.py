def send_mock_email(to: str, subject: str, body: str):
    """Mock email sending function for simulator"""
    return {"to": to, "subject": subject, "body": body, "provider": "mock"}
