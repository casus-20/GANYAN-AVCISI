from pathlib import Path
import base64
import re
import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetch import get_dashboard_data, get_tjk_race_program, get_tjk_horse_history
from bizim_skor_model import calculate_bizim_ranking
from reyting_model import calculate_rating_cached

BASE = Path(__file__).parent

def image_b64(name):
    p = BASE / "assets" / name
    try:
        return base64.b64encode(p.read_bytes()).decode("ascii")
    except Exception:
        return ""

MAIN_BANNER = image_b64("main_banner.jpg")
PROGRAM_BANNER = image_b64("program_banner.jpg")
st.set_page_config(page_title="GANYAN AVCISI", page_icon="🐎", layout="wide", initial_sidebar_state="expanded")

st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{{--bg:#080e1b;--panel:#111d31;--line:#29425e;--purple:#005BB3;--blue:#005BB3;--ice:#B2DAE4;--pink:#D8226C;--orange:#F86A38;--green:#029456;--text:#f5f8ff}}
html,body,[class*="css"]{{font-family:Inter,sans-serif}}
.stApp{{background:radial-gradient(ellipse at 48% 0%,#17152e 0%,#0b1020 52%,#080d1b 100%);color:var(--text)}}
[data-testid="stHeader"]{{background:transparent}}
.block-container{{padding:.25rem 1rem 1.1rem;max-width:1900px}}
section[data-testid="stSidebar"]{{background:linear-gradient(180deg,#171b31,#101528);border-right:1px solid #262d48;width:167px!important;min-width:167px!important;max-width:167px!important;flex:0 0 167px!important;}}
section[data-testid="stSidebar"]>div{{width:167px!important;min-width:167px!important;padding:.75rem .48rem}}
/* Kenar menüsü sabit: aç/kapat ve daraltma kontrolleri gizli */
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], button[kind="header"]{{display:none!important;visibility:hidden!important}}
section[data-testid="stSidebar"]{{transform:none!important;visibility:visible!important}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{{gap:.48rem!important}}
section[data-testid="stSidebar"] .stButton>button{{width:100%;min-height:34px!important;padding:5px 6px!important;border-radius:8px!important;background:#252d49!important;border:1px solid #3b4568!important;color:#f4f4fb!important;font-size:11.5px!important;font-weight:600!important;white-space:normal!important;line-height:1.18!important;box-shadow:0 2px 6px #0002}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(100deg,#7138ef,#8e4dff)!important;border-color:#a27aff!important}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:#343d61!important;border-color:#9a70ff!important}}
.brand{{text-align:center;padding:7px 4px 22px;color:white;font-size:19px;font-weight:800;line-height:1.2}}
.brand .horse{{display:block;font-size:44px;line-height:1.2;margin-bottom:6px}}
.hero{{min-height:126px;border-radius:0 0 14px 14px;padding:14px 24px;margin:0 0 10px;background:linear-gradient(90deg,rgba(12,15,31,.98),rgba(12,15,31,.88) 40%,rgba(12,15,31,.08)),url('data:image/jpeg;base64,{MAIN_BANNER}') right center/cover no-repeat;border-bottom:1px solid #252c48;display:flex;flex-direction:column;justify-content:center}}
.hero.program{{background-image:linear-gradient(90deg,rgba(12,15,31,.98),rgba(12,15,31,.84) 42%,rgba(12,15,31,.05)),url('data:image/jpeg;base64,{PROGRAM_BANNER}')}}
.hero h1{{font-size:clamp(26px,2.4vw,39px);margin:0;font-weight:800;letter-spacing:-.8px;color:#f8f7ff}}
.hero h1 .accent{{color:#B2DAE4}}.hero p{{margin:5px 0 0;color:#e2e4f0;font-size:15px;max-width:650px}}
[data-testid="stVerticalBlockBorderWrapper"]{{background:linear-gradient(145deg,#171d32f2,#11172af5);border:1px solid #303754!important;border-radius:14px!important;padding:9px 10px!important;box-shadow:0 6px 18px #0002}}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"]{{gap:.42rem}}
.panel-title{{font-size:16px;font-weight:750;margin:0 0 7px;color:#f4f3fb}}
.panel-title .ico{{color:#a15cff;margin-right:8px}}
.data-table{{width:100%;max-width:100%;table-layout:fixed;border-collapse:collapse;color:#18212d;font-size:12px;font-weight:800;white-space:normal;text-transform:uppercase}}
.data-table th{{background:#30343b;color:#f7f8fa;font-weight:900;padding:7px 5px;text-align:left;position:sticky;top:0;z-index:1;text-transform:uppercase;overflow-wrap:anywhere}}
.data-table td{{border-bottom:1px solid #c9cdd2;padding:6px 5px;color:#17212b;font-weight:900;overflow-wrap:anywhere;word-break:normal;line-height:1.15}}
.data-table tr:nth-child(even) td{{background:#e7e8e8}}
.data-table tr:nth-child(odd) td{{background:#f7f7f5}}
.data-table tr:hover td{{background:#dceaf4;color:#17212b}}
.featured-table-wrap{{border:2px solid #062b55;border-radius:10px;padding:3px;box-shadow:0 0 0 1px #fff7,0 5px 14px #0005;overflow:auto}}
.featured-table{{border:0!important;border-collapse:separate!important;border-spacing:0!important}}
.featured-table th{{background:#005BB3!important;color:#fff!important;font-size:11px!important;font-weight:900!important;text-transform:uppercase!important;border-bottom:2px solid #062b55!important;padding:6px 4px!important;overflow-wrap:normal!important;word-break:normal!important}}
.featured-table td{{color:#ffffff!important;font-weight:900!important;font-size:13px!important;text-transform:uppercase!important;border-bottom:1px solid #ffffff!important;padding:9px 6px!important}}
.featured-table tbody tr:nth-child(odd) td{{background:#555b64!important}}
.featured-table tbody tr:nth-child(even) td{{background:#3b414a!important}}
.featured-pill{{display:inline-block;min-width:36px;padding:3px 7px;border-radius:999px;font-size:12px;line-height:1.15;font-weight:900;text-align:center;white-space:nowrap;box-shadow:inset 0 0 0 1px #ffffff55}}
.featured-pill.agf{{background:#029456;color:#07150f}}
.featured-pill.ganyan{{background:#D8226C;color:#fff}}
.agf-summary-wrap{{border:1px solid #263d5b;border-radius:9px;padding:2px;overflow:auto}}
.agf-summary-table th{{background:#005BB3!important;color:#fff!important;font-size:13px!important;font-weight:900!important;padding:8px 6px!important}}
.agf-summary-table td{{font-size:13px!important;font-weight:900!important;padding:8px 6px!important;color:#ffffff!important}}
.agf-summary-table tbody tr:nth-child(odd) td{{background:#555b64!important}}
.agf-summary-table tbody tr:nth-child(even) td{{background:#3b414a!important}}
.agf-summary-table tbody tr td:nth-child(2){{color:#ffffff!important;font-weight:900!important}}
/* Üç ana tabloda at adları: lacivert elips + dikkat çekici mavi ışıklı çerçeve */
.horse-name-pill{{display:inline-flex!important;align-items:center!important;justify-content:center!important;
  max-width:100%!important;min-width:0!important;box-sizing:border-box!important;
  padding:4px 10px!important;border-radius:999px!important;background:#071b3a!important;
  color:#ff5a6e!important;font-weight:900!important;text-align:center!important;
  line-height:1.15!important;white-space:normal!important;overflow-wrap:break-word!important;
  border:2px solid #00cfff!important;
  box-shadow:0 0 4px #00d9ff,0 0 9px #00aaff,0 0 15px #007bff66,inset 0 0 5px #00cfff55!important}}
.featured-table tbody td:nth-child(2),.agf-summary-table tbody td:nth-child(2),
.race-results-table tbody td:nth-child(3){{text-align:center!important}}
.agf-summary-table tbody tr:hover td{{background:inherit!important}}
.agf-summary-table .featured-pill.agf{{background:#029456!important;color:#fff!important;font-size:14px!important;padding:4px 11px!important;min-width:48px}}
.race-results-table{{table-layout:fixed!important;width:100%!important}}
.race-results-table th{{background:#005BB3!important;color:#fff!important;font-weight:900!important;font-size:16px!important}}
.race-results-table td{{font-size:16px!important;font-weight:900!important;color:#fff!important;padding:8px 6px!important}}
.race-results-table tbody tr:nth-child(odd) td{{background:#555b64!important}}
.race-results-table tbody tr:nth-child(even) td{{background:#3b414a!important}}
.race-results-table td:nth-child(3){{font-size:16px!important;font-weight:900!important;letter-spacing:0!important;white-space:normal!important}}
.race-results-table .featured-pill{{font-size:16px!important}}
.race-results-table .result-ganyan{{display:inline-block;background:#D8226C;color:#fff;padding:3px 5px;border-radius:999px;font-size:10px;font-weight:900;white-space:nowrap}}
.race-results-table .result-agf{{display:inline-block;background:#fff;color:#005BB3;padding:3px 5px;border-radius:999px;font-size:10px;font-weight:900;white-space:nowrap}}


/* Yarış Programı - referans görseldeki açık gri/pembe tablo görünümü */
.race-program-table{{width:100%!important;min-width:0!important;table-layout:fixed!important;border-collapse:collapse!important;background:#f1f1ef!important;color:#111!important;font-size:10px!important;font-weight:900!important;text-transform:uppercase!important}}
.race-program-table th{{background:#30343b!important;color:#fff!important;font-size:9px!important;font-weight:900!important;padding:6px 4px!important;text-align:left!important;border-right:1px solid #59616a!important;white-space:nowrap!important}}
.race-program-table td{{padding:7px 5px!important;border-bottom:1px solid #c9cdd2!important;color:#111!important;font-size:10px!important;font-weight:900!important;line-height:1.18!important;overflow-wrap:anywhere!important;vertical-align:middle!important}}
.race-program-table tbody tr:nth-child(odd) td{{background:#e7e7e5!important}}
.race-program-table tbody tr:nth-child(even) td{{background:#f4dedd!important}}
.race-program-table tbody tr:hover td{{background:#dceaf4!important}}
.race-program-table tbody td:nth-child(1){{text-align:center!important;color:#111!important}}
.race-program-table tbody td:nth-child(2){{color:#c00018!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(4){{color:#005bb3!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(6){{color:#029456!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(7),.race-program-table tbody td:nth-child(8){{color:#005bb3!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(10){{color:#e00016!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(12){{color:#f07800!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(13){{color:#e00016!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(15){{color:#0795a5!important;font-weight:900!important}}
.race-program-table .scroll-table{{overflow-x:auto!important;overflow-y:auto!important}}

.data-table td:nth-child(2){{color:#c00018;font-weight:900}}
.data-table td:nth-child(4){{color:#005BB3;font-weight:900}}
.data-table td:nth-child(6),.data-table td:nth-child(7),.data-table td:nth-child(8){{color:#029456;font-weight:900}}
.scroll-table{{overflow:auto;max-width:100%;width:100%;border-radius:9px;scrollbar-color:#005BB3 #171c30;scrollbar-width:thin}}
.race-results-no-scroll{{overflow-x:hidden!important;overflow-y:visible!important;max-height:none!important;height:auto!important}}
.race-results-no-scroll .race-results-table{{height:auto!important}}
.scroll-table table{{width:100%!important;min-width:0!important;max-width:100%!important;table-layout:fixed!important;box-sizing:border-box}}
.scroll-table th,.scroll-table td{{box-sizing:border-box;max-width:0}}
.panel-title .ico{{color:#B2DAE4}}
.result-box{{border:1px solid #005BB3;border-radius:10px;padding:9px;background:#005BB322;margin-top:8px;font-size:12px;color:#B2DAE4;font-weight:800}}
.city-card{{border-color:#005BB366}}
.city-card{{background:linear-gradient(145deg,#242a45,#171d32);border:1px solid #333b5b;border-radius:12px;padding:9px;min-height:178px}}
.city-name{{font-size:13px;font-weight:750}}.city-temp{{font-size:23px;font-weight:800;margin-top:2px}}
.city-meta{{display:flex;justify-content:space-between;border-top:1px solid #343b55;padding-top:5px;margin-top:5px;font-size:11px;color:#d7daea}}
.result-box{{border:1px solid #8755ef;border-radius:10px;padding:9px;background:#241b45;margin-top:8px;font-size:12px}}
.small-muted{{color:#b9bfd4;font-size:11px}}
.stButton>button{{border-radius:9px;border:1px solid #4b5477;background:#202640;color:#fff;min-height:37px;font-size:13px}}
.stButton>button:hover{{border-color:#a36aff;color:white;background:#34245d}}
.stButton>button[kind="primary"]{{background:linear-gradient(100deg,#7138ef,#8e4dff);border-color:#9a70ff}}
div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label{{color:#e9eaf5!important}}
div[data-testid="stSelectbox"]>div>div,div[data-testid="stDateInput"] input{{background:#202640}}
/* Tarih ve hipodrom kontrolleri yaklaşık %40 daha kısa */
div[data-testid="stDateInput"] input{{height:25px!important;min-height:25px!important;padding-top:0!important;padding-bottom:0!important;font-size:12px!important}}
div[data-testid="stSelectbox"] [data-baseweb="select"]{{min-height:25px!important;height:25px!important;font-size:12px!important}}
div[data-testid="stSelectbox"] [data-baseweb="select"]>div{{min-height:25px!important;height:25px!important}}
div[data-testid="stDateInput"] label,div[data-testid="stSelectbox"] label{{font-size:11px!important;margin-bottom:0!important}}
div[data-testid="stRadio"] label{{color:#f5f5fb}}
[data-testid="stDataFrame"]{{border:1px solid #303754;border-radius:8px}}
@media(max-width:1100px){{.block-container{{padding-left:.6rem;padding-right:.6rem}}.data-table{{font-size:11px}}}}
@media(max-width:700px){{.hero{{padding:12px;min-height:100px;background-position:72% center}}.hero p{{max-width:72%;font-size:11px}}[data-testid="stVerticalBlockBorderWrapper"]{{padding:7px!important}}}}

/* Yalnızca Yarış Sonuçları tablosunun dar sağ paneldeki ölçü düzeltmesi */
.race-results-table {{ table-layout:fixed!important; width:100%!important; min-width:100%!important; }}
.race-results-table th {{ font-size:9px!important; line-height:1.1!important; padding:5px 2px!important; white-space:nowrap!important; overflow:hidden!important; text-overflow:clip!important; word-break:keep-all!important; overflow-wrap:normal!important; }}
.race-results-table td {{ font-size:10px!important; line-height:1.15!important; padding:5px 2px!important; white-space:nowrap!important; overflow:hidden!important; text-overflow:clip!important; }}
.race-results-table td:nth-child(3) {{ white-space:normal!important; overflow-wrap:break-word!important; }}
.race-results-table .featured-pill {{ font-size:9px!important; min-width:0!important; padding:3px 4px!important; }}
.race-results-table th:nth-child(1),.race-results-table td:nth-child(1) {{ white-space:nowrap!important; }}
.race-results-table th:nth-child(2),.race-results-table td:nth-child(2) {{ white-space:nowrap!important; }}
.race-results-table th:nth-child(6),.race-results-table td:nth-child(6) {{ white-space:nowrap!important; }}

/* Ana sayfa işaretli alanların kolon sınırları */
[data-testid="stHorizontalBlock"]{{align-items:stretch!important;min-width:0!important}}
[data-testid="stHorizontalBlock"]>div{{min-width:0!important;max-width:100%!important}}
[data-testid="stVerticalBlockBorderWrapper"]{{min-width:0!important;max-width:100%!important;overflow:hidden}}
.scroll-table{{min-width:0!important}}

/* Gerçek ekran genişliğine göre tabloları sıkıştır: başlık ve hücre taşmasını engelle */
.data-table {{ width:100%!important; max-width:100%!important; table-layout:fixed!important; }}
.data-table th {{ font-size:10px!important; line-height:1.15!important; padding:5px 3px!important;
  white-space:nowrap!important; overflow-wrap:normal!important; word-break:keep-all!important; }}
.data-table td {{ font-size:11px!important; line-height:1.2!important; padding:5px 4px!important;
  overflow-wrap:normal!important; word-break:normal!important; }}
.scroll-table {{ width:100%!important; max-width:100%!important; overflow-x:hidden!important; }}
.scroll-table table {{ width:100%!important; min-width:100%!important; max-width:100%!important;
  table-layout:fixed!important; }}
.scroll-table th,.scroll-table td {{ max-width:none!important; min-width:0!important; box-sizing:border-box!important; }}
.race-results-table th {{ font-size:10px!important; white-space:nowrap!important; padding:5px 2px!important; }}
.race-results-table td {{ font-size:11px!important; padding:5px 3px!important; white-space:nowrap!important; }}
.race-results-table td:nth-child(3) {{ font-size:11px!important; white-space:normal!important; overflow-wrap:anywhere!important; }}
.race-results-table .featured-pill {{ font-size:10px!important; min-width:0!important; padding:3px 5px!important; }}
.featured-table th {{ font-size:9px!important; padding:5px 2px!important; }}
.featured-table td {{ font-size:11px!important; padding:6px 4px!important; }}
.featured-table .featured-pill {{ font-size:10px!important; padding:3px 5px!important; }}
.agf-summary-table th,.agf-summary-table td {{ font-size:11px!important; padding:6px 4px!important; }}
.agf-summary-table .featured-pill.agf {{ font-size:11px!important; padding:3px 7px!important; min-width:0!important; }}
@media(max-width:1400px) {{
  .panel-title {{ font-size:14px!important; }}
  .race-results-table th {{ font-size:9px!important; }}
  .race-results-table td {{ font-size:10px!important; }}
  .featured-table th {{ font-size:8.5px!important; }}
  .featured-table td {{ font-size:10px!important; }}
}}
</style>''', unsafe_allow_html=True)

def title(icon, text, extra=""):
    st.markdown(f'<div class="panel-title"><span class="ico">{icon}</span>{text} <span class="small-muted">{extra}</span></div>', unsafe_allow_html=True)

def table(df, height=300):
    if df is None or len(df) == 0:
        st.caption("Gösterilecek kayıt bulunamadı.")
        return
    # Kolon bazlı genişlikler: dar sıra/no, geniş at adı ve orijin.
    width_map = {
        "No": 5, "Sıra": 8, "At No": 6, "At İsmi": 18, "At Adı": 18,
        "Yaş": 7, "Yaş / Cins": 8, "Yaş/Cins": 8,
        "Orijin (Baba - Anne)": 17, "Orijin (Baba-Anne)": 17,
        "Kilo": 6, "Sıklet": 6, "Jokey": 10, "Sahip": 11,
        "Antrenör": 10, "Sahip / Antrenör": 14, "St.": 5, "HP": 5,
        "Son 6 Y.": 10, "Son 6 Koşu": 20, "K / G / Y": 12, "KGS": 5, "s20": 5, "EİD": 7,
        "Sabit Oran": 7, "Muhtemel Ganyan": 20, "AGF Oranı": 9, "AGF": 11,
        "Ayak": 12, "Koşu": 13, "Kazanan At / Ganyan / AGF": 48,
        "Bitiş Derecesi": 18, "B. Derece": 18,
    }
    widths = [width_map.get(str(c), max(7, 80 // max(1, len(df.columns)))) for c in df.columns]
    total = sum(widths)
    colgroup = "<colgroup>" + "".join(f'<col style="width:{w/total*100:.2f}%">' for w in widths) + "</colgroup>"
    view = df.copy()
    # Ekrandaki bütün tablo metinleri büyük harf; oran ve derece değerleri korunur.
    view = view.applymap(lambda v: str(v).upper() if isinstance(v, str) else v)
    # Sonuç tablosunda uzun başlığı kısa göster; veri kaynağındaki anahtar değişmez.
    if "Bitiş Derecesi" in view.columns and {"Ayak", "Koşu", "At Adı", "Ganyan", "AGF"}.issubset(set(map(str, view.columns))):
        view = view.rename(columns={"Bitiş Derecesi": "B. Derece"})
    columns_set = set(map(str, view.columns))
    is_featured = {"Son 6 Koşu", "Koşu", "AGF", "Muhtemel Ganyan"}.issubset(columns_set)
    is_agf_summary = {"Sıra", "At Adı", "AGF Oranı"}.issubset(columns_set)
    is_race_results = {"Ayak", "Koşu", "At Adı", "Ganyan", "AGF", "B. Derece"}.issubset(columns_set)
    is_race_program = {"At Adı", "Yaş / Cins", "Jokey", "HP", "KGS"}.issubset(columns_set)
    if is_race_program:
        race_widths = {"Sıra":5, "At Adı":19, "Yaş / Cins":7, "Orijin (Baba - Anne)":17,
                       "Orijin (Baba-Anne)":17, "Sıklet":6, "Kilo":6, "Jokey":10,
                       "Sahip":11, "Antrenör":10, "St.":5, "HP":5, "Son 6 Y.":10,
                       "KGS":5, "EİD":7, "Sabit Oran":7, "Muhtemel Ganyan":8}
        widths = [race_widths.get(str(c), 7) for c in view.columns]
        total = sum(widths)
        colgroup = "<colgroup>" + "".join(f'<col style="width:{w/total*100:.2f}%">' for w in widths) + "</colgroup>"
    if is_race_results:
        # Önceki ölçülere göre: At Adı %15 daraltıldı, AGF %5 daraltıldı,
        # B. Derece alanı genişletildi. Ayak ve Koşu sütunları korunur.
        # Sağ panel dar olduğundan sütunları kullanılabilir alana göre paylaştır.
        # AYAK/KOŞU/B.DERECE başlıkları tek satırda kalır; AT ADI alanı yeterli genişlikte.
        result_widths = {"Ayak": 11, "Koşu": 12, "At Adı": 29,
                         "Ganyan": 11, "AGF": 11, "B. Derece": 26}
        widths = [result_widths.get(str(c), 10) for c in view.columns]
        total = sum(widths)
        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{w/total*100:.2f}%">' for w in widths
        ) + "</colgroup>"
    table_class = "data-table race-results-table" if is_race_results else ("data-table race-program-table" if is_race_program else ("data-table featured-table" if is_featured else ("data-table agf-summary-table" if is_agf_summary else "data-table")))
    html = view.to_html(index=False, escape=True, border=0, classes=table_class)
    if is_featured or is_agf_summary or is_race_results:
        # Yalnızca oran değerlerini rozetle vurgula; satır zeminleri korunur.
        headers = list(map(str, view.columns))
        agf_idx = headers.index("AGF") if "AGF" in headers else (headers.index("AGF Oranı") if "AGF Oranı" in headers else None)
        odds_idx = headers.index("Ganyan") if is_race_results else (headers.index("Muhtemel Ganyan") if "Muhtemel Ganyan" in headers else None)
        def badge_row(match):
            cells = re.findall(r"<td>(.*?)</td>", match.group(0), flags=re.S)
            rebuilt = match.group(0)
            badge_targets = []
            if agf_idx is not None:
                badge_targets.append((agf_idx, "result-agf" if is_race_results else "agf"))
            if odds_idx is not None:
                badge_targets.append((odds_idx, "ganyan"))
            name_idx = headers.index("At Adı") if "At Adı" in headers else None
            if name_idx is not None:
                badge_targets.append((name_idx, "horse-name-pill"))
            for idx, cls in badge_targets:
                if idx < len(cells):
                    value = cells[idx]
                    replacement = f'<td><span class="featured-pill {cls}">{value}</span></td>'
                    rebuilt = rebuilt.replace(f"<td>{value}</td>", replacement, 1)
            return rebuilt
        html = re.sub(r"<tr>.*?</tr>", badge_row, html, flags=re.S)
    html = html.replace(">", ">" + colgroup, 1)
    if is_featured:
        st.markdown(f'<div class="featured-table-wrap"><div class="scroll-table" style="max-height:{height}px">{html}</div></div>', unsafe_allow_html=True)
    elif is_agf_summary:
        st.markdown(f'<div class="agf-summary-wrap"><div class="scroll-table" style="max-height:{height}px">{html}</div></div>', unsafe_allow_html=True)
    elif is_race_results:
        st.markdown(f'<div class="scroll-table race-results-no-scroll">{html}</div>', unsafe_allow_html=True)
    elif is_race_program:
        st.markdown(f'<div class="scroll-table" style="max-height:{height}px">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="scroll-table" style="max-height:{height}px">{html}</div>', unsafe_allow_html=True)

def hero(program=False):
    cls = "hero program" if program else "hero"
    heading = '▦ Yarış Programı' if program else '<span class="accent">GANYAN</span> AVCISI'
    subtitle = "Günün, yaklaşan günlerin ve seçilen hipodromların yarış programı" if program else "Atlar, jokeyler, antrenörler ve pist performansları için kapsamlı analiz ve istatistikler"
    st.markdown(f'<div class="{cls}"><h1>{heading}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><span class="horse">♞</span>GANYAN<br>AVCISI</div>', unsafe_allow_html=True)
    pages = ["Ana Sayfa","Yarış Programı","Yarış Analizi","Yarış Sonuçları","At İstatistikleri","Jokey İstatistikleri","Antrenör İstatistikleri","Pist & Mesafe Analizi","Tahmin / Model","Hakkında"]
    icons = ["⌂","▦","▥","🏆","▤","♟","♞","◉","✣","ⓘ"]
    if "page" not in st.session_state: st.session_state.page = "Ana Sayfa"
    for p, ic in zip(pages, icons):
        if st.button(f"{ic}  {p}", key=f"nav_{p}", use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()
    st.markdown('<div style="color:#aab1ca;font-size:12px;margin:28px 8px 4px">◉　GitHub</div><div style="color:#aab1ca;font-size:10px;margin:8px">🔻 Streamlit ile hazırlanmıştır</div>', unsafe_allow_html=True)

if st.session_state.page == "Ana Sayfa":
    hero()
    d = get_dashboard_data()

    # Sol üst Yarış Sonuçları, sağ üst Hava ve Pist; AGF orta kolonda korunur.
    left_col, center_col, right_col = st.columns([1.15, 0.82, 1.00], gap="small")

    with left_col:
        with st.container(border=True):
            title("🏆", "Yarış Sonuçları")
            choice = st.radio(
                "Altılı türü", ["1. Altılı", "2. Altılı"],
                horizontal=True, label_visibility="collapsed"
            )
            result = d["results"][choice]
            st.markdown(
                f'<div class="small-muted" style="font-weight:900;color:#B2DAE4;margin:2px 0 6px">'
                f'ŞEHİR / HİPODROM: {result.get("city", "İSTANBUL")}</div>',
                unsafe_allow_html=True
            )
            result_rows = []
            for leg in result["legs"]:
                result_rows.append({
                    "Ayak": leg.get("Ayak", ""),
                    "Koşu": leg.get("Koşu", ""),
                    "At Adı": leg.get("Kazanan At", ""),
                    "Ganyan": leg.get("Ganyan", "-"),
                    "AGF": leg.get("AGF", "-"),
                    "Bitiş Derecesi": leg.get("Bitiş Derecesi", "")
                })
            table(pd.DataFrame(result_rows), None)
            st.markdown(
                f'<div class="result-box"><b>{choice.upper()} SONUCU:</b> {result["sequence"]}'
                f'<br><b>İKRAMİYE: {result["payout"]}</b>　|　'
                f'<b>BİLEN KİŞİ: {result["winners"]}</b></div>',
                unsafe_allow_html=True
            )

        with st.container(border=True):
            title("♞", "Öne Çıkan Atlar ve Muhtemel Ganyan", "(En fazla 15 at)")
            featured_df = pd.DataFrame(d["featured"]).rename(columns={"K / G / Y": "Koşu"})
            # AGF sütununu kaynak verideki AGF / AGF Oranı alanından garanti et.
            if "AGF" not in featured_df.columns:
                if "AGF Oranı" in featured_df.columns:
                    featured_df["AGF"] = featured_df["AGF Oranı"]
                else:
                    agf_source = pd.DataFrame(d.get("agf", []))
                    if {"At Adı", "AGF Oranı"}.issubset(agf_source.columns) and "At Adı" in featured_df.columns:
                        agf_map = agf_source.set_index("At Adı")["AGF Oranı"]
                        featured_df["AGF"] = featured_df["At Adı"].map(agf_map).fillna("-")
                    else:
                        featured_df["AGF"] = "-"
            featured_columns = ["Sıra", "At Adı", "Son 6 Koşu", "Koşu", "AGF", "Muhtemel Ganyan"]
            for column in featured_columns:
                if column not in featured_df.columns:
                    featured_df[column] = "-"
            featured_df = featured_df[featured_columns]
            table(featured_df, 285)

    with center_col:
        with st.container(border=True):
            title("▥", "AGF Oranları", "(Günün Öne Çıkan Koşusu)")
            table(pd.DataFrame(d["agf"][:20]), 620)

    with right_col:
        with st.container(border=True):
            title("◉", "Hava ve Pist Bilgileri", "(En fazla 3 şehir)")
            city_names = [x["city"] for x in d["weather"]]
            selected_cities = st.multiselect(
                "Şehir seç", city_names, default=city_names[:3],
                max_selections=3, label_visibility="collapsed",
                key="weather_cities"
            )
            chosen = [x for x in d["weather"] if x["city"] in selected_cities]
            city_cols = st.columns(max(1, len(chosen)), gap="small")
            for col, city in zip(city_cols, chosen):
                with col:
                    st.markdown(f"""<div class="city-card">
                        <div class="city-name">📍 {city["city"]}</div>
                        <div style="font-size:25px">{city["icon"]}</div>
                        <div class="city-temp">{city["temp"]}°C</div>
                        <div class="small-muted">{city["condition"]}</div>
                        <div class="city-meta"><span>Rüzgâr</span><b>{city["wind"]}</b></div>
                        <div class="city-meta"><span>Nem</span><b>{city["humidity"]}</b></div>
                        <div class="city-meta"><span>Pist</span><b>{city["track"]}</b></div>
                        <div class="city-meta"><span>Pist Durumu</span><b>{city["track_state"]}</b></div>
                        </div>""", unsafe_allow_html=True)

        with st.container(border=True):
            title("♧", "Kazanma Olasılığı Tahmini", "(Örnek Model)")
            for x in d["probabilities"]:
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:112px 1fr 45px;gap:7px;'
                    f'align-items:center;margin:13px 0;font-size:12px">'
                    f'<span>{x["horse"]}</span>'
                    f'<div style="height:18px;border-radius:5px;background:#292e48;overflow:hidden">'
                    f'<div style="height:100%;width:{x["prob"]}%;'
                    f'background:linear-gradient(90deg,#005BB3,#B2DAE4)"></div></div>'
                    f'<b>%{str(x["prob"]).replace(".",",")}</b></div>',
                    unsafe_allow_html=True
                )

    with st.container(border=True):
        title("▦", "Yarış Programı", "(Yaklaşan Koşular)")
        table(pd.DataFrame(d["program"]), 210)

elif st.session_state.page == "Yarış Programı":
    hero(True)
    f1,f2=st.columns([1.1,1.2],gap="small")
    with f1:
        with st.container(border=True):
            selected_date=st.date_input("Tarih",value=pd.Timestamp.today().date(),format="DD.MM.YYYY",key="tjk_program_date")
    @st.cache_data(ttl=300, show_spinner=False)
    def _cached_tjk_program(date_text):
        return get_tjk_race_program(date_text)

    with st.spinner("Seçilen tarihin TJK yarış programı yükleniyor..."):
        try:
            tjk_data = _cached_tjk_program(selected_date.strftime("%d/%m/%Y"))
        except Exception as exc:
            st.error("TJK yarış programı alınamadı. Biraz sonra tekrar deneyin.")
            st.caption(f"Bağlantı ayrıntısı: {type(exc).__name__}: {exc}")
            st.stop()

    tracks = tjk_data.get("tracks", [])
    if not tracks:
        st.warning(f"{selected_date.strftime('%d.%m.%Y')} tarihinde TJK günlük programında hipodrom bulunamadı.")
        st.stop()

    track_options = tracks
    previous_track = st.session_state.get("tjk_selected_track")
    default_track = previous_track if previous_track in track_options else tracks[0]
    if st.session_state.get("tjk_track_select") not in track_options:
        st.session_state["tjk_track_select"] = default_track
    with f2:
        with st.container(border=True):
            track=st.selectbox("Hipodrom",track_options,index=track_options.index(default_track),key="tjk_track_select")
    selected_track = track
    if st.session_state.get("_tjk_program_context") != (selected_date.isoformat(), selected_track):
        st.session_state["_tjk_program_context"] = (selected_date.isoformat(), selected_track)
        st.session_state["race_no"] = 1
    st.session_state["tjk_selected_track"] = track

    races = tjk_data.get("races_by_track", {}).get(selected_track, [])
    with st.container(border=True):
        x,y=st.columns([1,1.7])
        with x: title("▦","Günün Yarış Programı",f"({track})")
        with y:
            if races:
                times = [r.get("time") for r in races if r.get("time")]
                first_time = times[0] if times else "—"
                last_time = times[-1] if times else "—"
                st.markdown(f'<div style="text-align:right;font-size:12px;padding-top:5px">🏇　{selected_track}　 ⚑　{len(races)} Koşu　 ◷　İlk Koşu: {first_time}　 🏁　Son Koşu: {last_time}</div>',unsafe_allow_html=True)
        if races:
            selected=st.session_state.get("race_no",1)
            race_cols=st.columns(len(races),gap="small")
            for idx,col in enumerate(race_cols):
                r=races[idx]
                n=r["no"]
                with col:
                    if st.button(f'{n}. Koşu\n{r.get("time","")}',key=f"tjk_race_{selected_date:%Y%m%d}_{selected_track}_{n}",use_container_width=True,type="primary" if selected==n else "secondary"):
                        st.session_state.race_no=n
                        st.rerun()
        else:
            st.info(f"{selected_track} için seçilen tarihte koşu bilgisi bulunamadı.")

    selected=st.session_state.get("race_no",1)
    race=next((v for v in races if v["no"]==selected),None)
    if race is None:
        st.info("Seçilen hipodromda bu koşu bulunmuyor.")
    else:
        detail = tjk_data.get("details", {}).get(f"{selected_track}|{selected}", {})
        horses = detail.get("horses", [])
        with st.container(border=True):
            p1,p2,p3,p4=st.columns([.55,1,1.7,1.6])
            with p1: st.markdown(f'<div style="background:#005BB3;border-radius:10px;text-align:center;padding:12px 4px;font-weight:800">{race["no"]}. Koşu</div>',unsafe_allow_html=True)
            with p2: st.markdown(f'<b>{selected_track}</b><br><span class="small-muted">Hipodromu</span>',unsafe_allow_html=True)
            with p3: st.markdown(f'<b>{race.get("name") or str(race["no"])+". KOŞU"}</b><br><span class="small-muted">{race.get("class","")} / {race.get("age","")} / {race.get("distance","")} ({race.get("surface","")})</span>',unsafe_allow_html=True)
            with p4: st.markdown(f'<div style="font-size:12px;text-align:right">◷ {race.get("time") or "—"}<br>Koşan At: {race.get("runners",len(horses))}<br>Ödül: {race.get("prize") or "—"}</div>',unsafe_allow_html=True)
            tab=st.radio("Koşu detayları",["Koşu Bilgisi","Galoplar","Sabit Oranlar","Muhtemel Ganyan","Geçmiş Koşular"],horizontal=True,label_visibility="collapsed",key=f"race_detail_{selected_date:%Y%m%d}_{selected_track}_{selected}")
            if tab=="Koşu Bilgisi": table(pd.DataFrame(horses),650)
            elif tab=="Sabit Oranlar": table(pd.DataFrame(detail.get("fixed_odds",[])),650)
            elif tab=="Muhtemel Ganyan": table(pd.DataFrame(detail.get("probable_odds",[])),650)
            elif tab=="Geçmiş Koşular": table(pd.DataFrame(detail.get("past_runs",[])),650)
            else: table(pd.DataFrame(detail.get("gallops",[])),650)

elif st.session_state.page == "Yarış Analizi":
    hero(True)
    st.markdown("### 🧠 YARIŞ ANALİZ MERKEZİ")
    st.caption("TJK resmi programı ve at geçmişleri doğrudan TJK kaynaklarından alınır. Worker bağlantısı kullanılmaz.")
    a1, a2 = st.columns([1.1, 1.2], gap="small")
    with a1:
        with st.container(border=True):
            analysis_date = st.date_input("Yarış Tarihi", value=pd.Timestamp.today().date(), format="DD.MM.YYYY", key="analysis_tjk_date")
    @st.cache_data(ttl=300, show_spinner=False)
    def _analysis_program(date_text):
        return get_tjk_race_program(date_text)
    try:
        with st.spinner("TJK resmi yarış programı alınıyor..."):
            pdata = _analysis_program(analysis_date.strftime("%d/%m/%Y"))
    except Exception as exc:
        st.error("TJK yarış programı alınamadı.")
        st.caption(f"{type(exc).__name__}: {exc}")
        st.stop()
    cities = pdata.get("tracks", [])
    if not cities:
        st.warning("Seçilen tarihte TJK programı bulunamadı.")
        st.stop()
    with a2:
        with st.container(border=True):
            city = st.selectbox("Hipodrom", cities, key="analysis_tjk_city")
    races = pdata.get("races_by_track", {}).get(city, [])
    race_labels = {f'{r.get("no")}. Koşu  ·  {r.get("time") or "Saat yok"}  ·  {r.get("distance", "")} {r.get("surface", "")}': r for r in races}
    if not race_labels:
        st.info("Bu hipodrom için koşu bulunamadı.")
        st.stop()
    selected_label = st.selectbox("Analiz edilecek koşu", list(race_labels), key="analysis_tjk_race")
    selected_race = dict(race_labels[selected_label])
    race_no = selected_race.get("no")
    detail = pdata.get("details", {}).get(f"{city}|{race_no}", {})
    entries = detail.get("horses", [])
    race_context = {
        "date": analysis_date.isoformat(), "surface": selected_race.get("surface", ""),
        "distance": selected_race.get("distance", ""),
        "condition": selected_race.get("class", ""), "raceName": selected_race.get("name", ""),
        "track": city, "no": race_no,
    }
    st.markdown("#### KOŞU KÜNYESİ")
    with st.container(border=True):
        m1,m2,m3,m4,m5=st.columns(5)
        m1.metric("KOŞU", f"{race_no}. Koşu")
        m2.metric("SAAT", selected_race.get("time") or "—")
        m3.metric("MESAFE", selected_race.get("distance") or "—")
        m4.metric("PİST", selected_race.get("surface") or "—")
        m5.metric("AT SAYISI", len(entries))
        st.caption(f"{city} · {analysis_date:%d.%m.%Y} · {selected_race.get('name') or selected_race.get('class') or 'TJK Yarışı'} · {selected_race.get('age','')}")
    st.markdown("#### TJK RESMİ BÜLTENİ – KATILAN ATLAR")
    table(pd.DataFrame([{k:v for k,v in h.items() if not k.startswith("_")} for h in entries]), 420)

    def _analysis_horse_normalize(raw):
        h=dict(raw)
        h.update({
            "no": h.get("Sıra", ""), "number": h.get("Sıra", ""),
            "name": h.get("At Adı", ""), "at_ismi": h.get("At Adı", ""),
            "age": h.get("Yaş / Cins", ""), "origin": h.get("Orijin (Baba - Anne)", ""),
            "weight": h.get("Sıklet", ""), "siklet": h.get("Sıklet", ""),
            "jockey": h.get("Jokey", ""), "jokey": h.get("Jokey", ""),
            "owner": h.get("Sahip", ""), "trainer": h.get("Antrenör", ""),
            "st": h.get("St.", ""), "hp": h.get("HP", ""),
            "form": h.get("Son 6 Y.", ""), "kgs": h.get("KGS", ""),
            "s20": h.get("s20", ""), "bestTime": h.get("EİD", ""),
            "odds": h.get("Muhtemel Ganyan", ""), "agf": h.get("AGF", ""),
        })
        return h

    def _history_date_before(row, target):
        from datetime import datetime, date
        value=next((row.get(k) for k in ("Tarih","tarih","date","raceDate","race_date") if row.get(k)),None) if isinstance(row,dict) else None
        if isinstance(value,datetime): value=value.date()
        if isinstance(value,date): dt=value
        else:
            dt=None
            for fmt in ("%d.%m.%Y","%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
                try: dt=datetime.strptime(str(value or "")[:10],fmt).date(); break
                except Exception: pass
        return dt is not None and dt < target

    run_key=f"{analysis_date.isoformat()}|{city}|{race_no}"
    if st.button("🔎 TÜM AT GEÇMİŞLERİNİ ÇEK VE TAM ANALİZİ ÇALIŞTIR", type="primary", use_container_width=True, key=f"run_full_tjk_analysis_{run_key}"):
        normalized=[_analysis_horse_normalize(h) for h in entries]
        results=[None]*len(normalized)
        errors=[]
        progress=st.progress(0, text="TJK at geçmişleri alınıyor...")
        def _fetch_one(item):
            i,h=item
            at_id=h.get("_at_id") or h.get("atId") or h.get("at_id") or ""
            try:
                hist=get_tjk_horse_history(str(at_id)) if at_id else []
                return i, hist, "" if hist else ("AtId bulunamadı" if not at_id else "TJK geçmiş tablosu boş döndü")
            except Exception as exc:
                return i, [], f"{type(exc).__name__}: {exc}"
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures=[pool.submit(_fetch_one,item) for item in enumerate(normalized)]
            done=0
            for fut in as_completed(futures):
                i,hist,err=fut.result(); normalized[i]["_history"]=hist
                normalized[i]["_history_source"]="TJK doğrudan" if hist else "TJK doğrudan – veri yok"
                normalized[i]["_workouts"]=[]
                normalized[i]["_enrichment_error"]=err
                if err: errors.append(f'{normalized[i].get("name")}: {err}')
                done+=1; progress.progress(done/max(1,len(normalized)), text=f"{done}/{len(normalized)} at işlendi")
        progress.empty()
        # İki skor motoru da hedef tarihten önceki geçmişle çalışır.
        for h in normalized:
            h["_history"]=[r for r in h.get("_history",[]) if _history_date_before(r, analysis_date)]
        race_context["date"]=analysis_date.isoformat()
        bizim=calculate_bizim_ranking(normalized, race_context)
        rating=calculate_rating_cached(normalized, race_context)
        st.session_state["_full_tjk_analysis_result"]={"key":run_key,"horses":normalized,"bizim":bizim,"rating":rating,"errors":errors,"race":race_context}

    def _history_date_before(row, target):
        from datetime import datetime, date
        value=next((row.get(k) for k in ("Tarih","tarih","date","raceDate","race_date") if row.get(k)),None) if isinstance(row,dict) else None
        if isinstance(value,datetime): value=value.date()
        if isinstance(value,date): dt=value
        else:
            dt=None
            for fmt in ("%d.%m.%Y","%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
                try: dt=datetime.strptime(str(value or "")[:10],fmt).date(); break
                except Exception: pass
        return dt is not None and dt < target

    result=st.session_state.get("_full_tjk_analysis_result")
    if result and result.get("key")==run_key:
        horses=result["horses"]
        bizim_by={x["horse_index"]:x for x in result.get("bizim",[])}
        rating_by={x["horse_index"]:x for x in result.get("rating",[])}
        def _v(x): return x if x not in (None, "") else "—"
        def _money_value(value):
            import re
            raw=str(value or "").replace("₺", "").replace("TL", "").replace("\xa0", " ").strip()
            raw=re.sub(r"[^0-9,.]", "", raw)
            if not raw: return 0.0
            if "," in raw: raw=raw.replace(".", "").replace(",", ".")
            try: return float(raw)
            except Exception: return 0.0
        def _money_text(value):
            return (f"{value:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")) if value else "—"
        rows=[]
        for i,h in enumerate(horses):
            b=bizim_by.get(i,{}) ; rr=rating_by.get(i,{})
            owner_trainer=" / ".join(x for x in (h.get("owner"),h.get("trainer")) if x)
            hist=h.get("_history",[])
            last=hist[0] if hist else {}
            target_year=analysis_date.year
            total_earnings=sum(_money_value(rec.get("İkramiye") or rec.get("Ikramiye") or rec.get("Kazanç")) for rec in hist if isinstance(rec,dict))
            year_earnings=sum(_money_value(rec.get("İkramiye") or rec.get("Ikramiye") or rec.get("Kazanç")) for rec in hist if isinstance(rec,dict) and str(rec.get("Tarih", "")).endswith(str(target_year)))
            last_display=" / ".join(str(last.get(k)) for k in ("Tarih","Mesafe","Pist","Sıra","Derece") if last.get(k)) or "—"
            rows.append({
                "No":_v(h.get("no")),"At İsmi":_v(h.get("name")),"Yaş":_v(h.get("age")),
                "Orijin (Baba-Anne)":_v(h.get("origin")),"Kilo":_v(h.get("weight")),"Jokey":_v(h.get("jockey")),
                "Sahip / Antrenör":owner_trainer or "—","St":_v(h.get("st")),"HP":_v(h.get("hp")),
                "Son 6 Y.":_v(h.get("form")),"KGS":_v(h.get("kgs")),"s20":_v(h.get("s20")),
                "EİD":_v(h.get("bestTime")),"Gny":_v(h.get("odds")),"AGF":_v(h.get("agf")),
                "BİZİM SKOR":b.get("score","—"),"REYTİNG":rr.get("score","—"),
                "SON KOŞU":last_display,"GEÇMİŞ YARIŞ":len(hist),
                "BU YIL KAZANÇ":_money_text(year_earnings),"TOPLAM KAZANÇ":_money_text(total_earnings),
            })
        st.markdown("#### TAM YARIŞ ANALİZ TABLOSU")
        table(pd.DataFrame(rows), 650)
        st.markdown("#### BİZİM SKOR – PERFORMANS SIRALAMASI")
        b_rows=[]
        for x in result.get("bizim",[]):
            h=horses[x["horse_index"]]; row={"Sıra":x.get("rank"),"No":h.get("no"),"At":h.get("name"),"BİZİM SKOR":x.get("score")}
            row.update(x.get("components",{})); b_rows.append(row)
        table(pd.DataFrame(b_rows), 360)
        st.markdown("#### REYTİNG – BAĞIMSIZ PERFORMANS SIRALAMASI")
        r_rows=[]
        for x in result.get("rating",[]):
            h=horses[x["horse_index"]]; row={"Sıra":x.get("rank"),"No":h.get("no"),"At":h.get("name"),"REYTİNG":x.get("score")}
            row.update(x.get("components",{})); row["Kullanılan Bileşen"]=x.get("available_components"); row["Kullanılan Ağırlık %"]=x.get("available_weight_pct"); r_rows.append(row)
        table(pd.DataFrame(r_rows), 360)
        detail_names=[h.get("name") or f"At {i+1}" for i,h in enumerate(horses)]
        selected_horse_name=st.selectbox("At detayını görüntüle", detail_names, key="analysis_detail_horse")
        horse=next((h for h in horses if h.get("name")==selected_horse_name),{})
        st.markdown(f"#### {selected_horse_name.upper()} – GEÇMİŞ YARIŞLAR")
        table(pd.DataFrame(horse.get("_history",[])), 460)
        with st.expander("REYTİNG BİLEŞEN TEŞHİSİ", expanded=False):
            diag=[]
            for i,h in enumerate(horses):
                rr=rating_by.get(i,{}) ; comp=rr.get("components",{})
                diag.append({"At":h.get("name"),"REYTİNG":rr.get("score","HESAPLANMADI"),"Ortak Rakip + Kilo":comp.get("Ortak Rakip + Kilo"),"Kilo Uyumu":comp.get("Kilo Uyumu"),"Güncel Form":comp.get("Güncel Form"),"Pist / Mesafe":comp.get("Pist / Mesafe"),"Sınıf Uyumu":comp.get("Sınıf Uyumu"),"Eksik Bileşen":", ".join(k for k in ("Ortak Rakip + Kilo","Kilo Uyumu","Güncel Form","Pist / Mesafe","Sınıf Uyumu") if comp.get(k) is None) or "Yok"})
            table(pd.DataFrame(diag),360)
        with st.expander("TÜM ATLARIN GEÇMİŞ YARIŞ KAYITLARI", expanded=False):
            all_history=[]
            for h in horses:
                for rec in h.get("_history",[]):
                    row={"At":h.get("name")}; row.update(rec if isinstance(rec,dict) else {"Kayıt":str(rec)}); all_history.append(row)
            table(pd.DataFrame(all_history),520)
        with st.expander("GALOP / İŞ KAYITLARI", expanded=False):
            st.warning("Galop verisi için doğrudan TJK uç noktası bu kaynak dosyalarda doğrulanmadı. Worker kullanılmadı ve galop verisi uydurulmadı.")
        if result.get("errors"):
            with st.expander("TJK VERİ ERİŞİM HATALARI", expanded=False):
                for err in result["errors"]: st.write("• "+err)
        st.caption("REYTİNG motoru: Ortak Rakip + Kilo %35 · Kilo Uyumu %5 · Güncel Form %25 · Pist/Mesafe %15 · Sınıf Uyumu %20. Her iki motor da hedef yarış tarihinden önceki kayıtları kullanır.")
    else:
        st.info("Tüm atların geçmiş yarışlarını, BİZİM SKOR ve REYTİNG tablolarını oluşturmak için yukarıdaki analiz düğmesine basın.")

else:
    hero()
    with st.container(border=True): st.info(f"{st.session_state.page} sayfası sonraki geliştirme aşamasında hazırlanacaktır.")
