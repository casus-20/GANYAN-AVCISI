import requests
import re
from datetime import date, datetime
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor
import threading


# =========================================================
# RACE INTELLIGENCE
# TJK VERİ KAYNAĞI
# =========================================================



# =========================================================
# ŞEHİR LİSTESİ
# =========================================================

CITY_IDS = {
    "Ankara": 5,
    "Kocaeli": 9,
    "İstanbul": 3,
    "Bursa": 4,
    "İzmir": 2,
    "Adana": 1,
    "Elazığ": 7,
    "Diyarbakır": 6,
    "Şanlıurfa": 8,
    "Antalya": 10,
}


# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================

# =========================================================
# HTTP CONNECTION POOL
# =========================================================
# Her TJK thread kendi requests.Session nesnesini kullanır.
# Böylece TCP/TLS bağlantıları mümkün olduğunca yeniden kullanılır;
# veri şeması ve analiz mantığı değişmez.
_SESSION_LOCAL = threading.local()

def _get_http_session() -> requests.Session:
    session = getattr(_SESSION_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Race-Intelligence-Streamlit/34",
            "Accept": "application/json,text/plain,*/*",
        })
        _SESSION_LOCAL.session = session
    return session


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).replace("\xa0", " ").split()).strip()


def _fold_tr(value: Any) -> str:
    """Türkçe karakter ve birleşik Unicode farklarını kaldırarak karşılaştırma yapar."""
    import unicodedata
    text = normalize_text(value).replace("İ", "i").replace("ı", "i")
    return "".join(ch for ch in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(ch))


def normalize_date(value: Any) -> str:
    """
    Streamlit date_input:
        datetime.date
        veya YYYY-MM-DD

    TJK API:
        YYYY-MM-DD
    """

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    text = normalize_text(value)

    if not text:
        return date.today().isoformat()

    # YYYY-MM-DD
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text

    # DD/MM/YYYY
    if len(text) == 10 and text[2] == "/" and text[5] == "/":
        dd = text[0:2]
        mm = text[3:5]
        yyyy = text[6:10]
        return f"{yyyy}-{mm}-{dd}"

    # DD.MM.YYYY
    if len(text) == 10 and text[2] == "." and text[5] == ".":
        dd = text[0:2]
        mm = text[3:5]
        yyyy = text[6:10]
        return f"{yyyy}-{mm}-{dd}"

    return text


def format_date_tr(value: Any) -> str:
    iso = normalize_date(value)

    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return iso


# =========================================================
# WORKER BAĞLANTISI
# =========================================================


TJK_BASE = "https://www.tjk.org"
DYNAMIC_CITY_IDS = {}
DYNAMIC_VENUE_URLS = {}

