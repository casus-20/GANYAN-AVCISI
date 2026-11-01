"""REYTİNG motoru - Race Intelligence kaynak kodundan ayrıştırılmıştır."""
from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List
import re, math
import bizim_skor_model as _BIZIM_MODULE

_RATING_WEIGHTS = {
    "Ortak Rakip + Kilo": 0.35,
    "Kilo Uyumu": 0.05,
    "Güncel Form": 0.25,
    "Pist / Mesafe": 0.15,
    "Sınıf Uyumu": 0.20,
}

_RATING_FORM_WEIGHTS = (0.30, 0.22, 0.17, 0.13, 0.10, 0.08)

_RATING_FORM_POINTS = {
    1: 100.0, 2: 90.0, 3: 80.0, 4: 70.0, 5: 60.0,
    6: 50.0, 7: 40.0, 8: 30.0, 9: 20.0,
}

_RATING_FINISH_FACTOR = {
    1: 1.00, 2: 0.90, 3: 0.80, 4: 0.70, 5: 0.60,
}

_RATING_CLASS_BASE = dict(_BIZIM_MODULE.CLASS_BASE)

def display_value(
    value: Any,
    default: str = "-",
) -> str:

    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text

def get_race_number(
    race: Dict[str, Any],
    fallback: int,
) -> int:

    value = race.get(
        "race_number",
        fallback,
    )

    try:
        return int(value)
    except Exception:
        return fallback

def get_race_condition(race: Dict[str, Any]) -> str:
    """TJK'nın gerçek koşu şartını başlıktan çıkarır.

    Önemli: ``Tüm Koşular`` bir filtre değeridir; koşu şartı değildir.
    TJK program parser'ının koruduğu ``meta.raw`` / ``raw`` başlığı varsa,
    şartı doğrudan o başlıktan çıkarıyoruz. Böylece örneğin:

        9. Koşu 18:00 Handikap 16/DHÖW /H1, 4 ve Yukarı Araplar 1500 Sentetik ...

    başlığından yalnızca gerçek şart:

        Handikap 16/DHÖW /H1, 4 ve Yukarı Araplar

    alınır.
    """
    def clean(value: Any) -> str:
        text = display_value(value, "") if value not in (None, "") else ""
        text = re.sub(r"\s+", " ", text).strip(" ,;-:")
        if text.lower() in {"tüm koşular", "tum kosular", "-"}:
            return ""
        return text

    race_no = get_race_number(race, 0)
    race_time = clean(race.get("race_time") or race.get("time"))
    distance = clean(race.get("distance"))
    surface = clean(race.get("surface"))

    # 1) TJK'nın ham koşu başlığından çıkar. Bu, önceki denemede eksik kalan
    # kritik kısımdır: condition alanı '-' olsa bile meta.raw gerçek başlığı taşır.
    raw_sources = []
    meta = race.get("meta")
    if isinstance(meta, dict):
        for key in ("raw", "detail", "raceDetail", "race_detail", "header", "raceHeader", "race_header"):
            value = clean(meta.get(key))
            if value:
                raw_sources.append(value)
    for key in ("raw", "detail", "raceDetail", "race_detail", "header", "raceHeader", "race_header"):
        value = clean(race.get(key))
        if value:
            raw_sources.append(value)

    for raw in raw_sources:
        # Bir raw metni birden fazla koşuyu içerebiliyorsa seçili koşunun
        # son "N. Koşu" işaretinden itibaren olan bölümünü kullan.
        marks = list(re.finditer(r"\b(\d{1,2})\.\s*Koşu\b", raw, flags=re.I))
        if marks:
            wanted = [m for m in marks if race_no and int(m.group(1)) == int(race_no)]
            raw = raw[(wanted[-1] if wanted else marks[-1]).start():]

        # Başlangıç: "9. Koşu 18:00". Saat yoksa sadece "9. Koşu".
        if race_no:
            prefix = rf"\b{int(race_no)}\.\s*Koşu\b"
        else:
            prefix = r"\b\d{1,2}\.\s*Koşu\b"
        m = re.search(prefix, raw, flags=re.I)
        if not m:
            continue
        tail = raw[m.end():].strip()

        if race_time and race_time != "-":
            # Saat formatı 18:00 / 18.00 vb. olabilir.
            tm = re.search(r"^\s*" + re.escape(race_time) + r"\s*", tail)
            if tm:
                tail = tail[tm.end():]
            else:
                tm = re.search(r"^\s*\d{1,2}[:.]\d{2}\s*", tail)
                if tm:
                    tail = tail[tm.end():]

        # İkramiye ve prim bölümlerine gelmeden önce kes.
        tail = re.split(
            r"\s+(?=(?:İkramiye|Ikramiye|Yetiştirici(?:lik)? Primi|Yetistirici(?:lik)? Primi|At\s*Sahibi\s*Primi)\s*[:\-]?)",
            tail,
            maxsplit=1,
            flags=re.I,
        )[0].strip(" ,;-:")

        # Mesafe + pist kısmından hemen önceki metin gerçek koşu şartıdır.
        if distance and distance != "-":
            dm = re.search(r"\b" + re.escape(distance) + r"\b", tail, flags=re.I)
            if dm:
                candidate = clean(tail[:dm.start()])
                if candidate:
                    return candidate

        # Mesafe alanı farklı biçimde geldiyse, pist adı üzerinden kes.
        if surface and surface != "-":
            sm = re.search(r"\b" + re.escape(surface) + r"\b", tail, flags=re.I)
            if sm:
                before_surface = tail[:sm.start()].strip()
                # Son sayı grubunu mesafe kabul edip çıkar.
                candidate = re.sub(r"\s+\d{3,4}\s*$", "", before_surface).strip(" ,;-:")
                candidate = clean(candidate)
                if candidate:
                    return candidate

        # Son çare: ham başlıktaki ilk anlamlı metin; ancak filtre/boş değer dönmesin.
        candidate = clean(tail)
        candidate = re.sub(r"\s+\d{3,4}\s+(?:Kum|Çim|Sentetik)\b.*$", "", candidate, flags=re.I)
        if candidate:
            return candidate

    # 2) Ham başlık yoksa doğrudan normalize edilmiş alanları kullan.
    candidates = []
    for key in (
        "condition", "raceCondition", "race_condition",
        "conditionName", "condition_name", "className", "class",
        "sinif", "sınıf", "raceName", "race_name", "kosu",
        "title", "name",
    ):
        value = clean(race.get(key))
        if value:
            candidates.append(value)

    if isinstance(meta, dict):
        for key in (
            "condition", "raceCondition", "race_condition",
            "conditionName", "condition_name", "className", "class",
            "sinif", "sınıf", "raceName", "race_name", "kosu",
            "title", "name", "detail",
        ):
            value = clean(meta.get(key))
            if value:
                candidates.append(value)

    for candidate in candidates:
        candidate = re.split(
            r"\s+(?=İkramiye\s*:|Ikramiye\s*:|Yetiştirici(?:lik)?\s+Primi\s*:|At\s*Sahibi\s*Primi\s*:)",
            candidate, maxsplit=1, flags=re.I,
        )[0]
        candidate = clean(candidate)
        if candidate:
            return candidate

    return "-"

