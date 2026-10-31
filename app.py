from __future__ import annotations

import html
import io
import re
from pathlib import Path
from typing import Any
from html.parser import HTMLParser

import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# EQUEST / DEVEXPRESS SAHİP İSTATİSTİK ANALİZİ
# CSS dosyası assets/devexpress.css konumundan okunur. CSS, Python kodu değildir.
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "assets" / "devexpress.css"

st.set_page_config(
    page_title="Equest | Sahip İstatistikleri",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded",
)

FIELD_KEYS = [
    "ATNO",
    "ATADI",
    "SAHIP",
    "AT_SAHIP",
    "SAHIP_GENEL",
    "SAHIP_SEHIR",
    "BINICI_SAHIP",
    "ANTRENOR_SAHIP",
    "SAHIP_TOPLAM",
]
FIELD_LABELS = {
    "ATNO": "At No",
    "ATADI": "Atın Adı",
    "SAHIP": "Sahibi",
    "AT_SAHIP": "Sahip-At",
    "SAHIP_GENEL": "Genel",
    "SAHIP_SEHIR": "Şehir",
    "BINICI_SAHIP": "Binici-Sahip",
    "ANTRENOR_SAHIP": "Antrenör-Sahip",
    "SAHIP_TOPLAM": "Kaynak Rating",
}
FACTOR_KEYS = [
    "AT_SAHIP",
    "SAHIP_GENEL",
    "SAHIP_SEHIR",
    "BINICI_SAHIP",
    "ANTRENOR_SAHIP",
]
FACTOR_LABELS = {
    "AT_SAHIP": "Sahip-At",
    "SAHIP_GENEL": "Genel",
    "SAHIP_SEHIR": "Şehir",
    "BINICI_SAHIP": "Binici-Sahip",
    "ANTRENOR_SAHIP": "Antrenör-Sahip",
}
# Bu katsayılar örnek HTML verisinden çıkarılmış test hipotezidir; Equest'in
# doğrulanmış resmî formülü olarak sunulmaz. Katsayı analizi ekranı veriden
# ayrıca doğrusal regresyon tahmini üretir.
CANDIDATE_WEIGHTS = {
    "AT_SAHIP": 0.80,
    "SAHIP_GENEL": 0.85,
    "SAHIP_SEHIR": 0.45,
    "BINICI_SAHIP": 0.40,
    "ANTRENOR_SAHIP": 0.60,
}


def load_css() -> str:
    if not CSS_PATH.is_file():
        return ""
    try:
        return CSS_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def to_number(value: Any) -> float:
    text = clean_text(value).replace(".", "").replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return np.nan
    try:
        return float(match.group(0))
    except ValueError:
        return np.nan