def _tjk_headers():
    return {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language":"tr-TR,tr;q=0.9,en;q=0.8","Referer":TJK_BASE+"/"}

def _html_text(value):
    from html import unescape
    value=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>"," ",str(value or ""),flags=re.I)
    return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",value))).strip()

def _html_tables(html):
    source = html or ""
    tag_re = re.compile(r"</?table\b[^>]*>", re.I)
    stack, found = [], []
    for match in tag_re.finditer(source):
        tag = match.group(0)
        if re.match(r"<table\b", tag, re.I):
            stack.append((match.start(), len(stack)))
        elif stack:
            begin, depth = stack.pop()
            found.append((depth, source[begin:match.end()]))
    if not found:
        return []
    # Keep document order. Sorting by nesting depth/length scrambled race order
    # on TJK pages where each race is wrapped in nested layout tables.
    return [item[1] for item in sorted(found, key=lambda x: source.find(x[1]))]

def _html_rows(table):
    return re.findall(r"<tr\b[^>]*>[\s\S]*?</tr>",table or "",flags=re.I)

def _html_cells(row):
    return [_html_text(x) for x in re.findall(r"<(?:td|th)\b[^>]*>([\s\S]*?)</(?:td|th)>",row or "",flags=re.I)]

def _html_cells_raw(row):
    """Tablo hücrelerinin HTML içeriğini, tooltip/title metaverisiyle birlikte döndürür."""
    return re.findall(r"<(?:td|th)\b([^>]*)>([\s\S]*?)</(?:td|th)>", row or "", flags=re.I)

def _cell_tooltip(cell_attrs, cell_html):
    from html import unescape
    candidates = []
    for key in ("title", "aria-label", "data-original-title", "data-content", "data-tooltip"):
        match = re.search(r"\b" + re.escape(key) + r"\s*=\s*(['\"])(.*?)\1", cell_attrs or "", re.I | re.S)
        if match:
            candidates.append(match.group(2))
    for key in ("title", "aria-label", "data-original-title", "data-content", "data-tooltip"):
        match = re.search(r"\b" + re.escape(key) + r"\s*=\s*(['\"])(.*?)\1", cell_html or "", re.I | re.S)
        if match:
            candidates.append(match.group(2))
    # Bazı TJK sürümlerinde açıklama doğrudan hücre içindeki gizli span'de bulunur.
    for match in re.finditer(r"<(?:span|div|a)\b([^>]*)>([\s\S]*?)</(?:span|div|a)>", cell_html or "", re.I):
        attrs, body = match.groups()
        for key in ("title", "aria-label", "data-content", "data-original-title"):
            attr = re.search(r"\b" + key + r"\s*=\s*(['\"])(.*?)\1", attrs, re.I | re.S)
            if attr:
                candidates.append(attr.group(2))
    cleaned = [_html_text(unescape(x)).strip() for x in candidates]
    return next((x for x in cleaned if x), "")

def _at_id(row):
    m=re.search(r"(?:QueryParameter_AtId|AtKodu|Atkodu)=(\d+)",row or "",flags=re.I)
    return m.group(1) if m else None

def _parse_tjk_daily(html):
    races_by_no = {}
    source = html or ""
    for table in _html_tables(source):
        rows = _html_rows(table)
        header = None
        header_index = -1
        for row_index, row in enumerate(rows):
            cells = _html_cells(row)
            normalized = [_fold_tr(x) for x in cells]
            has_name = any(("at ismi" in x) or ("at adi" in x) or ("horse name" in x) for x in normalized)
            has_no = any(x in ("n", "no", "s", "numara") for x in normalized)
            # TJK sayfa sürümlerinde HP/Son 6 sütunları gizlenebiliyor;
            # at adı + numara başlığı program tablosunu tanımak için yeterlidir.
            if has_name and has_no:
                header = cells
                header_index = row_index
                break
        if not header:
            continue

        folded_header = [_fold_tr(x) for x in header]
        def ix(pattern):
            return next((i for i, value in enumerate(folded_header) if re.search(pattern, value, re.I)), -1)

        idx = {
            "no": ix(r"^(n|no|s|numara)$"), "name": ix(r"at ismi|at adi|horse name"),
            "age": ix(r"^(yas|age)$"), "origin": ix(r"orijin|origin"),
            "weight": ix(r"siklet|weight"), "jockey": ix(r"^(jokey|jockey)$"),
            "owner": ix(r"^(sahip|owner)$"), "trainer": ix(r"antrenor|trainer"),
            "st": ix(r"^(st|start)$"), "hp": ix(r"^(hp|rt)$"),
            "last6": ix(r"son 6|last 6"), "kgs": ix(r"^kgs$"),
            "s20": ix(r"^s20$"), "best": ix(r"en iyi d\.|best time"),
            "odds": ix(r"^gny$|odds"), "agf": ix(r"^agf$|favorite"),
            "workout": ix(r"^(idm|workout)$"),
            "lastDate": ix(r"son kosu tarihi|last race date"),
        }
        horses = []
        for row in rows[header_index + 1:]:
            cells = _html_cells(row)
            raw_cells = _html_cells_raw(row)
            if not cells:
                continue
            def val(key):
                i = idx[key]
                return cells[i].strip() if 0 <= i < len(cells) else ""
            def tooltip(key):
                i = idx[key]
                return _cell_tooltip(*raw_cells[i]) if 0 <= i < len(raw_cells) else ""
            no_match = re.match(r"^(\d{1,2})$", val("no"))
            if not no_match:
                continue
            name = re.sub(r"\s*Image.*$", "", val("name"), flags=re.I).strip()
            if not name:
                continue
            horses.append({
                "no": no_match.group(1), "name": name, "age": val("age"),
                "origin": val("origin"), "weight": val("weight"),
                "jockey": val("jockey"), "owner": val("owner"),
                "trainer": val("trainer"), "st": val("st"), "hp": val("hp"),
                "last6": val("last6"), "kgs": val("kgs"), "s20": val("s20"),
                "bestTime": val("best"), "bestInfo": tooltip("best"), "bestCity": "",
                "bestDate": "", "bestDistance": "", "odds": val("odds"),
                "agf": val("agf"), "workout": val("workout"),
                "lastDate": val("lastDate"), "atId": _at_id(row),
            })
        if len(horses) < 1:
            continue

        table_pos = source.find(table)
        header_html = rows[header_index] if 0 <= header_index < len(rows) else ""
        header_pos = table.find(header_html) if header_html else -1
        table_prefix = table[:header_pos] if header_pos >= 0 else ""
        before = _html_text(source[max(0, table_pos - 50000):table_pos] + table_prefix)
        markers = list(re.finditer(r"(\d{1,2})\.\s*Koşu\s+([0-2]?\d[:.][0-5]\d)", before, re.I))
        marker = markers[-1] if markers else None
        race_no = int(marker.group(1)) if marker else (len(races_by_no) + 1)
        race_time = marker.group(2).replace(".", ":") if marker else ""
        detail = ""
        if marker:
            detail = before[marker.end():]
            detail = re.split(r"\s+(?:İkramiye|At Sahibi Primi|Yetiştiricilik Primi|N\s+At İsmi|Forma\s+N\s+At İsmi)", detail, 1, flags=re.I)[0][:1800].strip(" ,;:-")
        dm = list(re.finditer(r"(\d{3,4})\s*(?:m)?\s*(Kum|Çim|Sentetik|Fiber Sand|Turf|Polytrack)\b", detail, re.I))
        parsed_race = {
            "no": race_no, "time": race_time,
            "name": detail or f"Koşu {race_no}",
            "meta": {"distance": int(dm[-1].group(1)) if dm else None,
                     "surface": dm[-1].group(2) if dm else "",
                     "raceName": detail, "detail": detail, "raw": before[-5000:]},
            "horses": horses,
        }
        # TJK layout tables can contain the same race as nested wrappers.
        # Keep one record per actual race number, preferring the fullest horse table.
        current = races_by_no.get(race_no)
        if current is None or len(horses) > len(current.get("horses", [])):
            races_by_no[race_no] = parsed_race

    return [races_by_no[n] for n in sorted(races_by_no)]


def _parse_tjk_workouts(html):
    result = []
    for table in _html_tables(html):
        rows = _html_rows(table)
        parsed = []
        for hi, header_row in enumerate(rows):
            headers = _html_cells(header_row)
            def ix(pattern):
                return next((i for i, value in enumerate(headers) if re.search(pattern, value, re.I)), -1)
            # Require an actual distance header and a date header before accepting rows.
            indexes = {
                "horse": ix(r"At\s*(?:Adı|İsmi|Adi|Ismi)|Horse"),
                "m2200": ix(r"^2200(?:\s*m)?$"), "m2000": ix(r"^2000(?:\s*m)?$"),
                "m1800": ix(r"^1800(?:\s*m)?$"), "m1600": ix(r"^1600(?:\s*m)?$"),
                "m1400": ix(r"^1400(?:\s*m)?$"), "m1200": ix(r"^1200(?:\s*m)?$"),
                "m1000": ix(r"^1000(?:\s*m)?$"), "m800": ix(r"^800(?:\s*m)?$"),
                "m600": ix(r"^600(?:\s*m)?$"), "m400": ix(r"^400(?:\s*m)?$"),
                "m200": ix(r"^200(?:\s*m)?$"), "date": ix(r"İ\\.?\s*Tarihi|Tarih|Date"),
                "surface": ix(r"^Pist$|Surface"), "type": ix(r"İ\\.?\s*Türü|Tür|Type"),
                "track": ix(r"İdman\s*Hipodromu|İ\\.?\s*Hip\\.?|Hipodrom|Track"),
                "status": ix(r"Durum|Status"),
            }
            if indexes["date"] < 0 or not any(indexes[k] >= 0 for k in ("m400","m600","m800","m1000","m1200")):
                continue
            for row in rows[hi+1:]:
                cells = _html_cells(row)
                if not cells: continue
                def val(key):
                    i = indexes[key]
                    return cells[i].replace(",", ".").strip() if 0 <= i < len(cells) else ""
                date_value = val("date")
                if not re.fullmatch(r"\d{2}[./]\d{2}[./]\d{4}", date_value):
                    continue
                splits = [val(k) for k in ("m2200","m2000","m1800","m1600","m1400","m1200","m1000","m800","m600","m400","m200")]
                if not any(splits): continue
                parsed.append({
                    "horse": val("horse"), "m2200": val("m2200"), "m2000": val("m2000"),
                    "m1800": val("m1800"), "m1600": val("m1600"), "m1400": val("m1400"),
                    "m1200": val("m1200"), "m1000": val("m1000"), "m800": val("m800"),
                    "m600": val("m600"), "m400": val("m400"), "m200": val("m200"),
                    "status": val("status"), "date": date_value, "surface": val("surface"),
                    "type": val("type"), "track": val("track"), "jockey": ""
                })
            if parsed:
                break
        if parsed:
            seen = set()
            for item in parsed:
                key = tuple(item.get(k, "") for k in ("date","m2200","m2000","m1800","m1600","m1400","m1200","m1000","m800","m600","m400","m200","track","surface"))
                if key not in seen:
                    seen.add(key); result.append(item)
            if result: break
    return result[:1000]



def _discover_tjk_venues(date_value, timeout=25):
    """Verilen TJK günlük program ana sayfasından o tarihin tüm yerli/yabancı hipodrom linklerini çıkarır."""
    from urllib.parse import urljoin, urlparse, parse_qs, quote
    from bs4 import BeautifulSoup

    iso = normalize_date(date_value)
    dmy = datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    main_url = f"{TJK_BASE}/TR/Kurumsal/Info/Page/GunlukYarisProgrami"
    urls = [main_url + "?QueryParameter_Tarih=" + quote(dmy)]
    found = {}
    errors = []

    for page_url in urls:
        try:
            response = _get_http_session().get(page_url, timeout=timeout, headers=_tjk_headers())
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}: {page_url}")
                continue
            html = response.text or ""
            soup = BeautifulSoup(html, "html.parser")

            # Önce gerçek anchor bağlantılarını oku.
            candidates = []
            for a in soup.find_all("a", href=True):
                href = a.get("href", "").replace("&amp;", "&")
                if re.search(r"GunlukYarisProgrami|Kayitlar", href, re.I):
                    candidates.append((href, a.get_text(" ", strip=True)))

            # Bazı TJK sürümlerinde şehir linkleri script/JSON içine gömülüyor.
            # Bu nedenle sayfa kaynağındaki URL benzeri parçaları da tara.
            for match in re.finditer(r"(?:href\s*=\s*['\"]|(?:\\/)?TR\\/)[^'\"]{0,1200}(?:GunlukYarisProgrami|Kayitlar)[^'\"]{0,1200}", html, re.I):
                raw = match.group(0).strip().strip("'\"")
                raw = raw.replace("\\/", "/").replace("&amp;", "&").replace("\u0026", "&")
                candidates.append((raw, ""))

            for href, link_text in candidates:
                absolute = urljoin(TJK_BASE, href)
                parsed = urlparse(absolute)
                params = parse_qs(parsed.query)
                ids = params.get("SehirId") or params.get("sehirId") or params.get("sehirID") or []
                names = params.get("SehirAdi") or params.get("sehirAdi") or params.get("Sehir") or []
                name = normalize_text(names[0] if names else link_text)
                name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
                if not name:
                    continue
                # SehirId her TJK sayfa sürümünde linkte bulunmayabilir;
                # yerli hipodromlarda bilinen ID yalnızca eksik parametreyi tamamlar.
                canonical = _canonical_city_name(name)
                raw_id = ids[0] if ids else None
                cid = int(raw_id) if raw_id and str(raw_id).isdigit() else CITY_IDS.get(canonical)
                if cid is None:
                    # Yabancı hipodromlar için kimlik olmadan tahmin yapılmaz.
                    continue
                # Aynı şehrin tekrar eden linkleri içinden tam program sayfasını sakla.
                key = _canonical_city_name(name)
                found[key] = {"id": cid, "url": absolute}

            if found:
                break
        except Exception as exc:
            errors.append(str(exc))

    DYNAMIC_CITY_IDS.clear()
    DYNAMIC_CITY_IDS.update({name: item["id"] for name, item in found.items()})
    DYNAMIC_VENUE_URLS.clear()
    DYNAMIC_VENUE_URLS.update({name: item["url"] for name, item in found.items()})
    return list(found)


