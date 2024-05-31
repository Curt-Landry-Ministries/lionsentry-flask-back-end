def format_email(devotional_content):
    email_lines = []
    for header, body in devotional_content.items():
        email_lines.append(f"<strong>{header}</strong><br>")
        email_lines.append(f"{body}<br><br>")  # Adds line breaks for separation

    return "\n".join(email_lines)

