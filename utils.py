RISK_COLORS = {
    "safe":       {"bg": "#d1fae5", "text": "#065f46", "border": "#6ee7b7", "hex": "#10b981"},
    "suspicious": {"bg": "#fef9c3", "text": "#713f12", "border": "#fde047", "hex": "#eab308"},
    "high_risk":  {"bg": "#fee2e2", "text": "#7f1d1d", "border": "#fca5a5", "hex": "#ef4444"},
}

RISK_EMOJI = {
    "safe": "✅",
    "suspicious": "⚠️",
    "high_risk": "🚨",
}

SAMPLE_MESSAGES = {
    "Hindi OTP Scam": "आपका SBI बैंक खाता बंद हो जाएगा। अभी अपना OTP शेयर करें। तुरंत इस नंबर पर कॉल करें 9876543210 वरना आपका खाता 24 घंटे में बंद हो जाएगा।",
    "Marathi KYC Scam": "तुमचे बँक खाते KYC अपडेट न केल्याने बंद होईल. आत्ताच 1800-XXX-XXXX वर कॉल करा आणि तुमचा ATM PIN सांगा. हे सरकारी नोटीस आहे.",
    "Tamil Lottery Scam": "வாழ்த்துக்கள்! நீங்கள் KBC லாட்டரியில் ₹50 லட்சம் வென்றீர்கள். உங்கள் Aadhaar மற்றும் வங்கி விவரங்களை உடனடியாக அனுப்புங்கள்.",
    "English Prize Scam": "URGENT: Your number has won ₹25 lakh in RBI lucky draw. Send Aadhaar card + bank account details to claim prize. Offer expires in 2 hours!",
    "Safe Message": "Hi, your Flipkart order #45892 has been shipped. Expected delivery in 3 days. Track at flipkart.com/orders. No action needed.",
}

TACTIC_DESCRIPTIONS = {
    "Urgency / Time pressure": "Creates artificial deadline to prevent rational thinking",
    "Fear / Threat": "Threatens account closure, legal action, or arrest",
    "Authority impersonation": "Pretends to be RBI, CBI, bank, police or government",
    "OTP / Password request": "Asks for OTP, PIN, or password — banks never do this",
    "Fake reward / Prize": "Offers lottery winnings or prizes to lure victims",
    "Personal info request": "Asks for Aadhaar, PAN, bank details",
}


def highlight_text_html(text: str, highlights: list) -> str:
    if not highlights or not text:
        return f"<p style='font-size:15px;line-height:1.8'>{text}</p>"
    result = text
    seen = set()
    sorted_h = sorted(highlights, key=lambda x: len(x.get("phrase", "")), reverse=True)
    for h in sorted_h:
        phrase = h.get("phrase", "").strip()
        reason = h.get("reason", "Suspicious phrase")
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)
        escaped_reason = reason.replace("'", "&#39;")
        highlighted = (
            f'<mark title="{escaped_reason}" style="background:#fef08a;'
            f'border-bottom:2.5px solid #eab308;border-radius:3px;'
            f'padding:1px 3px;cursor:help;font-weight:500">{phrase}</mark>'
        )
        result = result.replace(phrase, highlighted, 1)
    return f"<div style='font-size:15px;line-height:1.9;padding:12px'>{result}</div>"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    return f"{size_bytes/(1024*1024):.1f} MB"