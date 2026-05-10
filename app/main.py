from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="KI Commerce OS Platforms", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PRODUCTS_FILE = DATA_DIR / "products.csv"
CONTENT_FILE = DATA_DIR / "content.csv"
PLATFORMS_FILE = DATA_DIR / "platforms.json"
ANALYTICS_FILE = DATA_DIR / "analytics.csv"
LEARNINGS_FILE = DATA_DIR / "learnings.csv"


templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

DEFAULT_PLATFORMS = [
    {"name": "YouTube Shorts", "type": "Short Video", "active": True},
    {"name": "YouTube Longform", "type": "Long Video", "active": True},
    {"name": "TikTok", "type": "Short Video", "active": True},
    {"name": "Instagram Reels", "type": "Short Video", "active": True},
    {"name": "Facebook", "type": "Social", "active": True},
    {"name": "LinkedIn", "type": "Business", "active": True},
    {"name": "Pinterest", "type": "Search/Social", "active": True},
]


def ensure_files() -> None:
    if not PLATFORMS_FILE.exists():
        PLATFORMS_FILE.write_text(json.dumps(DEFAULT_PLATFORMS, ensure_ascii=False, indent=2), encoding="utf-8")
    if not PRODUCTS_FILE.exists():
        write_csv(PRODUCTS_FILE, ["id", "name", "target_group", "problem", "buy_price", "sell_price", "status"], [])
    if not CONTENT_FILE.exists():
        write_csv(CONTENT_FILE, ["id", "product_id", "platform", "title", "hook", "caption", "hashtags", "status", "created_at"], [])
    if not ANALYTICS_FILE.exists():
        write_csv(ANALYTICS_FILE, ["id", "content_id", "platform", "views", "likes", "comments", "sales", "learning"], [])
    if not LEARNINGS_FILE.exists():
        write_csv(LEARNINGS_FILE, ["id", "area", "insight", "action", "created_at"], [])


def read_csv(path: Path) -> List[Dict[str, str]]:
    ensure_files_basic(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ensure_files_basic(path: Path) -> None:
    if not path.exists():
        ensure_files()


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_csv(path: Path, fieldnames: List[str], row: Dict[str, str]) -> None:
    rows = read_csv(path)
    rows.append(row)
    write_csv(path, fieldnames, rows)


def next_id(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "1"
    return str(max(int(r.get("id", "0") or 0) for r in rows) + 1)


def load_platforms() -> List[Dict[str, object]]:
    ensure_files()
    return json.loads(PLATFORMS_FILE.read_text(encoding="utf-8"))


def platform_adapter(platform: str, product: Dict[str, str]) -> Dict[str, str]:
    name = product.get("name", "Produkt")
    target = product.get("target_group", "Kunden")
    problem = product.get("problem", "ein Alltagsproblem")

    base_hook = f"Warum {target} dieses Problem kennen: {problem}"
    hashtags_common = "#fahrrad #sicherheit #alltag #produkttest #kauftipp"

    if "YouTube Shorts" in platform:
        return {
            "title": f"{name}: Besser sichtbar in 60 Sekunden",
            "hook": base_hook,
            "caption": f"Kurzer Test: Wie {name} bei {problem} helfen kann.",
            "hashtags": hashtags_common + " #shorts #youtubeshorts",
        }
    if "YouTube Longform" in platform:
        return {
            "title": f"{name} im Test: Lohnt sich das für {target}?",
            "hook": f"Heute prüfen wir, ob {name} wirklich bei {problem} hilft.",
            "caption": f"Ausführlicher Test mit Vorteilen, Nachteilen, Einsatzbeispielen und Kaufkriterien für {target}.",
            "hashtags": hashtags_common + " #review #testbericht",
        }
    if "TikTok" in platform:
        return {
            "title": f"{name} Kurztest",
            "hook": f"Viele unterschätzen dieses Risiko: {problem}",
            "caption": f"Kleine Lösung, großer Unterschied. {name} im Alltagstest.",
            "hashtags": hashtags_common + " #tiktokshop #viral",
        }
    if "Instagram" in platform:
        return {
            "title": f"{name} Alltagstest",
            "hook": "Sicherer unterwegs mit einer einfachen Lösung.",
            "caption": f"Für {target}: praktisch, einfach und schnell gezeigt. Speichern für später 🚴",
            "hashtags": hashtags_common + " #reels #instareels",
        }
    if "Facebook" in platform:
        return {
            "title": f"Praktischer Tipp: {name}",
            "hook": f"Wer {problem} kennt, sollte diese einfache Lösung ansehen.",
            "caption": f"Ein verständlicher Produkttipp für {target}. Einfach erklärt und alltagstauglich.",
            "hashtags": "#fahrrad #sicherheit #alltagstipp",
        }
    if "LinkedIn" in platform:
        return {
            "title": f"Produktsicherheit im Alltag: Beispiel {name}",
            "hook": f"Ein kleines Produkt kann ein klares Kundenproblem lösen: {problem}.",
            "caption": f"Aus Business-Sicht zeigt {name}, wie einfache Produktkommunikation Vertrauen und Kaufinteresse erzeugen kann.",
            "hashtags": "#ecommerce #produktmarketing #kundennutzen #digitalbusiness",
        }
    if "Pinterest" in platform:
        return {
            "title": f"{name}: Sicherer unterwegs",
            "hook": "Merke dir diesen einfachen Sicherheitstipp.",
            "caption": f"Praktische Idee für {target}: {name} gegen {problem}.",
            "hashtags": "#fahrradtipps #sicherheit #outdoor #pendler",
        }
    return {
        "title": f"{name} Content",
        "hook": base_hook,
        "caption": f"{name} hilft bei: {problem}.",
        "hashtags": hashtags_common,
    }


@app.on_event("startup")
def startup() -> None:
    ensure_files()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    products = read_csv(PRODUCTS_FILE)
    content = read_csv(CONTENT_FILE)
    analytics = read_csv(ANALYTICS_FILE)
    learnings = read_csv(LEARNINGS_FILE)
    platforms = load_platforms()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "products": products,
            "content": content,
            "analytics": analytics,
            "learnings": learnings,
            "platforms": platforms,
        },
    )