def _weight_parts(value: Any) -> tuple[str, str]:
    text = display_value(value, "")
    if not text:
        return "-", ""

    # TJK programlarında örn. "53 +1.20 Fazla Kilo" / "53,5" gibi
    # biçimler görülebilir. Ana kilo ilk satırda, fazla kilo ikinci satırda
    # gösterilir; veri kaybedilmez.
    m = re.match(
        r"^\s*(\d+(?:[.,]\d+)?)\s*(.*)$",
        text,
        flags=re.I,
    )
    if not m:
        return text, ""

    base = m.group(1).replace(",", ".")
    rest = (m.group(2) or "").strip()
    if not rest:
        return base, ""

    # Fazla kilo bilgisini aynı hücrede ikinci satıra taşır.
    fm = re.search(r"([+\-]\s*\d+(?:[.,]\d+)?)", rest)
    if fm:
        return base, fm.group(1).replace(',', '.').replace(" ", "")
    return base, rest

def get_horse_weight(
    horse: Dict[str, Any],
) -> str:
    base, extra = _weight_parts(
        horse.get("siklet")
        or horse.get("Sıklet")
        or horse.get("weight")
    )
    return f"{base}\n{extra}" if extra else base

def _normalize_surface_for_table(value: Any) -> str:
    """Son 6 Y. renkleri için TJK pist adını standartlaştırır."""
    text = str(value or "").strip().lower()
    text = (
        text.replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    # TJK geçmişinde pist çoğu zaman K:Normal / Ç:Normal / S:Normal
    # biçiminde gelir. Prefix doğrudan pist türünü belirler.
    if text.startswith("k:") or text.startswith("k-") or text == "k":
        return "kum"
    if text.startswith("ç:") or text.startswith("c:") or text.startswith("c-") or text.startswith("cim:") or text == "ç" or text == "c":
        return "cim"
    if text.startswith("s:") or text.startswith("s-") or text == "s":
        return "sentetik"
    if any(x in text for x in ("cim", "grass", "turf")):
        return "cim"
    if any(x in text for x in ("sentetik", "synthetic", "polytrack", "fiber")):
        return "sentetik"
    if any(x in text for x in ("kum", "dirt", "sand")):
        return "kum"
    return ""

def _first_value(row: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    """Return the first non-empty field; use default when none is present."""
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default

def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(',', '.')
    if not text:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None

def _class_level_from_text(value: Any) -> float | None:
    """TJK geçmişindeki koşu sınıfını tek bir sınıf seviyesine dönüştürür.

    Bu değer BİZİM SKOR veya ŞART UYUMU değildir.
    Amaç yalnızca atın son gerçek koşularında hangi sınıf seviyelerinde
    koştuğunu ölçmek ve bunu GÜNCEL SINIF olarak göstermek.

    Öncelik: açık sınıf > KV > Şartlı > Handikap.
    Handikaplarda H numarası doğrudan kullanılır.
    Şartlı koşularda Şartlı 1-5 sırası kullanılır.
    """
    text = str(value or "").upper().strip()
    if not text or text == "-":
        return None

    # Açık sınıf koşular
    for pat, score in (
        (r"\bG\s*1\b", 100.0),
        (r"\bG\s*2\b", 97.0),
        (r"\bG\s*3\b", 94.0),
        (r"\bAÇIK\b", 90.0),
    ):
        if re.search(pat, text):
            return score

    # Kısa vadeli / KV koşuları. KV numarası yükseldikçe sınıf seviyesi yükselir.
    m = re.search(r"\bKV\s*[- ]?\s*(\d+)\b", text)
    if m:
        n = int(m.group(1))
        return min(89.0, 70.0 + n * 2.0)

    # Şartlı 1-5. TJK bazı kayıtlarda "Şartlı" ile sınıf numarasını
    # ayrı alanlarda döndürebilir; bu nedenle numaranın hemen yanında
    # veya aynı metin içinde bulunmasını kabul ediyoruz.
    m = re.search(r"(?:ŞARTLI|ŞART)\s*[-/]?\s*([1-5])\b", text)
    if not m:
        m = re.search(r"\b([1-5])\s*[-/]?\s*(?:ŞARTLI|ŞART)\b", text)
    if not m and re.search(r"\bŞARTLI\b|\bŞART\b", text):
        nums = re.findall(r"\b([1-5])\b", text)
        if nums:
            m = re.match(r"(.*)", nums[0])
            n = int(nums[0])
            return 35.0 + n * 7.0
    if m:
        n = int(m.group(1))
        return 35.0 + n * 7.0

    # Handikap H1-H18. H numarası sınıf seviyesini doğrudan temsil eder.
    m = re.search(r"\bH\s*(\d{1,2})\b", text)
    if m:
        n = int(m.group(1))
        return min(86.0, 30.0 + n * 3.0)

    # Satış / Maiden gibi diğer yarışlar.
    if "SATIŞ" in text or "SATIS" in text:
        m = re.search(r"(?:SATIŞ|SATIS)\s*[- ]?(\d+)", text)
        return 25.0 + (int(m.group(1)) if m else 1) * 3.0
    if "MAIDEN" in text:
        return 25.0

    return None

def _rating_place_number(value: Any) -> int | None:
    if value is None:
        return None
    m = re.search(r"\d+", str(value).strip())
    if not m:
        return None
    try:
        return int(m.group(0))
    except Exception:
        return None

def _rating_finish_points(place: Any) -> float:
    p = _rating_place_number(place)
    # Sıra verisi yoksa atı otomatik sonuncu sayma; nötr puan kullan.
    if p is None or p <= 0:
        return 50.0
    return _RATING_FORM_POINTS.get(p, 10.0)

def _rating_parse_date(value: Any) -> date | None:
    """TJK tarih alanlarını farklı formatlarda güvenli biçimde çözer."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text or text in {"-", "—", "None", "null"}:
        return None

    # ISO timestamp: 2026-10-07T20:30:00 / 2026-10-07 20:30:00
    iso = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso).date()
    except Exception:
        pass

    # TJK'da görülebilecek tarih biçimleri.
    for fmt in (
        "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y",
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    ):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except Exception:
            pass

    # Metnin içinde tarih varsa (örn. '07.10.2026 20:30') bul.
    m = re.search(r"(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})", text)
    if m:
        token = m.group(1)
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(token, fmt).date()
            except Exception:
                pass
    return None

def _history_value(row: Any, keys: List[str]) -> Any:
    """Geçmiş yarış kaydında alanı derinlemesine ve güvenli biçimde bulur.

    TJK/Worker bazı yanıtlarda tarih ve koşu sınıfını doğrudan satıra,
    bazılarında race/result/data gibi iç içe yapılara koyabiliyor. Önceki
    sürüm yalnızca bir seviye aradığı için tek geçmiş yarışı olan bazı
    atlarda GÜNCEL SINIF gereksiz yere boş kalabiliyordu.
    """
    wanted = {str(k).casefold() for k in keys}
    seen = set()

    def walk(obj: Any, depth: int = 0) -> Any:
        if depth > 8:
            return ""
        if isinstance(obj, dict):
            oid = id(obj)
            if oid in seen:
                return ""
            seen.add(oid)

            # Önce bu seviyedeki doğrudan alanları kontrol et.
            for k, v in obj.items():
                if str(k).casefold() in wanted and v not in (None, "", [], {}):
                    return v

            # Sonra iç içe dict/list yapılarını tara.
            for v in obj.values():
                if isinstance(v, (dict, list, tuple)):
                    found = walk(v, depth + 1)
                    if found not in (None, "", [], {}):
                        return found
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                if isinstance(v, (dict, list, tuple)):
                    found = walk(v, depth + 1)
                    if found not in (None, "", [], {}):
                        return found
        return ""

    return walk(row)

def _rating_row_value(row: Dict[str, Any], keys: List[str]) -> Any:
    """REYTİNG geçmişinde hem üst hem iç içe TJK alanlarını aynı şekilde oku."""
    return _history_value(row, keys)

def _rating_row_date(row: Dict[str, Any]) -> date | None:
    return _rating_parse_date(_rating_row_value(row, [
        "date", "tarih", "Tarih", "raceDate", "race_date", "kosuTarihi",
        "race_date_local", "runDate", "run_date", "kosuTarihiLocal",
        "startDate", "start_date", "raceDay", "race_day", "yarisTarihi",
        "yaris_tarihi", "eventDate", "event_date"
    ]))

def _rating_history_before_target(
    horse: Dict[str, Any],
    target_date: Any = None,
) -> list[Dict[str, Any]]:
    """Sadece tarih < hedef tarih kayıtlarını döndürür."""
    history = horse.get("_history", [])
    if not isinstance(history, list):
        return []

    target_dt = _rating_parse_date(target_date) if target_date is not None else None
    out = []
    for row in history:
        if not isinstance(row, dict):
            continue
        if target_dt is None:
            out.append(row)
            continue
        row_dt = _rating_parse_date(_history_value(row, [
            "date", "tarih", "Tarih", "raceDate", "race_date", "kosuTarihi",
            "race_date_local", "runDate", "run_date", "kosuTarihiLocal",
            "startDate", "start_date", "raceDay", "race_day", "yarisTarihi",
            "yaris_tarihi", "kosuTarihiLocal", "eventDate", "event_date"
        ]))
        # Tarih çözülemeyen kayıt, veri sızıntısını önlemek için kullanılmaz.
        if row_dt is not None and row_dt < target_dt:
            out.append(row)

    out.sort(key=lambda r: _rating_row_date(r) or date.min, reverse=True)
    return out

def _rating_surface(value: Any) -> str:
    try:
        return str(_normalize_surface_for_table(value) or "").strip().lower()
    except Exception:
        s = str(value or "").strip().lower()
        s = s.replace("sentetik", "sentetik").replace("synthetic", "sentetik")
        s = s.replace("çim", "çim").replace("grass", "çim")
        s = s.replace("kum", "kum").replace("dirt", "kum")
        return s

def _rating_distance(row: Dict[str, Any]) -> float | None:
    return _number(_rating_row_value(row, [
        "distance", "msf", "mesafe", "Msf", "distanceMeters", "distance_meters"
    ]))

def _rating_weight_value(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None

def _rating_row_weight(row: Dict[str, Any]) -> float | None:
    return _rating_weight_value(_rating_row_value(row, [
        "weight", "kilo", "siklet", "Sıklet", "carriedWeight", "carried_weight"
    ]))

def _rating_target_weight(horse: Dict[str, Any]) -> float | None:
    try:
        return _rating_weight_value(get_horse_weight(horse).split("\n")[0])
    except Exception:
        return _rating_weight_value(_first_value(horse, [
            "siklet", "Sıklet", "weight", "kilo"
        ]))

def _rating_recency_factor(row: Dict[str, Any], target_date: Any) -> float:
    target_dt = _rating_parse_date(target_date)
    row_dt = _rating_row_date(row)
    if target_dt is None or row_dt is None:
        return 0.50
    days = max(0, (target_dt - row_dt).days)
    if days <= 30: return 1.00
    if days <= 60: return 0.90
    if days <= 90: return 0.80
    if days <= 180: return 0.65
    if days <= 365: return 0.50
    return 0.30

def _rating_distance_proximity(history_distance: float | None, target_distance: float | None) -> float:
    if history_distance is None or target_distance is None:
        return 50.0
    diff = abs(float(history_distance) - float(target_distance))
    if diff <= 0.01: return 100.0
    if diff <= 100: return 95.0
    if diff <= 200: return 85.0
    if diff <= 300: return 70.0
    if diff <= 400: return 55.0
    return 35.0

def _rating_weight_similarity(history_weight: float | None, target_weight: float | None) -> float:
    if history_weight is None or target_weight is None:
        return 50.0
    diff = abs(history_weight - target_weight)
    if diff <= 0.01: return 100.0
    if diff <= 1: return 95.0
    if diff <= 2: return 90.0
    if diff <= 3: return 80.0
    if diff <= 4: return 70.0
    if diff <= 5: return 60.0
    if diff <= 6: return 50.0
    return 35.0

def _rating_row_race_key(row: Dict[str, Any]) -> tuple:
    """TJK geçmişindeki aynı koşuyu ID varsa ID ile, yoksa alanlarıyla eşleştirir."""
    race_id = _rating_row_value(row, [
        "raceId", "race_id", "kosuId", "kosu_id", "raceKey", "race_key",
        "eventId", "event_id", "resultId", "result_id"
    ])
    dt = _rating_row_date(row)
    city = str(_rating_row_value(row, [
        "city", "cityName", "city_name", "hipodrom", "hipodromAdi",
        "hipodrom_adi", "hippodrome", "hippodromeName", "hippodrome_name",
        "track", "trackName", "track_name", "raceTrack", "race_track",
        "location", "venue"
    ]) or "").strip().lower()
    dist = _rating_distance(row)
    surface = _rating_surface(_rating_row_value(row, [
        "surface", "pist", "pistAdi", "pist_adi", "trackSurface",
        "track_surface", "surfaceType", "surface_type", "trackType",
        "track_type", "trackCondition", "track_condition"
    ]))
    race_no = _rating_row_value(row, [
        "raceNo", "race_no", "kosuNo", "kosu_no", "raceNumber",
        "race_number", "kosuSirasi", "kosu_sirasi"
    ])
    race_name = str(_rating_row_value(row, [
        "raceName", "race_name", "kosuAdi", "kosu_adi", "conditionName",
        "condition_name", "className", "class_name", "raceClass",
        "race_class", "condition", "raceCondition", "race_condition",
        "raceType", "race_type"
    ]) or "").strip().lower()
    if race_id not in (None, ""):
        return ("id", str(race_id).strip())
    return (
        "fields",
        dt.isoformat() if dt else "",
        " ".join(city.split()),
        round(dist, 1) if dist is not None else "",
        surface,
        str(race_no or "").strip(),
        " ".join(race_name.split()),
    )

def _rating_shared_race_keys(
    h1: Dict[str, Any],
    h2: Dict[str, Any],
    target_date: Any,
) -> list[tuple[Dict[str, Any], Dict[str, Any]]]:
    """Aynı geçmiş yarışı yanlış pozitif üretmeden eşleştirir."""
    a = _rating_history_before_target(h1, target_date)
    b = _rating_history_before_target(h2, target_date)
    idx = {}
    for row in b:
        idx.setdefault(_rating_row_race_key(row), []).append(row)

    pairs = []
    used = set()
    for row_a in a:
        key_a = _rating_row_race_key(row_a)
        candidates = list(idx.get(key_a, []))
        # ID yoksa yarış adı farklı/eksik gelebilir. Ancak tarih, hipodrom,
        # mesafe, pist ve varsa koşu numarası uyumlu olmalı.
        if not candidates and key_a and key_a[0] == "fields":
            _, dt_a, city_a, dist_a, surface_a, no_a, _name_a = key_a
            if dt_a and dist_a != "" and surface_a:
                for key_b, rows_b in idx.items():
                    if not key_b or key_b[0] != "fields":
                        continue
                    _, dt_b, city_b, dist_b, surface_b, no_b, _name_b = key_b
                    if (dt_a != dt_b or dist_a != dist_b or surface_a != surface_b):
                        continue
                    if city_a and city_b and city_a != city_b:
                        continue
                    if no_a and no_b and no_a != no_b:
                        continue
                    # Yarış adı her iki tarafta varsa farklı isimli koşuları eşleştirme.
                    if _name_a and _name_b and _name_a != _name_b:
                        continue
                    candidates.extend(rows_b)
        for row_b in candidates:
            pair_key = (id(row_a), id(row_b))
            if pair_key in used:
                continue
            used.add(pair_key)
            pairs.append((row_a, row_b))
            break
    return pairs

def _rating_common_opponent_score(
    horse: Dict[str, Any],
    horses: List[Dict[str, Any]],
    target_date: Any,
) -> float:
    """Bugünkü alandaki rakiplerle geçmişteki ortak yarışları karşılaştırır."""
    target_no = str(horse.get("_at_id") or horse.get("atId") or id(horse))
    values = []

    for other in horses:
        if not isinstance(other, dict):
            continue
        other_no = str(other.get("_at_id") or other.get("atId") or id(other))
        if other_no == target_no:
            continue

        for own_row, other_row in _rating_shared_race_keys(horse, other, target_date):
            own_p = _rating_finish_points(_rating_row_value(own_row, ["place", "sira", "Sıra", "S", "finishPosition", "finish_position", "rank"]))
            oth_p = _rating_finish_points(_rating_row_value(other_row, ["place", "sira", "Sıra", "S", "finishPosition", "finish_position", "rank"]))
            own_w = _rating_row_weight(own_row)
            oth_w = _rating_row_weight(other_row)

            # Daha iyi sıra = pozitif; rakibe göre kilo avantajı = pozitif.
            score = 50.0 + 0.50 * (own_p - oth_p)
            if own_w is not None and oth_w is not None:
                score += 2.5 * (oth_w - own_w)

            score = max(0.0, min(100.0, score))
            values.append((score, _rating_recency_factor(own_row, target_date)))

    if not values:
        return 50.0

    return max(0.0, min(100.0,
        sum(v * w for v, w in values) / sum(w for _, w in values)
    ))

def _rating_field_weight_advantage(
    horse: Dict[str, Any],
    horses: List[Dict[str, Any]],
) -> float:
    own = _rating_target_weight(horse)
    if own is None:
        return 50.0
    others = [
        _rating_target_weight(h)
        for h in horses
        if isinstance(h, dict) and h is not horse
    ]
    others = [x for x in others if x is not None]
    if not others:
        return 50.0
    avg = sum(others) / len(others)
    return max(0.0, min(100.0, 50.0 + (avg - own) * 8.0))

def _rating_historical_weight_fit(
    horse: Dict[str, Any],
    target_date: Any,
) -> float:
    target_weight = _rating_target_weight(horse)
    history = _rating_history_before_target(horse, target_date)
    if target_weight is None or not history:
        return 50.0

    vals = []
    for row in history:
        rw = _rating_row_weight(row)
        if rw is None:
            continue
        sim = _rating_weight_similarity(rw, target_weight) / 100.0
        rec = _rating_recency_factor(row, target_date)
        vals.append((_rating_finish_points(_first_value(
            row, ["place", "sira", "Sıra", "S"]
        )), sim * rec))

    if not vals:
        return 50.0
    return max(0.0, min(100.0, sum(v*w for v,w in vals) / sum(w for _,w in vals)))

def _rating_weight_response(
    horse: Dict[str, Any],
    target_date: Any,
) -> float:
    """En az 3 geçmiş koşu varsa kilonun performansla ilişkisini ölçer."""
    history = _rating_history_before_target(horse, target_date)
    pairs = []
    for row in history[:30]:
        w = _rating_row_weight(row)
        p = _rating_place_number(_rating_row_value(row, ["place", "sira", "Sıra", "S", "finishPosition", "finish_position", "rank"]))
        if w is not None and p is not None:
            pairs.append((w, _rating_finish_points(p)))
    if len(pairs) < 3:
        return 50.0

    xbar = sum(x for x,_ in pairs) / len(pairs)
    ybar = sum(y for _,y in pairs) / len(pairs)
    den = sum((x-xbar)**2 for x,_ in pairs)
    if den <= 1e-9:
        return 50.0
    slope = sum((x-xbar)*(y-ybar) for x,y in pairs) / den
    # Negatif slope: kilo arttıkça performans düşüyor -> bugünkü kilo daha riskli.
    # Pozitif slope: geçmişte ağır kiloda da iyi performans -> avantaj.
    return max(0.0, min(100.0, 50.0 - slope * 8.0))

def _rating_weight_score(
    horse: Dict[str, Any],
    horses: List[Dict[str, Any]],
    target_date: Any,
) -> float:
    return max(0.0, min(100.0,
        0.40 * _rating_field_weight_advantage(horse, horses)
        + 0.35 * _rating_historical_weight_fit(horse, target_date)
        + 0.25 * _rating_weight_response(horse, target_date)
    ))

def _rating_all_history_form(horse: Dict[str, Any], target_date: Any) -> float | None:
    """Tüm geçmiş yarışları kullanır; yeni yarışlara daha fazla ağırlık verir.

    Yalnızca hedef tarihten önceki, bitiriş sırası okunabilen yarışlar puanlanır.
    Geçerli sonuç yoksa yapay/nötr puan üretmek yerine None döner.
    """
    history = _rating_history_before_target(horse, target_date)
    vals = []
    for row in history:
        place = _rating_place_number(_rating_row_value(
            row, ["place", "sira", "Sıra", "S", "finishPosition", "finish_position", "rank"]
        ))
        if place is None:
            continue
        points = _rating_finish_points(place)
        recency = _rating_recency_factor(row, target_date)
        # Her geçmiş yarış dahil; recency fonksiyonu eski yarışın etkisini azaltır.
        vals.append((points, recency))
    if not vals:
        return None
    denominator = sum(weight for _, weight in vals)
    if denominator <= 0:
        return None
    return max(0.0, min(100.0, sum(value * weight for value, weight in vals) / denominator))

def _rating_distance_component(
    horse: Dict[str, Any],
    target_distance: float | None,
    target_surface: str,
    target_date: Any,
) -> float:
    """Pist/mesafe = %35 mesafe + %30 pist + %20 benzer kilo + %15 güncellik."""
    history = _rating_history_before_target(horse, target_date)
    if not history:
        return 50.0

    target_weight = _rating_target_weight(horse)
    surface_target = _rating_surface(target_surface)

    distance_vals = []
    surface_vals = []
    weight_vals = []
    recency_vals = []

    for row in history:
        rec = _rating_recency_factor(row, target_date)
        dist = _rating_distance(row)
        rw = _rating_row_weight(row)
        row_surface = _rating_surface(_rating_row_value(row, [
            "surface", "pist", "Pist", "Surface", "trackSurface", "track_surface"
        ]))

        distance_vals.append((_rating_distance_proximity(dist, target_distance), rec))

        if surface_target and row_surface == surface_target:
            surface_vals.append((_rating_finish_points(_first_value(
                row, ["place", "sira", "Sıra", "S"]
            )), rec))

        weight_vals.append((_rating_weight_similarity(rw, target_weight), rec))
        recency_vals.append((rec * 100.0, 1.0))

    def weighted(vals, default=50.0):
        if not vals:
            return default
        return sum(v*w for v,w in vals) / sum(w for _,w in vals)

    m = weighted(distance_vals)
    p = weighted(surface_vals, 50.0)
    k = weighted(weight_vals)
    g = weighted(recency_vals)

    return max(0.0, min(100.0,
        0.35*m + 0.30*p + 0.20*k + 0.15*g
    ))

def _rating_class_group(value: Any) -> str:
    s = str(value or "").strip().lower()
    s = (s.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
           .replace("ü", "u").replace("ö", "o").replace("ç", "c"))
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    m = re.search(r"\b(?:g|grup|group)\s*[- ]?([123])\b", s)
    if m: return f"G{m.group(1)}"
    m = re.search(r"\b(?:acik|açik|açık|a)\s*[- ]?([123])\b", s)
    if m: return f"A{m.group(1)}"
    m = re.search(r"\bkv\s*[- ]?(\d+)\b", s)
    if m: return f"KV{m.group(1)}"
    m = re.search(r"\b(?:h|handikap)\s*[- ]?(\d+)\b", s)
    if m: return f"H{m.group(1)}"
    m = re.search(r"\b(?:s|sartli|sartlı)\s*[- ]?(\d+)\b", s)
    if m: return f"S{m.group(1)}"
    if "maiden" in s:
        return "MAIDEN"
    return ""

def _rating_class_base(group: str) -> float | None:
    if not group:
        return None
    if group in _RATING_CLASS_BASE:
        return float(_RATING_CLASS_BASE[group])
    v = _BIZIM_MODULE.class_base_points(group)
    return float(v) if v else None

def _rating_class_value(row: Dict[str, Any]) -> float | None:
    """Geçmiş koşu sınıfını yalnız sınıf/koşu türü alanlarından çıkarır."""
    keys = [
        "className", "class_name", "class", "classType", "class_type",
        "raceClass", "race_class", "raceClassName", "race_class_name",
        "raceType", "race_type", "raceTypeName", "race_type_name",
        "condition", "conditionName", "condition_name",
        "raceCondition", "race_condition", "kosuSarti", "kosu_sarti",
        "kosuSinifi", "kosu_sinifi", "sinif", "Sınıf",
        "raceName", "race_name", "kosuAdi", "kosu_adi", "kosu", "Koşu",
        "raceTitle", "race_title", "eventName", "event_name",
        "raceGroup", "race_group", "groupName", "group_name",
        "yarisTuru", "yaris_turu", "kosuTuru", "kosu_turu",
        "kosuSartiAdi", "kosu_sarti_adi", "sart", "şart", "sartli", "şartli",
    ]
    values = []
    for key in keys:
        value = _history_value(row, [key])
        if value not in (None, "", [], {}) and not isinstance(value, (dict, list)):
            text = str(value).strip()
            if text and text not in values:
                values.append(text)

    # Şartlı/Handikap gibi tür ile sınıf numarası ayrı alanlardaysa birleştir.
    combined = " ".join(values)
    if combined:
        values.append(combined)

    base = None
    for raw in values:
        group = _rating_class_group(raw)
        candidate = _rating_class_base(group)
        if candidate is None:
            candidate = _class_level_from_text(raw)
        if candidate is not None:
            base = candidate
            break
    if base is None:
        return None

    place = _rating_place_number(_rating_row_value(row, [
        "place", "sira", "Sıra", "finishPosition", "finish_position",
        "rank", "finish", "position", "result"
    ]))
    if place is None:
        return base * 0.50
    return base * (_BIZIM_MODULE.finish_factor(place) or 0.20)

def _rating_target_class_value(race: Dict[str, Any]) -> float:
    raw = _rating_row_value(race, [
        "condition", "conditionName", "condition_name", "raceCondition", "race_condition",
        "className", "class_name", "raceClass", "race_class", "raceType", "race_type",
        "raceTypeName", "race_type_name", "raceName", "race_name", "kosu", "Koşu", "class"
    ]) or get_race_condition(race)
    group = _rating_class_group(raw)
    _gb = _rating_class_base(group)
    if _gb is not None:
        return _gb
    lv = _class_level_from_text(raw)
    return lv if lv is not None else 50.0

def _rating_class_score(
    horse: Dict[str, Any],
    race: Dict[str, Any],
    target_date: Any,
) -> float:
    target = _rating_target_class_value(race)
    history = _rating_history_before_target(horse, target_date)
    vals = []
    for row in history:
        v = _rating_class_value(row)
        if v is None:
            continue
        rec = _rating_recency_factor(row, target_date)
        # Bugünkü sınıfa yakın geçmiş daha güçlü referans.
        proximity = max(0.25, 1.0 - abs(v-target)/100.0)
        vals.append((v, rec * proximity))
    if not vals:
        return 50.0

    hist = sum(v*w for v,w in vals) / sum(w for _,w in vals)
    # Geçmiş sınıf seviyesi bugünkü seviyeye ne kadar yakınsa o kadar yüksek.
    similarity = max(0.0, 100.0 - abs(hist - target))
    return max(0.0, min(100.0, 0.55*similarity + 0.45*hist))

def _calculate_rating_for_race(
    horses: List[Dict[str, Any]],
    race: Dict[str, Any],
) -> list[Dict[str, Any]]:
    target_date = race.get("date")
    target_distance = _number(race.get("distance"))
    target_surface = display_value(race.get("surface"), "")
    results = []
    for idx, horse in enumerate(horses):
        if not isinstance(horse, dict):
            continue

        # KESİN KURAL:
        # Hedef tarihten önce en az 1 gerçek yarış yoksa REYTİNG hesaplanmaz.
        eligible_history = _rating_history_before_target(horse, target_date)
        if not eligible_history:
            continue

        components = {
            "Ortak Rakip + Kilo": _rating_common_opponent_score(horse, horses, target_date),
            "Kilo Uyumu": _rating_weight_score(horse, horses, target_date),
            "Güncel Form": _rating_all_history_form(horse, target_date),
            "Pist / Mesafe": _rating_distance_component(
                horse, target_distance, target_surface, target_date
            ),
            "Sınıf Uyumu": _rating_class_score(horse, race, target_date),
        }

        # Veri varlığını bileşen bazında doğrula. Kaynak veri yoksa 50 puan
        # vermek yerine bileşeni eksik işaretle; veri toplama/enrichment
        # katmanı (_history / _workouts) gerçek kayıtları sağlar.
        own_history = _rating_history_before_target(horse, target_date)
        if not any(
            _rating_shared_race_keys(horse, other, target_date)
            for other in horses if isinstance(other, dict) and other is not horse
        ):
            components["Ortak Rakip + Kilo"] = None
        if _rating_target_weight(horse) is None or not any(
            _rating_row_weight(r) is not None for r in own_history
        ):
            components["Kilo Uyumu"] = None
        if not any(
            _rating_place_number(_rating_row_value(r, ["place", "sira", "Sıra", "S", "finishPosition", "finish_position", "rank"])) is not None
            for r in own_history
        ):
            components["Güncel Form"] = None
        if not any(
            _rating_distance(r) is not None
            and _rating_surface(_rating_row_value(r, ["surface", "pist", "Pist", "Surface", "trackSurface", "track_surface", "surfaceType", "surface_type", "trackType", "track_type"])) == _rating_surface(target_surface)
            for r in own_history
        ):
            components["Pist / Mesafe"] = None
        if not any(_rating_class_value(r) is not None for r in own_history):
            components["Sınıf Uyumu"] = None

        # Eksik veri için 50 puan uydurulmaz. Yalnız gerçek puanı hesaplanan
        # bileşenler kullanılır; kalan ağırlıklar mevcut bileşenler arasında
        # oranlı olarak yeniden dağıtılır. Bileşen detayı eksik olanı gösterir.
        available = {
            key: value for key, value in components.items()
            if isinstance(value, (int, float)) and math.isfinite(float(value))
        }
        if not available:
            continue
        weight_total = sum(_RATING_WEIGHTS[key] for key in available)
        if weight_total <= 0:
            continue
        score = sum(
            float(available[key]) * (_RATING_WEIGHTS[key] / weight_total)
            for key in available
        )

        results.append({
            "horse_index": idx,
            "score": round(max(0.0, min(100.0, score)), 2),
            "components": {k: (round(float(v), 2) if isinstance(v, (int, float)) and math.isfinite(float(v)) else None) for k,v in components.items()},
            "available_components": len(available),
            "available_weight_pct": round(weight_total * 100, 2),
        })

    results.sort(key=lambda x: (-x["score"], x["horse_index"]))
    for rank, item in enumerate(results, 1):
        item["rank"] = rank
        item["label"] = (
            "ÇOK GÜÇLÜ" if item["score"] >= 80 else
            "GÜÇLÜ" if item["score"] >= 70 else
            "ORTA" if item["score"] >= 55 else
            "ZAYIF"
        )
    return results

def calculate_rating_cached(horses: List[Dict[str, Any]], race: Dict[str, Any]):
    """REYTİNG için 180 dk cache; anahtar yarış tarihi/koşu ve gerçek geçmişi içerir."""
    return _calculate_rating_for_race(horses, race)