def _fetch_tjk_daily(date_value, city, timeout=45):
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

    iso = normalize_date(date_value)
    city = normalize_text(city)
    city_key = _canonical_city_name(city)
    cid = DYNAMIC_CITY_IDS.get(city) or DYNAMIC_CITY_IDS.get(city_key) or CITY_IDS.get(city)

    if not cid:
        _discover_tjk_venues(date_value, timeout=min(timeout, 25))
        cid = DYNAMIC_CITY_IDS.get(city) or DYNAMIC_CITY_IDS.get(city_key) or CITY_IDS.get(city)
    if not cid:
        raise ValueError(f"Bu tarihte TJK programında hipodrom bulunamadı: {city}")

    dmy = datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    discovered_url = DYNAMIC_VENUE_URLS.get(city) or DYNAMIC_VENUE_URLS.get(city_key)

    # Ana günlük program sayfası yalnızca hipodrom keşfi içindir.
    # Yarış verisi mutlaka seçilen hipodromun Info/Sehir sayfasından alınır.
    parsed = urlparse(discovered_url) if discovered_url else None
    path = parsed.path if parsed and "/Info/Sehir/" in parsed.path else "/TR/Kurumsal/Info/Sehir/GunlukYarisProgrami"
    query = dict(parse_qsl(parsed.query, keep_blank_values=True)) if parsed else {}
    query.update({
        "Era": "today" if iso == datetime.now().strftime("%Y-%m-%d") else "",
        "QueryParameter_Tarih": dmy,
        "SehirAdi": city,
        "SehirId": str(cid),
    })
    if not query.get("Era"):
        query.pop("Era", None)
    url = urlunparse(("https", "www.tjk.org", path, "", urlencode(query), ""))

    try:
        response = _get_http_session().get(url, timeout=timeout, headers=_tjk_headers())
        if response.status_code >= 400:
            raise RuntimeError(f"TJK HTTP {response.status_code}: {url}")

        response_parts = urlparse(response.url)
        response_params = dict(parse_qsl(response_parts.query, keep_blank_values=True))
        response_city = response_params.get("SehirAdi") or response_params.get("sehirAdi") or ""
        response_city_id = response_params.get("SehirId") or response_params.get("sehirId") or ""
        if "/Info/Sehir/" not in response_parts.path:
            raise RuntimeError("TJK yanıtı seçilen hipodromun şehir programı sayfası değil.")
        if response_city and _canonical_city_name(response_city) != city_key:
            raise RuntimeError(
                f"TJK yanıt hipodromu uyuşmuyor: istenen {city}, gelen {response_city}."
            )
        if response_city_id and str(response_city_id) != str(cid):
            raise RuntimeError(
                f"TJK şehir kimliği uyuşmuyor: istenen {cid}, gelen {response_city_id}."
            )
        if not response_city and not response_city_id:
            raise RuntimeError("TJK yanıt URL'sinde seçilen hipodrom kimliği doğrulanamadı.")

        page_text = _html_text(response.text or "")
        date_tokens = re.findall(r"\b\d{1,2}[./]\d{1,2}[./]20\d{2}\b", page_text)
        page_dates = set()
        for token in date_tokens:
            try:
                page_dates.add(normalize_date(token.replace(".", "/")))
            except Exception:
                pass
        if iso not in page_dates:
            raise RuntimeError(
                f"TJK yanıtında seçilen tarih doğrulanamadı ({dmy}); "
                f"sayfada bulunan tarihler: {', '.join(sorted(page_dates)) or 'yok'}. "
                "Yanlış tarih verisi engellendi."
            )

        races = _parse_tjk_daily(response.text)
        if not races:
            raise RuntimeError(
                f"TJK {city} hipodromu için {dmy} tarihinde koşu tablosu ayrıştırılamadı: {url}"
            )

        races.sort(key=lambda item: int(item.get("no") or 999))
        race_numbers = [int(item.get("no") or 0) for item in races]
        if len(race_numbers) != len(set(race_numbers)):
            raise RuntimeError("TJK yanıtında aynı koşu birden fazla kez bulundu; karışık veri engellendi.")

        count = sum(len(item.get("horses", [])) for item in races)
        return {
            "ok": True,
            "source": "TJK Günlük Yarış Programı (doğrudan)",
            "date": iso,
            "city": city,
            "status": response.status_code,
            "sourceUrl": response.url,
            "raceCount": len(races),
            "horseCount": count,
            "races": races,
        }
    except requests.RequestException as exc:
        raise RuntimeError(f"TJK bağlantı hatası ({city}, {dmy}): {exc}") from exc


