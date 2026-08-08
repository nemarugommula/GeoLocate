from __future__ import annotations
import re

SCRIPT_TO_COUNTRY = {
    "sinhala": ["Sri Lanka"],
    "tamil": ["Sri Lanka", "India", "Singapore"],
    "devanagari": ["India", "Nepal"],
    "thai": ["Thailand"],
    "arabic": ["Middle East / North Africa"],
    "chinese": ["China", "Taiwan", "Singapore"],
    "japanese": ["Japan"],
    "korean": ["South Korea"],
}

COUNTRY_NAMES = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria",
    "Bangladesh", "Belgium", "Bhutan", "Bolivia", "Brazil", "Cambodia", "Canada",
    "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Cuba", "Czech",
    "Denmark", "Ecuador", "Egypt", "England", "Ethiopia", "Finland", "France",
    "Germany", "Ghana", "Greece", "Guatemala", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kenya", "Korea", "Laos", "Lebanon", "Malaysia",
    "Maldives", "Mexico", "Mongolia", "Morocco", "Myanmar", "Nepal",
    "Netherlands", "New Zealand", "Nigeria", "Norway", "Pakistan", "Panama",
    "Peru", "Philippines", "Poland", "Portugal", "Romania", "Russia",
    "Saudi Arabia", "Scotland", "Singapore", "South Africa", "Spain",
    "Sri Lanka", "Sweden", "Switzerland", "Taiwan", "Tanzania", "Thailand",
    "Turkey", "Uganda", "Ukraine", "United Kingdom", "United States",
    "Uruguay", "Venezuela", "Vietnam", "Wales", "Yunnan", "Kerala",
    "Rajasthan", "Bali", "Tuscany", "Patagonia", "Hokkaido",
]


def detect_scripts(text: str) -> list[str]:
    scripts = set()
    for ch in text:
        cp = ord(ch)
        if 0x0D80 <= cp <= 0x0DFF:
            scripts.add("sinhala")
        elif 0x0B80 <= cp <= 0x0BFF:
            scripts.add("tamil")
        elif 0x0900 <= cp <= 0x097F:
            scripts.add("devanagari")
        elif 0x0E00 <= cp <= 0x0E7F:
            scripts.add("thai")
        elif 0x0600 <= cp <= 0x06FF:
            scripts.add("arabic")
        elif 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            scripts.add("chinese")
        elif 0x3040 <= cp <= 0x30FF:
            scripts.add("japanese")
        elif 0xAC00 <= cp <= 0xD7AF:
            scripts.add("korean")
    return list(scripts)


def extract_country_mentions(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for name in COUNTRY_NAMES:
        if name.lower() in text_lower:
            found.append(name)
    return found


def extract_location_hints(title: str, description: str, channel_name: str) -> dict:
    combined = f"{title} {description} {channel_name}"

    scripts = detect_scripts(combined)
    country_hints_from_scripts = []
    for s in scripts:
        country_hints_from_scripts.extend(SCRIPT_TO_COUNTRY.get(s, []))

    country_mentions = extract_country_mentions(combined)

    place_pattern = r'\b(?:in|from|near|at|visiting)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    place_matches = re.findall(place_pattern, f"{title} {description}")

    return {
        "scripts_detected": scripts,
        "country_hints_from_scripts": list(set(country_hints_from_scripts)),
        "country_mentions": list(set(country_mentions)),
        "place_names": list(set(place_matches)),
        "title": title,
        "channel_name": channel_name,
    }