@app.post("/products")
def add_product(
    name: str = Form(...),
    target_group: str = Form(...),
    problem: str = Form(...),
    buy_price: str = Form("0"),
    sell_price: str = Form("0"),
    status: str = Form("Test"),
):
    rows = read_csv(PRODUCTS_FILE)
    product_id = next_id(rows)
    print(f"{product_id=}")
    append_csv(
        PRODUCTS_FILE,
        ["id", "name", "target_group", "problem", "buy_price", "sell_price", "status"],
        {
            "id": product_id,
            "name": name,
            "target_group": target_group,
            "problem": problem,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "status": status,
        },
    )
    return RedirectResponse("/", status_code=303)


@app.post("/generate-content/{product_id}")
def generate_content(product_id: str):
    products = read_csv(PRODUCTS_FILE)
    product = next((p for p in products if p.get("id") == product_id), None)
    if not product:
        return RedirectResponse("/", status_code=303)
    content_rows = read_csv(CONTENT_FILE)
    platforms = [p for p in load_platforms() if p.get("active")]
    for platform in platforms:
        platform_name = str(platform["name"])
        adapted = platform_adapter(platform_name, product)
        content_id = next_id(content_rows)
        row = {
            "id": content_id,
            "product_id": product_id,
            "platform": platform_name,
            "title": adapted["title"],
            "hook": adapted["hook"],
            "caption": adapted["caption"],
            "hashtags": adapted["hashtags"],
            "status": "geplant",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        content_rows.append(row)
    write_csv(CONTENT_FILE, ["id", "product_id", "platform", "title", "hook", "caption", "hashtags", "status", "created_at"], content_rows)
    return RedirectResponse("/", status_code=303)


@app.post("/analytics")
def add_analytics(
    content_id: str = Form(...),
    platform: str = Form(...),
    views: str = Form("0"),
    likes: str = Form("0"),
    comments: str = Form("0"),
    sales: str = Form("0"),
):
    rows = read_csv(ANALYTICS_FILE)
    learning = ""
    try:
        v = int(views or 0)
        s = int(sales or 0)
        c = int(comments or 0)
        if v >= 10000 or s > 0:
            learning = "Gewinner: mehr Varianten erzeugen"
        elif c >= 5:
            learning = "Kommentare auswerten und FAQ Content erstellen"
        else:
            learning = "Weiter testen"
    except ValueError:
        learning = "Daten prüfen"
    append_csv(
        ANALYTICS_FILE,
        ["id", "content_id", "platform", "views", "likes", "comments", "sales", "learning"],
        {
            "id": next_id(rows),
            "content_id": content_id,
            "platform": platform,
            "views": views,
            "likes": likes,
            "comments": comments,
            "sales": sales,
            "learning": learning,
        },
    )
    append_csv(
        LEARNINGS_FILE,
        ["id", "area", "insight", "action", "created_at"],
        {
            "id": next_id(read_csv(LEARNINGS_FILE)),
            "area": platform,
            "insight": learning,
            "action": "Content anpassen und erneut testen",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    )
    return RedirectResponse("/", status_code=303)


@app.get("/api/content")
def api_content():
    return read_csv(CONTENT_FILE)


@app.get("/api/products")
def api_products():
    return read_csv(PRODUCTS_FILE)