def fetch_TJK(date_value: Any, city: str, timeout: int = 45) -> Dict[str, Any]:
    """Geriye dönük uyumluluk: TJK yerine doğrudan TJK günlük program sayfası."""
    return _fetch_tjk_daily(date_value, city, timeout=timeout)


# =========================================================
# ANA PROGRAM ÇEKME
# =========================================================

def get_program(
    date_value: Any,
    city: str,
) -> Dict[str, Any]:

    iso_date = normalize_date(date_value)
    city = normalize_text(city)

    data = fetch_TJK(
        date_value=iso_date,
        city=city,
    )

    races = data.get("races", [])

    if not isinstance(races, list):
        races = []

    # -----------------------------------------------------
    # TJK'dan gelen gerçek değerleri koru
    # -----------------------------------------------------

    race_count = data.get(
        "raceCount",
        len(races),
    )

    horse_count = data.get(
        "horseCount",
        sum(
            len(r.get("horses", []))
            for r in races
            if isinstance(r, dict)
        ),
    )

    # -----------------------------------------------------
    # Debug bilgisi
    # -----------------------------------------------------

    total_horses = 0
    horses_per_race = {}

    for race in races:

        if not isinstance(race, dict):
            continue

        horses = race.get("horses", [])

        if not isinstance(horses, list):
            horses = []

        race_no = race.get(
            "no",
            len(horses_per_race) + 1,
        )

        horses_per_race[str(race_no)] = len(horses)

        total_horses += len(horses)

    # -----------------------------------------------------
    # Streamlit'in beklediği standart cevap
    # -----------------------------------------------------

    result = {
        "ok": True,
        "source": data.get(
            "source",
            "TJK Günlük Yarış Programı",
        ),
        "date": iso_date,
        "date_tr": format_date_tr(iso_date),
        "city": city,

        "races": races,

        "race_count": int(race_count or len(races)),
        "raceCount": int(race_count or len(races)),

        "total_horses": int(
            total_horses
            if total_horses
            else horse_count or 0
        ),

        "horse_count": int(
            horse_count
            if horse_count is not None
            else total_horses
        ),

        "horseCount": int(
            horse_count
            if horse_count is not None
            else total_horses
        ),

        "status": data.get("status"),

        "source_url": data.get("sourceUrl", ""),

        "debug": {
            "transport": "Doğrudan TJK HTTPS",
            "source_url": data.get("sourceUrl", ""),
            "date": iso_date,
            "date_tr": format_date_tr(iso_date),
            "city": city,
            "city_id": CITY_IDS.get(city),

            "http_status": data.get("status"),

            "race_count": len(races),

            "total_horse_count": total_horses,

            "horses_per_race": horses_per_race,

            "source": data.get(
                "source",
                "TJK Günlük Yarış Programı",
            ),

            "source_url": data.get(
                "sourceUrl",
                "",
            ),
        },
    }

    return normalize_program(result)


# =========================================================
# TEK AT / YARDIMCI VERİ NORMALİZASYONU
# =========================================================

def normalize_horse(horse: Dict[str, Any]) -> Dict[str, Any]:
    """
    TJK HTML -> Streamlit ortak at şeması.

    TJK'ın döndürdüğü alanlar korunur; ayrıca app.py'nin
    kullandığı V34 alan adları da oluşturulur.
    """
    if not isinstance(horse, dict):
        return {}

    result = dict(horse)

    # Ortak / TJK alanları
    result["name"] = (
        result.get("name")
        or result.get("horse")
        or result.get("horseName")
        or result.get("At İsmi")
        or ""
    )

    result["no"] = (
        result.get("no")
        or result.get("number")
        or result.get("numara")
        or result.get("s")
        or result.get("S")
        or ""
    )

    result["age"] = (
        result.get("age")
        or result.get("yas")
        or result.get("Yaş")
        or ""
    )

    result["weight"] = (
        result.get("weight")
        or result.get("siklet")
        or result.get("Sıklet")
        or result.get("kilo")
        or ""
    )

    result["jockey"] = (
        result.get("jockey")
        or result.get("jokey")
        or result.get("Jokey")
        or result.get("jockeyName")
        or ""
    )

    result["hp"] = (
        result.get("hp")
        or result.get("HP")
        or result.get("rating")
        or result.get("RT")
        or ""
    )

    result["last6"] = (
        result.get("last6")
        or result.get("son6")
        or result.get("Son 6 Y.")
        or result.get("lastSix")
        or ""
    )

    result["agf"] = (
        result.get("agf")
        or result.get("AGF")
        or ""
    )

    # AGF ile ganyan/odds birbirine karıştırılmaz.
    result["odds"] = (
        result.get("odds")
        or result.get("Gny")
        or ""
    )

    result["st"] = (
        result.get("st")
        or result.get("St")
        or result.get("start")
        or ""
    )

    result["kgs"] = (
        result.get("kgs")
        or result.get("KGS")
        or ""
    )

    result["form"] = (
        result.get("form")
        or result.get("Forma")
        or result.get("last6")
        or ""
    )

    result["trainer"] = (
        result.get("trainer")
        or result.get("antrenor")
        or result.get("Antrenörü")
        or result.get("trainerName")
        or ""
    )

    result["owner"] = (
        result.get("owner")
        or result.get("sahip")
        or result.get("Sahip")
        or result.get("ownerName")
        or ""
    )

    # Gerçek TJK at kimliğini standartlaştır.
    # ÖNEMLİ: program numarası (no) hiçbir zaman atId yerine kullanılmaz.
    at_id = (
        result.get("atId")
        or result.get("at_id")
        or result.get("horseId")
        or result.get("horse_id")
        or result.get("horseKey")
        or result.get("horse_key")
        or result.get("id")
        or result.get("Id")
        or ""
    )
    if at_id not in (None, ""):
        result["atId"] = str(at_id)
        result["at_id"] = str(at_id)

    # app.py'nin kullandığı V34 alan adları
    result["at_ismi"] = result["name"]
    result["numara"] = result["no"]
    result["yas"] = result["age"]
    result["siklet"] = result["weight"]
    result["jokey"] = result["jockey"]

    return result


