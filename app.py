from pathlib import Path
import base64
import re
import streamlit as st
import pandas as pd
from fetch import get_dashboard_data, get_tjk_race_program, get_tjk_horse_history
from bizim_skor_model import calculate_bizim_ranking

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


/* Yarış Programı: Yarış Analizi ana tablosuyla aynı yoğunluk ve tipografi */
.race-program-scroll{{overflow-x:auto!important;overflow-y:auto!important;max-width:100%!important}}
.race-program-table{{width:100%!important;min-width:1320px!important;table-layout:fixed!important;border-collapse:collapse!important;background:#f1f1ef!important;color:#111!important;font-size:11px!important;font-weight:900!important;text-transform:uppercase!important}}
.race-program-table th{{background:#30343b!important;color:#fff!important;font-size:10px!important;font-weight:900!important;padding:7px 4px!important;text-align:left!important;border-right:1px solid #59616a!important;white-space:nowrap!important}}
.race-program-table td{{padding:4px 4px!important;border-bottom:1px solid #c9cdd2!important;color:#111!important;font-size:11px!important;font-weight:900!important;line-height:1.08!important;overflow-wrap:anywhere!important;vertical-align:middle!important}}
.race-program-table tbody tr{{height:39px!important;min-height:39px!important}}
.race-program-table td.rp-eid-cell{{white-space:nowrap!important;overflow:visible!important}}
.race-program-table .rp-eid-value{{display:inline-block;position:relative;color:#d40000!important;font-weight:900!important;cursor:help!important;border-bottom:1px dotted #d40000!important}}
.race-program-table .rp-extra-weight,.race-program-table .rp-st-marker{{color:#d40000!important;font-size:9px!important;font-weight:900!important;white-space:nowrap!important}}

.race-program-table tbody tr:nth-child(odd) td{{background:#e7e7e5!important}}
.race-program-table tbody tr:nth-child(even) td{{background:#f7f7f5!important}}
.race-program-table tbody tr:hover td{{background:#dceaf4!important}}
.race-program-table tbody td:nth-child(1){{text-align:center!important;color:#111!important}}
.race-program-table .rp-horse-name{{color:#071b69!important;font-size:12px!important;font-weight:900!important}}
.race-program-table .rp-horse-no{{color:#16833b!important;font-size:11px!important;font-weight:900!important}}
.race-program-table .rp-equipment{{color:#d00000!important;font-size:9px!important;font-weight:900!important;white-space:nowrap!important}}
.race-program-table .rp-origin-sire{{color:#005bb3!important;font-weight:900!important}}
.race-program-table .rp-origin-dam{{color:#c00018!important;font-size:9px!important;font-weight:900!important}}
.race-program-table .rp-jockey{{color:#029456!important;font-weight:900!important}}
.race-program-table .rp-owner{{color:#005bb3!important;font-weight:900!important}}
.race-program-table .rp-trainer{{color:#c00018!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(4){{color:#005bb3!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(6){{color:#029456!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(7){{color:#005bb3!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(10){{color:#111!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(11){{color:#f07800!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(13){{color:#e00016!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(14){{color:#0795a5!important;font-weight:900!important}}
.race-program-table tbody td:nth-child(15){{color:#029456!important;font-weight:900!important}}

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
    from fetch import get_tjk_active_cities as _get_tjk_active_cities, get_tjk_program as _get_tjk_program

    hero(True)
    f1, f2 = st.columns([1.1, 1.2], gap="small")
    with f1:
        with st.container(border=True):
            selected_date = st.date_input(
                "Tarih", value=pd.Timestamp.today().date(),
                format="DD.MM.YYYY", key="tjk_program_date"
            )

    @st.cache_data(ttl=300, show_spinner=False)
    def _cached_tjk_active_cities(date_iso):
        return _get_tjk_active_cities(date_iso)

    try:
        tracks = _cached_tjk_active_cities(selected_date.isoformat())
    except Exception as exc:
        st.error(f"TJK hipodrom listesi alınamadı: {exc}")
        st.stop()

    if not tracks:
        st.warning(f"{selected_date.strftime('%d.%m.%Y')} tarihinde TJK tarafından doğrulanan yarışlı hipodrom bulunamadı.")
        st.stop()

    previous_track = st.session_state.get("tjk_selected_track")
    default_track = previous_track if previous_track in tracks else tracks[0]
    if st.session_state.get("tjk_track_select") not in tracks:
        st.session_state["tjk_track_select"] = default_track
    with f2:
        with st.container(border=True):
            track = st.selectbox(
                "Hipodrom", tracks,
                index=tracks.index(default_track),
                key="tjk_track_select"
            )

    _tjk_context_changed = st.session_state.get("_tjk_program_context") != (selected_date.isoformat(), track)
    if _tjk_context_changed:
        st.session_state["_tjk_program_context"] = (selected_date.isoformat(), track)
        st.session_state["race_no"] = 1
    st.session_state["tjk_selected_track"] = track

    @st.cache_data(ttl=300, show_spinner=False)
    def _cached_tjk_program(date_iso, city):
        return _get_tjk_program(date_iso, city)

    # Tarih/hipodrom değiştiğinde önceki seçimin bellekte kalmış programını kullanma.
    if _tjk_context_changed:
        _cached_tjk_program.clear()

    with st.spinner(f"TJK {track} programı doğrulanıyor..."):
        try:
            tjk_data = _cached_tjk_program(selected_date.isoformat(), track)
            if not isinstance(tjk_data, dict):
                raise RuntimeError("TJK geçerli program verisi döndürmedi.")
            if str(tjk_data.get("date") or "") != selected_date.isoformat():
                raise RuntimeError("TJK yanıtındaki tarih seçilen tarihle uyuşmuyor.")
            if str(tjk_data.get("city") or "").strip().casefold() != track.strip().casefold():
                raise RuntimeError("TJK yanıtındaki hipodrom seçilen hipodromla uyuşmuyor.")
        except Exception as exc:
            st.error(f"Seçilen tarih/hipodrom için TJK programı doğrulanamadı: {exc}")
            st.stop()

    races = tjk_data.get("races", [])
    races = sorted(
        [r for r in races if isinstance(r, dict)],
        key=lambda r: int(r.get("no") or r.get("race_number") or 999)
    )

    def _program_surface(race_obj):
        """Pist bilgisini TJK yanıtındaki farklı alanlardan güvenli biçimde bul."""
        if not isinstance(race_obj, dict):
            return ""
        # TJK farklı hipodromlarda pist bilgisini farklı alanlarda/nested meta içinde döndürebiliyor.
        # Koşu düzeyindeki tüm metin alanlarını tara; at geçmişi/horses alanına girme.
        candidates = []
        def _collect_race_text(obj, depth=0):
            if depth > 4:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if str(k).casefold() in {"horses", "atlar", "horse_list", "entries"}:
                        continue
                    if isinstance(v, (dict, list, tuple)):
                        _collect_race_text(v, depth + 1)
                    elif v is not None:
                        candidates.append(str(v))
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    _collect_race_text(v, depth + 1)
        _collect_race_text(race_obj)
        value = " ".join(candidates).casefold()
        # Önce sentetik kontrol edilir; bazı TJK metinlerinde 'kum' da birlikte geçebilir.
        if "sentetik" in value:
            return "sentetik"
        if "çim" in value or "cim" in value:
            return "çim"
        if "kum" in value:
            return "kum"
        return ""

    def _program_surface_colors(surface_value):
        key = str(surface_value or "").casefold()
        if "sentetik" in key:
            return "#F2D34F", "#241D08"  # parlak sarı, koyu yazı
        if "kum" in key:
            return "#E87516", "#FFFFFF"  # turuncu, beyaz yazı
        if "çim" in key or "cim" in key or "turf" in key:
            return "#238B45", "#FFFFFF"  # çim/turf: yeşil, beyaz yazı
        return "#35415e", "#ffffff"

    with st.container(border=True):
        x, y = st.columns([1, 1.7])
        with x:
            title("▦", "Günün Yarış Programı", f"({track})")
        with y:
            if races:
                times = [r.get("time") for r in races if r.get("time")]
                first_time = times[0] if times else "—"
                last_time = times[-1] if times else "—"
                st.markdown(
                    f'<div style="text-align:right;font-size:12px;padding-top:5px">'
                    f'🏇　{track}　 ⚑　{len(races)} Koşu　 ◷　İlk Koşu: {first_time}　 🏁　Son Koşu: {last_time}</div>',
                    unsafe_allow_html=True
                )
        if races:
            race_cols = st.columns(len(races), gap="small")
            selected = st.session_state.get("race_no", 1)
            for idx, col in enumerate(race_cols):
                race_item = races[idx]
                race_no = int(race_item.get("no") or race_item.get("race_number") or idx + 1)
                with col:
                    race_surface = _program_surface(race_item)
                    button_color, button_text = _program_surface_colors(race_surface)
                    race_button_key = f"tjk_race_{selected_date:%Y%m%d}_{track}_{race_no}"
                    race_button_wrap = f"race_btn_wrap_{selected_date:%Y%m%d}_{idx}"
                    st.markdown(
                        f'<style>'
                        f'div.st-key-{race_button_wrap} button, '
                        f'div.st-key-{race_button_wrap} button[kind="secondary"]{{'
                        f'background:{button_color}!important;'
                        f'background-color:{button_color}!important;'
                        f'color:{button_text}!important;'
                        f'border:1px solid {button_color}!important;'
                        f'font-weight:800!important;box-shadow:none!important;'
                        f'}}'
                        f'div.st-key-{race_button_wrap} button p{{color:{button_text}!important;}}'
                        f'</style>', unsafe_allow_html=True
                    )
                    with st.container(key=race_button_wrap):
                        if st.button(
                            f'{race_no}. Koşu',
                            key=race_button_key,
                            use_container_width=True,
                            type="secondary"
                        ):
                            st.session_state.race_no = race_no
                            st.rerun()
        else:
            st.info(f"{track} için seçilen tarihte koşu bilgisi bulunamadı.")

    selected = st.session_state.get("race_no", 1)
    race = next(
        (r for r in races if int(r.get("no") or r.get("race_number") or 0) == int(selected)),
        None
    )

    if race is None:
        st.info("Seçilen hipodromda bu koşu bulunmuyor.")
    else:
        horses = race.get("horses", []) if isinstance(race.get("horses"), list) else []
        meta = race.get("meta", {}) if isinstance(race.get("meta"), dict) else {}
        distance = race.get("distance") or meta.get("distance") or "—"
        surface = _program_surface(race) or race.get("surface") or meta.get("surface") or "—"
        race_name = race.get("name") or race.get("condition") or meta.get("raceName") or f"{selected}. KOŞU"

        with st.container(border=True):
            import html as _race_html
            selected_race_item = next(
                (item for item in races
                 if int(item.get("no") or item.get("race_number") or 0) == int(selected)),
                {}
            )
            race_class_text = str(
                race.get("class") or race.get("condition") or meta.get("class") or
                race.get("race_class") or race.get("raceClass") or race.get("race_type") or
                race.get("raceType") or race.get("type") or meta.get("raceClass") or
                meta.get("race_type") or selected_race_item.get("class") or
                selected_race_item.get("condition") or selected_race_item.get("race_class") or
                selected_race_item.get("raceClass") or selected_race_item.get("race_type") or
                selected_race_item.get("raceType") or selected_race_item.get("type") or ""
            ).strip()
            race_details = str(race.get("details") or "").strip()
            surface_key = str(surface or "").casefold()
            # Aynı pist renkleri hem yatay koşu düğmelerinde hem bilgi bandında kullanılır.
            race_color, race_text_color = _program_surface_colors(surface_key)
            if race_color == "#35415e":
                race_color, race_text_color = "#1769aa", "#ffffff"

            # Tek ve dolu bir başlık bandı: boş kolonlar kaldırıldı.
            age_text = str(race.get("age", meta.get("age", "")) or "").strip()
            distance_text = str(distance or "").strip()
            race_name_text = str(race_name or "").strip()
            if not race_class_text and race_name_text:
                race_class_text = race_name_text
            race_time_text = str(race.get("time") or race.get("start_time") or meta.get("time") or meta.get("startTime") or race.get("startTime") or "").strip()
            # Başlık sırası: koşu numarası + saat + koşu şartı; ardından ad ve pist detayları.
            # Saat, TJK verisindeki farklı olası alan adlarından alınır.
            race_time_text = str(
                race.get("time") or race.get("start_time") or race.get("startTime") or
                meta.get("time") or meta.get("start_time") or meta.get("startTime") or
                selected_race_item.get("time") or selected_race_item.get("start_time") or
                selected_race_item.get("startTime") or ""
            ).strip()
            race_no_text = f"{selected}. KOŞU"
            name_is_class = (
                race_name_text.casefold() == race_class_text.casefold()
                if race_class_text else False
            )
            name_is_only_race_number = bool(re.fullmatch(
                r"\\s*\\d+\\s*\\.?\\s*koşu\\s*", race_name_text, flags=re.I
            ))
            title_parts = [race_no_text, race_time_text, race_class_text,
                           "" if (name_is_class or name_is_only_race_number) else race_name_text,
                           age_text, str(race.get("weight") or "").strip(),
                           distance_text, str(surface or "").strip()]
            header_text = " · ".join(x for x in title_parts if x and x != "—")
            prize_text = str(race.get("prize") or "").strip()
            st.markdown(
                f'<div style="background:{race_color};color:{race_text_color};'
                f'border-radius:8px;padding:12px 16px;font-weight:800;'
                f'display:flex;justify-content:space-between;align-items:center;gap:16px">'
                f'<span style="flex:1">{_race_html.escape(header_text)}</span>'
                f'<span style="white-space:nowrap;font-size:12px">{len(horses)} AT</span></div>',
                unsafe_allow_html=True
            )
            if race_details or prize_text:
                details_text = race_details or f"İkramiye: {prize_text}"
                st.markdown(
                    f'<div style="margin-top:6px;padding:9px 12px;'
                    f'border-left:4px solid {race_color};background:rgba(245,238,215,.98);'
                    f'color:#243126;border-radius:5px;font-size:11px;line-height:1.55;'
                    f'font-weight:700;white-space:normal">'
                    f'{_race_html.escape(details_text)}</div>',
                    unsafe_allow_html=True
                )

            tab = st.radio(
                "Koşu detayları",
                ["Koşu Bilgisi", "Galoplar", "Sabit Oranlar", "Muhtemel Ganyan", "Geçmiş Koşular"],
                horizontal=True, label_visibility="collapsed",
                key=f"race_detail_{selected_date:%Y%m%d}_{track}_{selected}"
            )

            if tab == "Koşu Bilgisi":
                import html as _html
                import re as _re

                def _format_program_weight(value):
                    raw = str(value or "").strip()
                    if not raw:
                        return ""
                    # TJK kilo alanındaki baz kilo ve fazla kilo bilgisini ayır.
                    m = _re.search(r"(?P<base>\d+(?:[.,]\d+)?)\s*(?:KG|KİLO|KILO)?\s*(?P<extra>[+]\s*\d+(?:[.,]\d+)?)?", raw, flags=_re.I)
                    if not m:
                        return raw
                    base = m.group("base").replace(".", ",")
                    extra = (m.group("extra") or "").replace(" ", "").replace(".", ",")
                    return f"{base}KG" + (f" {extra}" if extra else "")

                def _format_program_st(value):
                    raw = str(value or "").strip()
                    if not raw:
                        return ""
                    # TJK'nın gerçek start işaretini koru; DS/TS değerini kendimiz üretme.
                    number = _re.search(r"\d+", raw)
                    marker = _re.search(r"\b(DS|TS)\b", raw, flags=_re.I)
                    if number and marker:
                        return f"{number.group(0)} {marker.group(1).upper()}"
                    return number.group(0) if number else raw

                def _format_program_eid(value):
                    raw = str(value or "").strip()
                    if not raw:
                        return "", ""
                    # bestTime bazı yanıtlarda derece + açıklamayı tek alanda döndürüyor.
                    m = _re.search(r"(?<!\d)(\d{1,2}\.\d{2}\.\d{2})(?!\d)", raw)
                    if m:
                        degree = m.group(1)
                        remainder = (raw[:m.start()] + raw[m.end():]).strip(" \t\r\n-–|;:")
                        return degree, remainder
                    return raw, ""

                def _split_program_horse_name(horse):
                    raw = str(horse.get("name") or horse.get("at_ismi") or "").strip()
                    nonrunner = bool(horse.get("nonRunner") or horse.get("Koşmaz") or horse.get("koşmaz") or _re.search(r"\(\s*ko[sş]maz\s*\)", raw, flags=_re.I))
                    raw = _re.sub(r"\s*\(\s*ko[sş]maz\s*\)", "", raw, flags=_re.I)
                    raw = _re.sub(r"\s*Image.*$", "", raw, flags=_re.I)
                    # TJK At İsmi hücresindeki parantezli numara gerçek at numarasıdır.
                    # no/numara alanı bazı kaynaklarda yalnızca satır sırasını verir.
                    nm = _re.search(r"\((\d{1,2})\)", raw)
                    number = nm.group(1) if nm else str(
                        horse.get("horseNumber") or horse.get("horse_no") or
                        horse.get("programNo") or horse.get("numara") or horse.get("no") or ""
                    ).strip()
                    equipment = str(horse.get("equipment") or horse.get("taki") or "").strip()
                    if not equipment:
                        tokens = _re.findall(r"(?i)\b(?:SKG|GKR|SGK|DB|KG|SK|K|G|D|B|H|TT|M)\b", raw)
                        equipment = " ".join(x.upper() for x in tokens[:6])
                    clean_name = _re.sub(r"\s*\(\d{1,2}\)", "", raw)
                    clean_name = _re.sub(
                        r"(?i)\s*(?:SKG|GKR|SGK|DB|KG|SK|K|G|D|B|H|TT|M)(?:\s+(?:SKG|GKR|SGK|DB|KG|SK|K|G|D|B|H|TT|M))*"
                        r"(?:\s+(?:Ring|Kulaklık|Kulaklik|Kapalı|Kapali|Dilbağı|Dilbagi|Dilinin|Gözlük|Gozluk|Takı|Taki)\b.*)?$",
                        "", clean_name, flags=_re.I
                    ).strip()
                    return clean_name or raw, number, equipment, nonrunner

                display_rows = []
                for i, h in enumerate(horses, 1):
                    horse_name, horse_no, equipment, nonrunner = _split_program_horse_name(h)
                    owner = str(h.get("owner") or h.get("sahip") or "").strip()
                    trainer = str(h.get("trainer") or h.get("antrenor") or "").strip()
                    eid_degree, eid_embedded_info = _format_program_eid(h.get("bestTime") or "")
                    eid_info_parts = [
                        eid_embedded_info,
                        str(h.get("bestInfo") or h.get("best_info") or "").strip(),
                        ("Hipodrom: " + str(h.get("bestCity") or h.get("best_city"))) if (h.get("bestCity") or h.get("best_city")) else "",
                        ("Tarih: " + str(h.get("bestDate") or h.get("best_date"))) if (h.get("bestDate") or h.get("best_date")) else "",
                        ("Mesafe: " + str(h.get("bestDistance") or h.get("best_distance"))) if (h.get("bestDistance") or h.get("best_distance")) else "",
                    ]
                    display_rows.append({
                        "No": horse_no or str(h.get("no") or i),
                        "At İsmi": horse_name,
                        "_horse_form": str(h.get("form") or h.get("last6") or h.get("Son 6 Y.") or "").strip(),
                        "_nonrunner": nonrunner,
                        "_ekuri": bool(h.get("ekuri") or h.get("Eküri") or h.get("eküri")),
                        "Yaş": h.get("age") or h.get("yas") or "",
                        "Orijin (Baba-Anne)": h.get("origin") or h.get("orijin") or "",
                        "Kilo": _format_program_weight(h.get("weight") or h.get("siklet") or ""),
                        "Jokey": h.get("jockey") or h.get("jokey") or "",
                        "Sahip / Antrenör": "",
                        "_owner": owner,
                        "_trainer": trainer,
                        "St": _format_program_st(h.get("st") or ""),
                        "HP": h.get("hp") or "",
                        "Son 6 Y.": h.get("form") or h.get("last6") or "",
                        "KGS": h.get("kgs") or "",
                        "S20": h.get("s20") or h.get("S20") or h.get("son20") or h.get("Son 20") or "",
                        "EİD": eid_degree,
                        "_eid_info": "\n".join(x for x in eid_info_parts if x),
                        "Gny": h.get("odds") or "",
                        "AGF": h.get("agf") or "",
                        "_equipment": equipment,
                    })

                headers = ["No", "At İsmi", "Yaş", "Orijin (Baba-Anne)", "Kilo", "Jokey",
                           "Sahip / Antrenör", "St", "HP", "Son 6 Y.", "KGS", "S20", "EİD", "Gny", "AGF"]
                widths = [4, 17, 7, 15, 5, 9, 12, 4, 4, 10, 4, 4, 7, 6, 6]
                total_width = sum(widths)
                colgroup = "".join(
                    f'<col style="width:{w/total_width*100:.2f}%">' for w in widths
                )
                html_rows = []
                for row in display_rows:
                    cells = []
                    for key in headers:
                        value = str(row.get(key, "") or "—")
                        safe = _html.escape(value)
                        if key == "At İsmi":
                            number = _html.escape(str(row.get("No", "")))
                            gear = _html.escape(str(row.get("_equipment", "")))
                            nonrunner_tag = ' <span style="color:#d40000!important;font-size:9px!important;font-weight:900!important">KOŞMAZ</span>' if row.get("_nonrunner") else ""
                            ekuri_tag = ' <span title="Eküri" style="color:#d40000!important;font-size:11px!important;font-weight:900!important">♞</span>' if row.get("_ekuri") else ""
                            form_value = _html.escape(str(row.get("_horse_form", "") or "").strip())
                            form_tag = (
                                f' <span style="color:#075b32!important;font-size:10px!important;font-weight:900!important">'
                                f'<span style="color:#1683d8!important"> (</span>{form_value}'
                                f'<span style="color:#1683d8!important">)</span></span>'
                            ) if form_value else ""
                            safe = (
                                f'<span class="rp-horse-name">{safe}</span> '
                                f'<span class="rp-horse-no">({number})</span>'
                                f'{form_tag}{ekuri_tag}{nonrunner_tag} '
                                f'<span class="rp-equipment">{gear}</span>'
                            )
                        elif key == "Orijin (Baba-Anne)":
                            parts = [x.strip() for x in value.split("/", 1)]
                            sire = _html.escape(parts[0] if parts else value)
                            dam = _html.escape(parts[1] if len(parts) > 1 else "")
                            safe = f'<span class="rp-origin-sire">{sire}</span>'
                            if dam:
                                safe += f'<br><span class="rp-origin-dam">{dam}</span>'
                        elif key == "Kilo":
                            km = _re.search(r"(\d+(?:[.,]\d+)?)\s*KG\s*([+]\s*\d+(?:[.,]\d+)?)?", value, flags=_re.I)
                            if km:
                                base = _html.escape(km.group(1) + "KG")
                                extra_value = _re.sub(r"\s+", "", km.group(2) or "")
                                extra = f' <span class="rp-extra-weight" style="color:#d40000!important;font-size:9px!important;font-weight:900!important">{_html.escape(extra_value)}</span>' if extra_value else ""
                                safe = base + extra
                        elif key == "St":
                            sm = _re.search(r"(\d+)\s*(DS|TS)\b", value, flags=_re.I)
                            if sm:
                                safe = f'{_html.escape(sm.group(1))} <span class="rp-st-marker" style="color:#d40000!important;font-size:9px!important;font-weight:900!important">{_html.escape(sm.group(2).upper())}</span>'
                        elif key == "Jokey":
                            safe = f'<span class="rp-jockey">{safe}</span>'
                        elif key == "Sahip / Antrenör":
                            owner = _html.escape(str(row.get("_owner", "")))
                            trainer = _html.escape(str(row.get("_trainer", "")))
                            safe = f'<span class="rp-owner">{owner}</span>'
                            if trainer:
                                safe += f'<br><span class="rp-trainer">{trainer}</span>'
                        elif key == "Son 6 Y.":
                            safe = _html.escape(value.replace(" ", ""))
                        if key == "EİD":
                            eid_info = str(row.get("_eid_info", "") or "").strip()
                            # Tooltip içeriği güvenli biçimde HTML attribute'a yazılır.
                            tooltip = _html.escape(eid_info, quote=True)
                            safe = f'<span class="rp-eid-value" title="{tooltip}">{safe}</span>'
                            cells.append(f'<td class="rp-eid-cell">{safe}</td>')
                        else:
                            cells.append(f"<td>{safe}</td>")
                    html_rows.append("<tr>" + "".join(cells) + "</tr>")

                table_html = (
                    '<div class="scroll-table race-program-scroll"><table class="data-table race-program-table">'
                    f'<colgroup>{colgroup}</colgroup><thead><tr>'
                    + "".join(f"<th>{_html.escape(h)}</th>" for h in headers)
                    + "</tr></thead><tbody>"
                    + "".join(html_rows)
                    + "</tbody></table></div>"
                )
                st.markdown(table_html, unsafe_allow_html=True)

            elif tab == "Sabit Oranlar":
                table(pd.DataFrame([
                    {"No": h.get("no"), "At Adı": h.get("name"), "Sabit Oran": h.get("fixedOdds") or h.get("fixed_odds") or ""}
                    for h in horses
                ]), 650)
            elif tab == "Muhtemel Ganyan":
                table(pd.DataFrame([
                    {"No": h.get("no"), "At Adı": h.get("name"), "Muhtemel Ganyan": h.get("odds") or ""}
                    for h in horses
                ]), 650)
            elif tab == "Geçmiş Koşular":
                st.info("Geçmiş koşular, seçilen atın Yarış Analizi sayfasındaki TJK geçmiş kayıtlarından görüntülenebilir.")
            else:
                st.info("Galop verileri Yarış Analizi sayfasında TJK at kimliği üzerinden yüklenir.")

elif st.session_state.page == "Yarış Analizi":
    from race_analysis_page import render as render_race_analysis
    render_race_analysis()

else:
    hero()
    with st.container(border=True): st.info(f"{st.session_state.page} sayfası sonraki geliştirme aşamasında hazırlanacaktır.")