class _EquestTableParser(HTMLParser):
    """Extract table rows using Python's standard library (no bs4 needed)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[tuple[str, list[str]]] = []
        self._table_depth = 0
        self._in_target_table = False
        self._row_id = ""
        self._cells: list[str] = []
        self._cell_parts: list[str] | None = None
        self._target_table_seen = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        if tag == "table":
            self._table_depth += 1
            if attrs_dict.get("id") == "gridIstatistikSahip_DXMainTable":
                self._in_target_table = True
                self._target_table_seen = True
        elif tag == "tr" and (self._in_target_table or not self._target_table_seen):
            self._row_id = attrs_dict.get("id", "") or ""
            self._cells = []
        elif tag == "td" and (self._in_target_table or not self._target_table_seen):
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._cell_parts is not None:
            value = clean_text(" ".join(self._cell_parts))
            self._cells.append(value)
            self._cell_parts = None
        elif tag == "tr" and (self._in_target_table or not self._target_table_seen):
            if self._cells:
                self.rows.append((self._row_id, self._cells[:]))
            self._row_id = ""
            self._cells = []
        elif tag == "table":
            if self._table_depth > 0:
                self._table_depth -= 1
            if self._in_target_table and self._table_depth == 0:
                self._in_target_table = False


def parse_equest_html(raw: str, source_name: str = "HTML") -> pd.DataFrame:
    """Parse DevExpress callback/full-page HTML containing gridIstatistikSahip."""
    parser = _EquestTableParser()
    parser.feed(raw)
    parser.close()

    # Prefer rows explicitly belonging to the target DevExpress grid.
    data_rows = [
        cells for row_id, cells in parser.rows
        if re.fullmatch(r"gridIstatistikSahip_DXDataRow\d+", row_id)
    ]
    # Some callback fragments omit row IDs; use the nine-column data rows.
    if not data_rows:
        data_rows = [cells for _, cells in parser.rows if len(cells) >= 9]

    records: list[dict[str, Any]] = []
    for cells in data_rows:
        if len(cells) < 9:
            continue
        values = [clean_text(value) for value in cells[:9]]
        if not values[0] or not values[1]:
            continue
        record = dict(zip(FIELD_KEYS, values))
        if record["ATADI"].lower() in {"atın adı", "at adi", "atadi"}:
            continue
        records.append(record)

    if not records:
        raise ValueError(
            "Dosyada gridIstatistikSahip tablosunda okunabilir at/sahip satırı bulunamadı. "
            "Equest'in Sahip İstatistikleri HTML/response içeriğini yükleyin."
        )

    df = pd.DataFrame(records)
    for key in ["ATNO", *FACTOR_KEYS, "SAHIP_TOPLAM"]:
        df[key] = df[key].map(to_number)
    df["ATNO"] = df["ATNO"].astype("Int64")
    df["Kaynak"] = source_name
    return df


def parse_uploaded_file(uploaded_file) -> pd.DataFrame:
    raw_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
    suffix = Path(filename).suffix.lower()
    if suffix in {".html", ".htm", ".txt", ".aspx"}:
        raw = raw_bytes.decode("utf-8", errors="replace")
        return parse_equest_html(raw, filename)
    if suffix == ".csv":
        df = pd.read_csv(io.BytesIO(raw_bytes))
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(io.BytesIO(raw_bytes))
    elif suffix == ".json":
        df = pd.read_json(io.BytesIO(raw_bytes))
    else:
        raise ValueError(f"Desteklenmeyen dosya türü: {suffix}")

    # CSV/Excel/JSON imports can use source field names or visible Turkish labels.
    reverse_labels = {v: k for k, v in FIELD_LABELS.items()}
    df = df.rename(columns={c: reverse_labels.get(str(c), str(c)) for c in df.columns})
    missing = [k for k in FIELD_KEYS if k not in df.columns]
    if missing:
        raise ValueError("Tabloda beklenen alanlar eksik: " + ", ".join(missing))
    df = df[FIELD_KEYS].copy()
    for key in ["ATNO", *FACTOR_KEYS, "SAHIP_TOPLAM"]:
        df[key] = df[key].map(to_number)
    df["ATNO"] = df["ATNO"].astype("Int64")
    df["Kaynak"] = filename
    return df


def fetch_html(url: str) -> tuple[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text, url


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Aday Rating"] = sum(
        out[key].fillna(0) * weight
        for key, weight in CANDIDATE_WEIGHTS.items()
    ).round(2)
    out["Rating Farkı"] = (out["Kaynak Rating"] - out["Aday Rating"]).round(2)
    return out


def render_devexpress_grid(df: pd.DataFrame, css: str) -> None:
    columns = [
        ("ATNO", "No"), ("ATADI", "🏇 Atın Adı"), ("SAHIP", "🤵 Sahibi"),
        ("AT_SAHIP", "Sahip<br>At"), ("SAHIP_GENEL", "Genel"),
        ("SAHIP_SEHIR", "Şehir"), ("BINICI_SAHIP", "Sahip<br>Binici"),
        ("ANTRENOR_SAHIP", "Sahip<br>Antrenör"), ("SAHIP_TOPLAM", "Rating"),
    ]
    head = "".join(
        f'<td class="dxgvHeader_BlackGlass">{label}</td>' for _, label in columns
    )
    body_rows = []
    for idx, (_, row) in enumerate(df.iterrows()):
        row_class = "dxgvFocusedRow_BlackGlass" if idx == 0 else (
            "dxgvDataRow_BlackGlass dxgvDataRowAlt_BlackGlass" if idx % 2 else "dxgvDataRow_BlackGlass"
        )
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if pd.isna(value):
                value = "—"
            elif key in {"ATNO", *FACTOR_KEYS, "SAHIP_TOPLAM"} and isinstance(value, (int, float, np.number)):
                value = f"{value:.0f}" if float(value).is_integer() else f"{value:.2f}"
            safe = html.escape(str(value))
            if key == "ATADI":
                cells.append(f'<td class="istatistik-adi dxgv">{safe}</td>')
            elif key == "SAHIP":
                cells.append(f'<td class="istatistik-adi dxgv owner-cell">{safe}</td>')
            elif key == "SAHIP_TOPLAM":
                cells.append(f'<td class="rating-cell dxgv"><span>{safe}</span></td>')
            else:
                cells.append(f'<td class="dxgv dx-ac">{safe}</td>')
        body_rows.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')

    table_html = f"""
    <html><head><meta charset="utf-8"><style>
    {css}
    html,body{{margin:0;padding:0;background:#0d141d;color:#e8edf2;font-family:Arial,sans-serif;}}
    .grid-wrap{{width:100%;overflow-x:auto;border:1px solid #293746;border-radius:7px;}}
    table.dxgvTable_BlackGlass{{width:100%;min-width:920px;border-collapse:collapse;table-layout:fixed;background:#17202a;}}
    .dxgvHeader_BlackGlass{{background:#212121!important;color:#eceff1!important;text-align:center!important;font-weight:800!important;font-size:13px!important;padding:11px 6px!important;border:1px solid #46515b!important;white-space:normal;}}
    .dxgv{{padding:10px 6px!important;text-align:center!important;border:1px solid rgba(0,0,0,.35)!important;color:#e9eef4!important;font-size:14px!important;overflow-wrap:anywhere;}}
    .dxgvDataRow_BlackGlass{{background:#182431!important;}}
    .dxgvDataRowAlt_BlackGlass{{background:#1e2b38!important;}}
    .dxgvFocusedRow_BlackGlass{{background:#26394b!important;}}
    .istatistik-adi{{background:rgba(144,164,174,.25)!important;color:#f1f5f9!important;font-weight:700!important;text-align:left!important;}}
    .owner-cell{{font-weight:800!important;}}
    .rating-cell{{background:#17202a!important;color:#ffc107!important;font-weight:900!important;font-size:19px!important;text-shadow:1px 1px #000;}}
    .rating-cell span{{color:#ffc107!important;}}
    .dxgvTable_BlackGlass tr:hover td{{filter:brightness(1.16);}}
    @media(max-width:700px){{.dxgv{{font-size:12px!important;padding:8px 4px!important;}}}}
    </style></head><body>
    <div class="grid-wrap"><table class="dxgvTable_BlackGlass"><thead><tr>{head}</tr></thead>
    <tbody>{''.join(body_rows)}</tbody></table></div></body></html>
    """
    components.html(table_html, height=min(620, 90 + 48 * max(len(df), 1)), scrolling=True)


def estimate_weights(df: pd.DataFrame) -> dict[str, Any] | None:
    valid = df[FACTOR_KEYS + ["SAHIP_TOPLAM"]].dropna()
    if len(valid) < len(FACTOR_KEYS) + 1:
        return None
    x = valid[FACTOR_KEYS].to_numpy(dtype=float)
    y = valid["SAHIP_TOPLAM"].to_numpy(dtype=float)
    if np.linalg.matrix_rank(x) < len(FACTOR_KEYS):
        return None
    weights, *_ = np.linalg.lstsq(x, y, rcond=None)
    predicted = x @ weights
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {
        "weights": dict(zip(FACTOR_KEYS, weights.tolist())),
        "r2": r2,
        "rows": len(valid),
        "rmse": float(np.sqrt(np.mean((y - predicted) ** 2))),
        "actual": y,
        "predicted": predicted,
        "index": valid.index,
    }


# ------------------------------ PAGE -----------------------------------------
css_text = load_css()
if not css_text:
    st.warning("assets/devexpress.css bulunamadı. Uygulama çalışır; DevExpress görünümü yüklenmez.")

st.markdown(
    """
    <style>
    .stApp{background:#0d141d;color:#e8edf2;}
    [data-testid="stSidebar"]{background:#121c27;}
    h1,h2,h3{color:#f4f7fa!important;}
    div[data-testid="stMetric"]{background:#172635;border:1px solid #2a3b4d;padding:12px;border-radius:8px;}
    div[data-testid="stMetricValue"]{color:#ffc107!important;}
    .equest-subtitle{color:#aab7c4;font-size:13px;margin-top:-8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏇 EQUEST · SAHİP İSTATİSTİKLERİ")
st.markdown('<div class="equest-subtitle">DevExpress görünümü · Sahip/at performans tablosu · Rating katsayı incelemesi</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Veri Kaynağı")
    st.caption("Equest sayfasından kaydedilmiş HTML/TXT response dosyası yükleyebilir veya doğrudan erişilebilen bir URL deneyebilirsiniz.")
    source_url = st.text_input("Equest sayfa / response URL", placeholder="https://.../AtYarisi/...")
    fetch_button = st.button("URL'den veriyi getir", use_container_width=True)
    st.divider()
    uploads = st.file_uploader(
        "Response / veri dosyaları",
        type=["html", "htm", "txt", "aspx", "csv", "xlsx", "xls", "json"],
        accept_multiple_files=True,
        help="gridIstatistikSahip tablosunu içeren HTML/TXT response desteklenir.",
    )
    st.caption("CSS dosyası: assets/devexpress.css")

if "equest_df" not in st.session_state:
    st.session_state.equest_df = None
if "equest_source" not in st.session_state:
    st.session_state.equest_source = ""

if fetch_button:
    if not source_url.strip():
        st.error("Önce tam URL girin.")
    else:
        try:
            with st.spinner("Equest URL'si okunuyor..."):
                page, source = fetch_html(source_url.strip())
                parsed = parse_equest_html(page, source)
            st.session_state.equest_df = parsed
            st.session_state.equest_source = source
            st.success(f"{len(parsed)} satır alındı.")
        except Exception as exc:
            st.error(f"URL okunamadı: {exc}")
            st.info(
                "Equest grid'i DevExpress callback ile çalışıyorsa yalnızca callback adresine GET atmak yeterli olmayabilir. "
                "İlk sayfa oturumu ve callback POST verisi gerekir. Tarayıcı Network/Response bölümünden kaydettiğiniz HTML/TXT response dosyasını yükleyebilirsiniz."
            )

if uploads:
    loaded_frames = []
    errors = []
    for file in uploads:
        try:
            loaded_frames.append(parse_uploaded_file(file))
        except Exception as exc:
            errors.append(f"{file.name}: {exc}")
    if loaded_frames:
        combined = pd.concat(loaded_frames, ignore_index=True)
        # Keep each file's rows but remove exact duplicates from repeated uploads.
        combined = combined.drop_duplicates(subset=FIELD_KEYS, keep="last").reset_index(drop=True)
        st.session_state.equest_df = combined
        st.session_state.equest_source = ", ".join(f.name for f in uploads)
        st.success(f"{len(combined)} satır yüklendi.")
    for error in errors:
        st.error(error)

df_raw = st.session_state.equest_df
if df_raw is None or df_raw.empty:
    st.info("Başlamak için sol taraftan Equest Sahip İstatistikleri HTML/TXT response dosyasını yükleyin veya tam URL girin.")
    st.markdown("**Beklenen kaynak alanları:** `ATNO`, `ATADI`, `SAHIP`, `AT_SAHIP`, `SAHIP_GENEL`, `SAHIP_SEHIR`, `BINICI_SAHIP`, `ANTRENOR_SAHIP`, `SAHIP_TOPLAM`.")
    st.markdown("**Önemli:** CSS yalnızca görünümü sağlar. At ve sahip puanları HTML/response içindeki gerçek sayısal alanlardan okunur; olmayan veri üretilmez.")
    st.stop()

df = add_scores(df_raw)

# Summary cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("At sayısı", f"{len(df):,}")
c2.metric("Sahip sayısı", f"{df['SAHIP'].nunique():,}")
c3.metric("En yüksek kaynak rating", f"{df['SAHIP_TOPLAM'].max():.0f}" if df["SAHIP_TOPLAM"].notna().any() else "—")
c4.metric("Ortalama kaynak rating", f"{df['SAHIP_TOPLAM'].mean():.2f}" if df["SAHIP_TOPLAM"].notna().any() else "—")

# Filters
f1, f2, f3 = st.columns([1.2, 1.2, 1])
with f1:
    owner_query = st.text_input("Sahip ara", placeholder="Sahip adı")
with f2:
    horse_query = st.text_input("At ara", placeholder="At adı")
with f3:
    sort_choice = st.selectbox("Sıralama", ["Kaynak Rating yüksekten düşüğe", "Sahip-At yüksekten düşüğe", "At adına göre", "Kaynak sırası"])

view = df.copy()
if owner_query:
    view = view[view["SAHIP"].astype(str).str.contains(owner_query, case=False, na=False)]
if horse_query:
    view = view[view["ATADI"].astype(str).str.contains(horse_query, case=False, na=False)]
if sort_choice == "Kaynak Rating yüksekten düşüğe":
    view = view.sort_values("SAHIP_TOPLAM", ascending=False, na_position="last")
elif sort_choice == "Sahip-At yüksekten düşüğe":
    view = view.sort_values("AT_SAHIP", ascending=False, na_position="last")
elif sort_choice == "At adına göre":
    view = view.sort_values("ATADI", key=lambda s: s.astype(str).str.casefold())

st.subheader("Sahip istatistik tablosu")
st.caption(f"Kaynak: {st.session_state.equest_source or 'Yüklenen response'} · Görüntülenen satır: {len(view)}")
render_devexpress_grid(view, css_text)

with st.expander("Ayrıntılı veri tablosu / dışa aktarım", expanded=False):
    display = view[["ATNO", "ATADI", "SAHIP", *FACTOR_KEYS, "SAHIP_TOPLAM", "Aday Rating", "Rating Farkı"]].copy()
    display = display.rename(columns={**FIELD_LABELS, "Aday Rating": "Aday Rating", "Rating Farkı": "Rating Farkı"})
    st.dataframe(display, use_container_width=True, hide_index=True)
    csv_bytes = display.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSV indir", csv_bytes, file_name="equest_sahip_istatistikleri.csv", mime="text/csv")

st.subheader("Rating katsayı incelemesi")
st.write("Kaynak response içindeki `SAHIP_TOPLAM` alanı Equest'in gösterdiği rating değeridir. Aşağıdaki regresyon, aynı response satırlarındaki beş bileşen ile kaynak rating arasındaki ilişkiyi tahmin eder.")
fit = estimate_weights(df)
if fit is None:
    st.warning(f"Katsayı tahmini için en az {len(FACTOR_KEYS) + 1} tam satır ve bağımsız değişken çeşitliliği gerekiyor. Şu an yeterli veri yok.")
else:
    w1, w2, w3 = st.columns(3)
    w1.metric("Veri satırı", str(fit["rows"]))
    w2.metric("Regresyon R²", f"{fit['r2']:.5f}")
    w3.metric("Tahmin RMSE", f"{fit['rmse']:.3f}")
    weight_rows = []
    for key in FACTOR_KEYS:
        estimate = fit["weights"][key]
        candidate = CANDIDATE_WEIGHTS[key]
        weight_rows.append({
            "Bileşen": FACTOR_LABELS[key],
            "Veriden tahmin edilen katsayı": round(estimate, 5),
            "Test hipotezi katsayısı": candidate,
            "Fark": round(estimate - candidate, 5),
        })
    st.dataframe(pd.DataFrame(weight_rows), use_container_width=True, hide_index=True)

    compare = df.loc[fit["index"], ["ATADI", "SAHIP", "SAHIP_TOPLAM"]].copy()
    compare["Regresyon tahmini"] = fit["predicted"].round(2)
    compare["Test formülü"] = sum(
        df.loc[fit["index"], key].fillna(0) * CANDIDATE_WEIGHTS[key]
        for key in FACTOR_KEYS
    ).round(2)
    compare["Kaynak - test"] = (compare["SAHIP_TOPLAM"] - compare["Test formülü"]).round(2)
    compare = compare.rename(columns={"ATADI": "At", "SAHIP": "Sahip", "SAHIP_TOPLAM": "Kaynak Rating"})
    st.dataframe(compare, use_container_width=True, hide_index=True)

    st.markdown(
        "**İncelenen test formülü:** "
        "Sahip-At × 0,80 + Genel × 0,85 + Şehir × 0,45 + "
        "Binici-Sahip × 0,40 + Antrenör-Sahip × 0,60."
    )
    st.caption(
        "Bu katsayılar yüklediğiniz örnek satırlara çok yakın sonuç veren bir hipotezdir; tek response görüntüsüyle "
        "Equest'in sunucu tarafındaki kesin formülü kanıtlanmış olmaz. Farklı at/koşu ve tarihlerden ek response'lar "
        "yüklenerek katsayıların kararlılığı test edilmelidir."
    )

st.divider()
st.caption("Equest HTML/response verisi üzerinden çalışır. CSS görünümü sağlar; DevExpress'in sunucu tarafı callback mekanizmasını veya erişim yetkisini taklit etmez.")