def normalize_program(program: Dict[str, Any]) -> Dict[str, Any]:
    """
    TJK HTML yarış şemasını app.py'nin beklediği V34 şemasına çevirir.
    TJK verisinin orijinal alanları korunur.
    """
    if not isinstance(program, dict):
        return {
            "ok": False,
            "races": [],
            "race_count": 0,
            "total_horses": 0,
        }

    races = program.get("races", [])
    if not isinstance(races, list):
        races = []

    normalized_races = []

    for index, race in enumerate(races, start=1):
        if not isinstance(race, dict):
            continue

        item = dict(race)

        meta = item.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        item["meta"] = meta

        race_no = (
            item.get("race_number")
            or item.get("no")
            or item.get("number")
            or index
        )

        race_time = (
            item.get("race_time")
            or item.get("time")
            or meta.get("time")
            or ""
        )

        distance = (
            item.get("distance")
            or meta.get("distance")
            or ""
        )

        surface = (
            item.get("surface")
            or meta.get("surface")
            or ""
        )

        condition = (
            item.get("condition")
            or meta.get("condition")
            or meta.get("detail")
            or meta.get("raceName")
            or ""
        )

        horses = item.get("horses", [])
        if not isinstance(horses, list):
            horses = []

        normalized_horses = [
            normalize_horse(h)
            for h in horses
            if isinstance(h, dict)
        ]

        # TJK alanlarını koru + app.py uyumlu alanları ekle
        item["race_number"] = race_no
        item["race_time"] = race_time
        item["distance"] = distance
        item["surface"] = surface
        item["condition"] = condition
        item["no"] = race_no
        item["time"] = race_time
        item["horses"] = normalized_horses

        normalized_races.append(item)

    program["races"] = normalized_races

    program["race_count"] = len(normalized_races)
    program["raceCount"] = len(normalized_races)

    total = sum(len(r["horses"]) for r in normalized_races)

    program["total_horses"] = total
    program["horse_count"] = total
    program["horseCount"] = total

    # TJK ve Streamlit bağlantısını debug ekranında açıkça göster
    debug = program.get("debug")
    if not isinstance(debug, dict):
        debug = {}

    debug.setdefault("transport", "Doğrudan TJK HTTPS")
    debug["city_id"] = CITY_IDS.get(program.get("city"))
    debug["race_count"] = len(normalized_races)
    debug["total_horse_count"] = total
    debug["horses_per_race"] = {
        str(r.get("race_number", i + 1)): len(r.get("horses", []))
        for i, r in enumerate(normalized_races)
    }

    program["debug"] = debug

    return program


def get_supported_cities() -> List[str]:
    return list(dict.fromkeys(list(DYNAMIC_CITY_IDS.keys())))


def get_city_id(city: str) -> int:
    city = normalize_text(city)

    if city in DYNAMIC_CITY_IDS:
        return DYNAMIC_CITY_IDS[city]
    if city in CITY_IDS:
        return CITY_IDS[city]
    raise ValueError(f"Bilinmeyen hipodrom: {city}")



def _canonical_city_name(value: Any) -> str:
    """TJK cevabındaki hipodrom adını resmi şehir adına çevirir."""
    s = normalize_text(value)
    s = re.sub(r"\s+Hipodromu\s*$", "", s, flags=re.I)
    key = (s.lower().replace("ı", "i").replace("ş", "s")
           .replace("ğ", "g").replace("ü", "u").replace("ö", "o")
           .replace("ç", "c"))
    aliases = {
        "ankara": "Ankara", "kocaeli": "Kocaeli", "istanbul": "İstanbul",
        "bursa": "Bursa", "izmir": "İzmir", "adana": "Adana",
        "elazig": "Elazığ", "diyarbakir": "Diyarbakır",
        "sanliurfa": "Şanlıurfa", "antalya": "Antalya",
    }
    return aliases.get(key, s)


def _TJK_result_matches_target(data: Dict[str, Any], target_date: str, requested_city: str) -> bool:
    """Bir TJK cevabının gerçekten istenen tarih ve hipodroma ait olduğunu doğrular."""
    if not isinstance(data, dict) or not data.get("ok", False):
        return False

    races = data.get("races")
    if not isinstance(races, list) or not races:
        return False

    returned_date = data.get("date") or data.get("targetDate") or data.get("programDate")
    if returned_date:
        try:
            if normalize_date(returned_date) != target_date:
                return False
        except Exception:
            return False
    else:
        # Tarih bilgisi yoksa, yanlış tarih programını doğru kabul etme.
        return False

    returned_city = data.get("city") or data.get("hippodrome") or data.get("hipodrom")
    if not returned_city:
        return False

    return _canonical_city_name(returned_city) == _canonical_city_name(requested_city)


def get_active_cities(date_value: Any) -> List[str]:
    """TJK günlük programındaki gerçek hipodrom bağlantılarını döndürür.

    Günlük program ana sayfasındaki şehir bağlantıları zaten TJK'nın o tarih
    için yayımladığı programları temsil eder. Önceki sürüm bu bağlantıları
    bulduktan sonra aynı anda 10 ayrı şehir sayfasına tekrar istek gönderiyor;
    TJK tarafındaki eşzamanlı istek/oturum sınırlamaları yüzünden tüm kontroller
    başarısız olabiliyor ve ekranda hatalı biçimde hiç hipodrom yok deniyordu.
    Bu nedenle keşfedilen resmi program bağlantıları doğrudan kullanılır.
    Keşif sayfası bağlantı vermezse bilinen yerli hipodromlar tek tek kontrol
    edilir; paralel istek gönderilmez.
    """
    target = normalize_date(date_value)

    # 1) Resmi günlük program ana sayfasındaki şehir linkleri birincil kaynaktır.
    discovered = _discover_tjk_venues(target, timeout=25) or []
    active = []
    seen = set()
    for city in discovered:
        canonical = _canonical_city_name(city)
        key = _fold_tr(canonical)
        if canonical and key not in seen:
            seen.add(key)
            active.append(canonical)

    # TJK ana sayfası program linklerini verdiğinde bunlar doğrudan kullanılır.
    # Her linkin href bilgisi DYNAMIC_VENUE_URLS içinde tutulur; seçilen şehir
    # seçildiğinde get_program aynı resmi şehir URL'sinden atları çeker.
    if active:
        return active

    # 2) Ana sayfa linkleri boşsa yerli merkezleri sırayla sorgula.
    # Altı/on eşzamanlı istek TJK'nın geçici engellemesine yol açabildiğinden
    # ThreadPoolExecutor kullanılmıyor.
    for city in CITY_IDS:
        try:
            data = _fetch_tjk_daily(target, city, timeout=35)
            races = data.get("races") if isinstance(data, dict) else None
            if isinstance(races, list) and races:
                active.append(city)
        except Exception:
            continue

    return active


def TJK_health() -> Dict[str, Any]:
    try:
        r=_get_http_session().get(TJK_BASE,timeout=15,headers=_tjk_headers())
        return {"ok":r.status_code<400,"status":r.status_code,"source":TJK_BASE}
    except Exception as exc:
        return {"ok":False,"status":0,"error":str(exc)}


# =========================================================
# GERÇEK AT GEÇMİŞİ / GALOP VERİSİ
# =========================================================

def _clean_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.replace("\xa0", " ").split()).strip()
    return value


def _first_nonempty(d: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    for key in keys:
        if key in d and d.get(key) not in (None, "", "-", "—", "–"):
            return _clean_value(d.get(key))
    return default


_HISTORY_KEYS = {
    "date": ["date", "tarih", "Tarih", "Date"],
    "city": ["city", "şehir", "sehir", "hipodrom", "Hipodrom", "Hipo"],
    "distance": ["distance", "mesafe", "Msf", "msf", "Msf."],
    "surface": ["surface", "pist", "Pist", "track", "zemin", "Surface", "trackSurface", "track_surface", "surfaceType", "surface_type", "pistTuru", "pist_turu", "pistAdi", "pist_adi", "Zemin", "zeminTuru", "zemin_turu"],
    "post": ["post", "start", "St", "st", "kulvar", "Kulvar"],
    "time": ["time", "derece", "Derece", "finishTime", "süre", "Sure"],
    "weight": ["weight", "kilo", "Kilo", "siklet", "Sıklet"],
    "jockey": ["jockey", "jokey", "Jokey", "jockeyName"],
    "group": ["group", "grup", "Grup"],
    "raceName": ["raceName", "race_name", "kosu", "Koşu", "Koşu Adı", "race"],
    "raceType": ["raceType", "race_type", "kosuTuru", "Koşu Türü", "type", "tur"],
    "trainer": ["trainer", "antrenor", "Antrenör", "Antrenörü", "trainerName"],
    "owner": ["owner", "sahip", "Sahip", "ownerName"],
    "hp": ["hp", "HP", "handicap", "handikap", "RT", "rt"],
    "prize": ["prize", "ikramiye", "Ikramiye", "İkramiye", "Kazanç", "kazanc", "earnings", "earning", "prizeAmount", "prize_amount"],
    "l20": ["l20", "L20", "son20", "Son20"],
    "place": ["place", "sira", "Sıra", "S", "finish", "rank", "dereceSirasi"],
}


def _normalize_history_row(row: Any) -> Dict[str, Any] | None:
    """TJK/TJK geçmiş satırını BİZİM SKOR'un ortak şemasına çevirir."""
    if isinstance(row, dict):
        src = dict(row)
        out = dict(row)
        for target, aliases in _HISTORY_KEYS.items():
            value = _first_nonempty(src, aliases, "")
            if value not in (None, ""):
                out[target] = value
        # Bazı TJK sürümlerinde yalnızca 'finish' veya 'S' bulunur.
        if not out.get("place"):
            out["place"] = _first_nonempty(src, ["finish", "S", "sira", "siraNo", "rank"], "")
        return out

    if isinstance(row, (list, tuple)):
        # TJK AtKosuBilgileri tablosunun bilinen kolon sırası.
        cols = [
            "date", "city", "distance", "surface", "post", "time",
            "weight", "jockey", "group", "raceName", "raceType",
            "trainer", "owner", "hp", "prize", "l20",
        ]
        vals = list(row)
        if len(vals) < 3:
            return None
        out = {cols[i]: _clean_value(vals[i]) for i in range(min(len(vals), len(cols)))}
        # Bazı tablolar sıralamayı ayrıca taşıyabilir.
        if len(vals) > 16:
            out["place"] = _clean_value(vals[16])
        return out
    return None


def _extract_history_payload(data: Any) -> List[Dict[str, Any]]:
    """JSON cevabındaki history/rows/items/results/data katmanlarını esnekçe bulur."""
    candidates: List[Any] = []

    def walk(obj: Any, depth: int = 0) -> None:
        if depth > 5:
            return
        if isinstance(obj, dict):
            for key in ("history", "History", "rows", "Rows", "items", "Items",
                        "results", "Results", "data", "Data"):
                value = obj.get(key)
                if isinstance(value, list):
                    candidates.append(value)
                elif isinstance(value, dict):
                    walk(value, depth + 1)
            # history doğrudan tek nesne olarak gelirse
            if any(k in obj for k in ("date", "tarih", "Tarih", "distance", "mesafe", "Derece", "derece")):
                candidates.append([obj])
        elif isinstance(obj, list):
            candidates.append(obj)
            for item in obj[:5]:
                if isinstance(item, (dict, list)):
                    walk(item, depth + 1)

    walk(data)

    best: List[Dict[str, Any]] = []
    for cand in candidates:
        rows = []
        for raw in cand:
            nr = _normalize_history_row(raw)
            if nr:
                rows.append(nr)
        if len(rows) > len(best):
            best = rows
    return best


def _money_to_float(value: Any) -> float:
    if value in (None, "", "-", "—", "–"):
        return 0.0
    s = str(value).strip().replace("₺", "").replace("TL", "").replace("tl", "").strip()
    # 1.234.567,89 -> 1234567.89
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    try:
        return float(m.group(0)) if m else 0.0
    except Exception:
        return 0.0


def _earnings_from_history(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0.0
    year = 0.0
    current_year = date.today().year
    for row in history:
        prize = _first_nonempty(row, _HISTORY_KEYS["prize"], "")
        amount = _money_to_float(prize)
        total += amount
        ds = str(_first_nonempty(row, _HISTORY_KEYS["date"], ""))
        if str(current_year) in ds:
            year += amount
    return {"total": total if total > 0 else None, "year": year if year > 0 else None}


def _merge_history(primary: List[Dict[str, Any]], fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aynı yarışları tarih+şehir+mesafe+derece ile tekilleştirerek birleştirir."""
    out: List[Dict[str, Any]] = []
    seen = set()
    for row in (primary or []) + (fallback or []):
        if not isinstance(row, dict):
            continue
        key = (
            str(row.get("date") or row.get("tarih") or ""),
            str(row.get("city") or row.get("şehir") or ""),
            str(row.get("distance") or row.get("mesafe") or ""),
            str(row.get("time") or row.get("derece") or ""),
            str(row.get("place") or row.get("S") or row.get("sira") or ""),
        )
        if key == ("", "", "", "", ""):
            key = ("raw", repr(sorted(row.items()))[:500])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out



class _TJKTableParser:
    """TJK HTML tablosunu stdlib ile parse eder; BeautifulSoup gerektirmez."""
    def __init__(self):
        from html.parser import HTMLParser
        self.rows = []
        self._row = None
        self._cell = None
        self._buf = []
        self._href = ""

    def feed(self, html_text: str):
        from html.parser import HTMLParser
        outer = self

        class P(HTMLParser):
            def handle_starttag(self, tag, attrs):
                tag = tag.lower()
                if tag == "tr":
                    outer._row = []
                elif tag in ("td", "th") and outer._row is not None:
                    outer._cell = {"text": [], "href": ""}
                    outer._buf = []
                elif tag == "a" and outer._cell is not None:
                    for k, v in attrs:
                        if k.lower() == "href":
                            outer._cell["href"] = v or ""

            def handle_data(self, data):
                if outer._cell is not None:
                    outer._cell["text"].append(data)

            def handle_endtag(self, tag):
                tag = tag.lower()
                if tag in ("td", "th") and outer._cell is not None and outer._row is not None:
                    txt = " ".join("".join(outer._cell["text"]).split())
                    outer._row.append((txt, outer._cell.get("href", "")))
                    outer._cell = None
                elif tag == "tr" and outer._row is not None:
                    if outer._row:
                        outer.rows.append(outer._row)
                    outer._row = None

        # HTMLParser.feed() None döndürür; gerçek satırlar self.rows içindedir.
        # Eski kod feed() dönüşünü rows olarak aldığı için rows=None oluyor ve
        # doğrudan TJK fallback'i hiç parse edilemiyordu.
        P(convert_charrefs=True).feed(html_text or "")
        return self.rows


def _direct_tjk_history(at_id: str, timeout: int = 25) -> List[Dict[str, Any]]:
    """TJK AtKosuBilgileri sayfasını doğrudan okuyup ortak geçmiş şemasına çevirir.

    TJK'nin gerçek AtKosuBilgileri tablosu 2026 sürümünde tipik olarak şu sıradadır:
    Tarih, Şehir, Msf, Pist, S, Derece, Sıklet, Takı, Jokey, St, Gny,
    Grup, K. No-K. Adı, Kcins, Ant., Sahip, HP, Ikramiye, S20.

    Buradaki kritik nokta: ``S`` bitiriş sırasıdır, ``St`` ise start/kulvardır.
    Eski parser bu iki alanı karıştırıyor ve 16 kolonluk eski şemaya zorladığı
    için geçmiş verisini BİZİM SKOR'a kullanılabilir biçimde aktaramıyordu.
    """
    urls = [
        f"https://www.tjk.org/TR/kurumsal/Query/ConnectedPage/AtKosuBilgileri?1=1&QueryParameter_AtId={at_id}",
        f"https://www.tjk.org/TR/map/Query/ConnectedPage/AtKosuBilgileri?1=1&QueryParameter_AtId={at_id}",
        f"https://www.tjk.org/TR/YarisSever/Query/ConnectedPage/AtKosuBilgileri?1=1&QueryParameter_AtId={at_id}",
    ]
    last_error = None

    def norm_header(x: str) -> str:
        x = _clean_value(x).lower()
        x = (x.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
               .replace("ü", "u").replace("ö", "o").replace("ç", "c"))
        x = re.sub(r"[^a-z0-9]+", "", x)
        return x

    header_alias = {
        "tarih": "date", "sehir": "city", "msf": "distance", "mesafe": "distance",
        "pist": "surface", "s": "place", "derece": "time", "siklet": "weight",
        "taki": "equipment", "jokey": "jockey", "st": "post", "gny": "odds",
        "grup": "group", "knokko": "raceName", "kno-kadi": "raceName",
        "kno-kadi": "raceName", "kcins": "raceType", "ant": "trainer",
        "ant": "trainer", "sahip": "owner", "hp": "hp", "ikramiye": "prize",
        "s20": "l20",
    }

    for url in urls:
        try:
            response = _get_http_session().get(
                url,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://www.tjk.org/",
                    "Cache-Control": "no-cache",
                },
            )
            if response.status_code >= 400:
                last_error = RuntimeError(f"TJK HTTP {response.status_code}")
                continue

            parser = _TJKTableParser()
            rows = parser.feed(response.text or "")
            parsed: List[Dict[str, Any]] = []
            header_idx = None
            header_map: Dict[int, str] = {}

            # Önce gerçek başlık satırını bul.
            for ri, cells in enumerate(rows):
                texts = [_clean_value(c[0]) for c in cells]
                norms = [norm_header(x) for x in texts]
                if "tarih" in norms and ("derece" in norms or "pist" in norms) and ("ikramiye" in norms or "hp" in norms):
                    header_idx = ri
                    for ci, h in enumerate(norms):
                        if h in header_alias:
                            header_map[ci] = header_alias[h]
                    break

            for ri, cells in enumerate(rows):
                if header_idx is not None and ri <= header_idx:
                    continue
                texts = [_clean_value(c[0]) for c in cells]
                if len(texts) < 8:
                    continue
                first = str(texts[0] if texts else "")
                if not re.search(r"\d{1,2}[./]\d{1,2}[./]20\d{2}", first):
                    continue

                row: Dict[str, Any] = {}
                if header_map:
                    for ci, key in header_map.items():
                        if ci < len(texts):
                            row[key] = texts[ci]
                else:
                    # Fallback: güncel TJK tablosunun bilinen 19 kolon sırası.
                    cols = [
                        "date", "city", "distance", "surface", "place", "time", "weight",
                        "equipment", "jockey", "post", "odds", "group", "raceName", "raceType",
                        "trainer", "owner", "hp", "prize", "l20",
                    ]
                    row = {cols[i]: texts[i] for i in range(min(len(cols), len(texts)))}

                nr = _normalize_history_row(row)
                if nr and nr.get("date"):
                    parsed.append(nr)

            if parsed:
                return parsed
            last_error = RuntimeError("TJK geçmiş tablosu bulundu ancak yarış satırı ayrıştırılamadı")
        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error
    return []

def get_horse_history(at_id: Any, timeout: int = 45) -> Dict[str, Any]:
    if at_id in (None, ""):
        return {"ok": False, "history": [], "error": "atId yok"}
    try:
        history = _direct_tjk_history(str(at_id), timeout=min(timeout, 35))
        return {"ok": bool(history), "history": history, "historyCount": len(history),
                "earnings": _earnings_from_history(history),
                "historySource": "TJK AtKosuBilgileri (doğrudan)"}
    except Exception as exc:
        return {"ok": False, "history": [], "historyCount": 0, "error": str(exc)}


def get_horse_workouts(horse: str, timeout: int = 45) -> Dict[str, Any]:
    horse_name = normalize_text(horse)
    if not horse_name:
        return {"ok": False, "workouts": [], "error": "At adı yok"}
    from urllib.parse import quote
    urls = [
        f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?1=1&QueryParameter_ATADI={quote(horse_name)}",
        f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?1=1&QueryParameter_AtAdi={quote(horse_name)}",
    ]
    errors = []
    for url in urls:
        try:
            response = _get_http_session().get(url, timeout=timeout, headers=_tjk_headers())
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}: {url}")
                continue
            workouts = _parse_tjk_workouts(response.text)
            if workouts:
                return {"ok": True, "status": response.status_code, "horse": horse_name,
                        "workouts": workouts, "source": url}
        except requests.RequestException as exc:
            errors.append(str(exc))
    return {"ok": False, "workouts": [], "horse": horse_name,
            "error": "; ".join(errors) if errors else "TJK galop sayfasında ayrıştırılabilir kayıt bulunamadı."}



def get_horse_enrichment(
    at_id: Any,
    horse: str,
    timeout: int = 30,
    target_date: Any = None,
    target_city: str = "",
    target_distance: Any = None,
    target_surface: str = "",
    target_class: str = "",
) -> Dict[str, Any]:
    """
    Mevcut uygulama mimarisini bozmadan gerçek koşu geçmişi ve galop verisini
    hafif TJK sayfalarından alır.

    ÖNEMLİ:
    Eski sürüm önce /horsedata çağırıyordu. Bu endpoint tek at için birden
    fazla TJK sayfası taradığı için TJK 503/resource-limit oluşturabiliyordu.
    Burada doğrudan mevcut /horse ve /workouts endpointleri kullanılır.
    target_* parametreleri uygulama ile geriye dönük uyumluluk için korunur.
    """
    horse_name = normalize_text(horse)
    errors: List[str] = []

    def fetch_history() -> Dict[str, Any]:
        if at_id in (None, ""):
            return {"ok": False, "history": [], "error": "atId yok"}
        try:
            return get_horse_history(at_id, timeout=timeout)
        except Exception as exc:
            return {"ok": False, "history": [], "error": str(exc)}

    def fetch_workouts() -> Dict[str, Any]:
        if not horse_name:
            return {"ok": False, "workouts": [], "error": "At adı yok"}
        try:
            return get_horse_workouts(horse_name, timeout=timeout)
        except Exception as exc:
            return {"ok": False, "workouts": [], "error": str(exc)}

    # Tek at seçildiğinde iki hafif endpoint aynı anda çalışır.
    # Her istek kendi thread-local HTTP session bağlantı havuzunu kullanır.
    with ThreadPoolExecutor(max_workers=2) as executor:
        history_future = executor.submit(fetch_history)
        workout_future = executor.submit(fetch_workouts)
        history_data = history_future.result()
        workout_data = workout_future.result()

    history = _extract_history_payload(history_data) if isinstance(history_data, dict) else []
    workouts = workout_data.get("workouts", []) if isinstance(workout_data, dict) else []

    if not isinstance(history, list):
        history = []
    if not isinstance(workouts, list):
        workouts = []

    # get_horse_history() zaten /horse -> /horsedata -> doğrudan TJK
    # fallback zincirini kendi içinde tamamlar. Burada aynı zinciri ikinci
    # kez çalıştırmıyoruz. Galop endpointi de yalnızca bir kez sorgulanır.
    # Bu, özellikle çok atlı koşularda gereksiz HTTP çağrılarını ciddi azaltır.

    if not history and isinstance(history_data, dict) and history_data.get("error"):
        errors.append(f"horse: {history_data.get('error')}")
    if not workouts and isinstance(workout_data, dict) and workout_data.get("error"):
        errors.append(f"workouts: {workout_data.get('error')}")

    # TJK geçmişi boş dönerse, Streamlit sunucusundan TJK'nın gerçek at geçmişini
    # doğrudan sorgula. Bu yalnızca TJK geçmişi gerçekten boşsa çalışır.
    if not history and at_id not in (None, ""):
        try:
            direct = _direct_tjk_history(str(at_id), timeout=min(timeout, 25))
            if direct:
                history = direct
                history_data = dict(history_data or {})
                history_data["history"] = history
                history_data["historyCount"] = len(history)
                history_data["earnings"] = _earnings_from_history(history)
        except Exception as exc:
            errors.append(f"direct TJK history: {exc}")

    errors = list(dict.fromkeys(errors))

    # TJK /api/tjk/horse artık resmi kazanç ve hangi TJK kaynağının
    # kullanıldığını da döndürüyor. Bunları Streamlit'e aynen taşı.
    result: Dict[str, Any] = {
        "ok": bool(history or workouts),
        "history": history,
        "workouts": workouts,
        "historyCount": len(history),
        "workoutCount": len(workouts),
    }
    if isinstance(history_data, dict):
        if isinstance(history_data.get("earnings"), dict):
            result["earnings"] = history_data.get("earnings")
        if history_data.get("historySource"):
            result["historySource"] = history_data.get("historySource")
        if history_data.get("atId"):
            result["atId"] = history_data.get("atId")
    if "earnings" not in result:
        result["earnings"] = {"total": None, "year": None}
    if isinstance(result.get("earnings"), dict):
        derived = _earnings_from_history(history)
        if result["earnings"].get("total") in (None, "", 0, 0.0):
            result["earnings"]["total"] = derived.get("total")
        if result["earnings"].get("year") in (None, "", 0, 0.0):
            result["earnings"]["year"] = derived.get("year")

    if errors:
        result["error"] = " | ".join(errors)
    return result

# =========================================================
# GERİYE DÖNÜK UYUMLULUK
# =========================================================

def fetch_program(
    date_value: Any,
    city: str,
) -> Dict[str, Any]:

    return normalize_program(
        get_program(
            date_value,
            city,
        )
    )


def load_program(
    date_value: Any,
    city: str,
) -> Dict[str, Any]:

    return normalize_program(
        get_program(
            date_value,
            city,
        )
    )
