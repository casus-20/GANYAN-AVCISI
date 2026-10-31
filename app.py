
from pathlib import Path
import streamlit as st
import pandas as pd
from fetch import get_dashboard_data, get_race_program_data, get_race_detail

BASE = Path(__file__).parent
st.set_page_config(page_title="GANYAN AYCISI", page_icon="🐎", layout="wide", initial_sidebar_state="expanded")

st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#0b1020;--panel:#171d32;--line:#303958;--purple:#7942f4;--text:#f5f5fb}
html,body,[class*="css"]{font-family:Inter,sans-serif}
.stApp{background:linear-gradient(135deg,#0b1020,#090d1b);color:var(--text)}
[data-testid="stHeader"]{background:transparent}
.block-container{padding:.55rem 1rem 1.5rem;max-width:1900px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#171b31,#101528);border-right:1px solid #262d48}
section[data-testid="stSidebar"]>div{padding-top:1rem}
.brand{text-align:center;padding:12px 4px 22px;color:white;font-size:20px;font-weight:800;line-height:1.2}
.brand span{display:block;font-size:43px}
.hero{min-height:112px;border-radius:0 0 14px 14px;padding:16px 24px;margin:0 0 12px;background:linear-gradient(90deg,rgba(12,15,31,.98),rgba(12,15,31,.83) 42%,rgba(12,15,31,.12)),url('assets/main_banner.jpg') right center/cover no-repeat;border-bottom:1px solid #252c48}
.hero.program{background-image:linear-gradient(90deg,rgba(12,15,31,.98),rgba(12,15,31,.82) 42%,rgba(12,15,31,.12)),url('assets/program_banner.jpg')}
.hero h1{font-size:clamp(25px,2.2vw,38px);margin:0;font-weight:800;letter-spacing:-.8px}
.hero h1 span{color:#9860ff}.hero p{margin:5px 0 0;color:#e2e4f0;font-size:14px}
.panel{background:linear-gradient(145deg,#1a1f37,#12172a);border:1px solid #303754;border-radius:14px;padding:12px 13px;box-shadow:0 6px 18px #0002;height:100%}
.panel-title{font-size:16px;font-weight:750;margin:0 0 9px;color:#f4f3fb}
.panel-title .ico{color:#a15cff;margin-right:8px}
.data-table{width:100%;border-collapse:collapse;color:#f2f3fa;font-size:12px;white-space:nowrap}
.data-table th{background:#272d47;color:#f0f1fa;font-weight:650;padding:7px 8px;text-align:left}
.data-table td{border-bottom:1px solid #5d698f40;padding:6px 8px}
.data-table tr:nth-child(even) td{background:#6e49c21c}
.data-table tr:hover td{background:#7849f03d}
.scroll-table{overflow:auto;max-width:100%;border-radius:9px;scrollbar-color:#777aa7 #171c30;scrollbar-width:thin}
.city-card{background:linear-gradient(145deg,#242a45,#171d32);border:1px solid #333b5b;border-radius:12px;padding:9px;min-height:155px}
.city-name{font-size:13px;font-weight:750}.city-temp{font-size:23px;font-weight:800}
.city-meta{display:flex;justify-content:space-between;border-top:1px solid #343b55;padding-top:5px;margin-top:5px;font-size:11px;color:#d7daea}
.result-box{border:1px solid #8755ef;border-radius:10px;padding:9px;background:#241b45;margin-top:9px;font-size:12px}
.stat-line{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid #303752;padding:5px 0;font-size:12px}
.small-muted{color:#b9bfd4;font-size:11px}
.stButton>button{border-radius:9px;border:1px solid #4b5477;background:#202640;color:#fff;min-height:38px}
.stButton>button:hover{border-color:#a36aff;color:white;background:#34245d}
div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label{color:#e9eaf5!important}
div[data-testid="stSelectbox"]>div>div{background:#202640}
@media(max-width:1100px){.block-container{padding-left:.6rem;padding-right:.6rem}.data-table{font-size:11px}}
@media(max-width:700px){.hero{padding:12px;min-height:95px;background-position:70% center}.hero p{max-width:75%;font-size:11px}.panel{padding:9px}}
</style>
''', unsafe_allow_html=True)

def title(icon, text, extra=""):
    st.markdown(f'<div class="panel-title"><span class="ico">{icon}</span>{text} <span class="small-muted">{extra}</span></div>', unsafe_allow_html=True)

def table(df, height=350):
    st.markdown(f'<div class="scroll-table" style="max-height:{height}px">{df.to_html(index=False,escape=True,border=0,classes="data-table")}</div>', unsafe_allow_html=True)

def hero(program=False):
    cls = "hero program" if program else "hero"
    heading = "▦ Yarış Programı" if program else '<span>GANYAN</span> AYCISI'
    subtitle = "Günün, yaklaşan günlerin ve seçilen hipodromların yarış programı" if program else "Atlar, jokeyler, antrenörler ve pist performansları için kapsamlı analiz ve istatistikler"
    st.markdown(f'<div class="{cls}"><h1>{heading}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><span>♞</span>GANYAN<br>AYCISI</div>', unsafe_allow_html=True)
    pages = ["Ana Sayfa","Yarış Programı","Yarış Analizi","Yarış Sonuçları","At İstatistikleri","Jokey İstatistikleri","Antrenör İstatistikleri","Pist & Mesafe Analizi","Tahmin / Model","Hakkında"]
    icons = ["⌂","▦","▥","🏆","▤","♟","♞","◉","✣","ⓘ"]
    if "page" not in st.session_state: st.session_state.page = "Ana Sayfa"
    for p, ic in zip(pages, icons):
        if st.button(f"{ic}  {p}", key=f"nav_{p}", use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()
    st.markdown('<div style="text-align:center;color:#aab1ca;font-size:11px;margin-top:20px">Streamlit ile hazırlanmıştır</div>', unsafe_allow_html=True)

if st.session_state.page == "Ana Sayfa":
    hero()
    d = get_dashboard_data()
    c1,c2,c3 = st.columns([1.55,1.08,1.35],gap="small")
    with c1:
        st.markdown('<div class="panel">',unsafe_allow_html=True); title("◉","Hava ve Pist Bilgileri","(En fazla 3 şehir)")
        cc=st.columns(3,gap="small")
        for col, city in zip(cc,d["weather"]):
            with col:
                st.markdown(f'''<div class="city-card"><div class="city-name">📍 {city["city"]}</div><div style="font-size:25px">{city["icon"]}</div><div class="city-temp">{city["temp"]}°C</div><div class="small-muted">{city["condition"]}</div><div class="city-meta"><span>Rüzgâr</span><b>{city["wind"]}</b></div><div class="city-meta"><span>Nem</span><b>{city["humidity"]}</b></div><div class="city-meta"><span>Pist</span><b>{city["track"]}</b></div><div class="city-meta"><span>Pist Durumu</span><b>{city["track_state"]}</b></div></div>''',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel">',unsafe_allow_html=True); title("▥","AGF Oranları","(Günün Öne Çıkan Koşusu)"); table(pd.DataFrame(d["agf"]),260); st.markdown('</div>',unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel">',unsafe_allow_html=True); title("🏆","Yarış Sonuçları")
        choice=st.radio("Altılı türü",["1. Altılı","2. Altılı"],horizontal=True,label_visibility="collapsed")
        result=d["results"][choice]; table(pd.DataFrame(result["legs"]),210)
        st.markdown(f'<div class="result-box"><b>{choice} Sonucu:</b> {result["sequence"]}<br><b>İkramiye:</b> {result["payout"]}　|　<b>Bilen kişi:</b> {result["winners"]}</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    a,b=st.columns([1.35,1],gap="small")
    with a:
        st.markdown('<div class="panel">',unsafe_allow_html=True); title("♞","Öne Çıkan Atlar ve Muhtemel Ganyan","(En fazla 15 at)"); table(pd.DataFrame(d["featured"]),300); st.markdown('</div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel">',unsafe_allow_html=True); title("♧","Kazanma Olasılığı Tahmini","(Örnek Model)")
        for x in d["probabilities"]:
            st.markdown(f'<div style="display:grid;grid-template-columns:112px 1fr 45px;gap:7px;align-items:center;margin:13px 0;font-size:12px"><span>{x["horse"]}</span><div style="height:18px;border-radius:5px;background:#292e48;overflow:hidden"><div style="height:100%;width:{x["prob"]}%;background:linear-gradient(90deg,#7644ef,#a15cff)"></div></div><b>{x["prob"]}%</b></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="panel" style="margin-top:12px">',unsafe_allow_html=True); title("▦","Yarış Programı","(Yaklaşan Koşular)"); table(pd.DataFrame(d["program"]),220); st.markdown('</div>',unsafe_allow_html=True)

elif st.session_state.page == "Yarış Programı":
    hero(True)
    f1,f2,f3=st.columns([1.1,1.2,.75],gap="small")
    with f1: st.date_input("Tarih",value=pd.Timestamp("2025-01-26").date(),format="DD.MM.YYYY")
    with f2: track=st.selectbox("Hipodrom",["Tümü (3 Hipodrom)","İstanbul","Ankara","İzmir"])
    with f3: st.write(""); only=st.toggle("Sadece Koşular",value=False)
    races=get_race_program_data()
    if track!="Tümü (3 Hipodrom)": races=[r for r in races if r["track"]==track]
    if only: races=[r for r in races if r["runners"]>0]
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    x,y=st.columns([1,1.2])
    with x: title("▦","Günün Yarış Programı",f"({track})")
    with y: st.markdown('<div style="text-align:right;font-size:12px;padding-top:5px">🏇 3 Hipodrom　 ⚑ 18 Koşu　 ◷ İlk Koşu: 13:00　 🏁 Son Koşu: 19:30</div>',unsafe_allow_html=True)
    selected=st.session_state.get("race_no",1)
    race_cols=st.columns(10,gap="small")
    for n,col in enumerate(race_cols,1):
        r=next((v for v in races if v["no"]==n),None)
        if r:
            with col:
                if st.button(f'{n}. Koşu\\n{r["time"]}',key=f"race_{n}",use_container_width=True,type="primary" if selected==n else "secondary"):
                    st.session_state.race_no=n; st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    race=next((r for r in races if r["no"]==selected),None)
    if race is None: st.info("Seçilen hipodromda bu koşu bulunmuyor.")
    else:
        detail=get_race_detail(selected)
        left,right=st.columns([3.2,1.05],gap="small")
        with left:
            st.markdown('<div class="panel">',unsafe_allow_html=True)
            p1,p2,p3=st.columns([.55,1,1.7])
            with p1: st.markdown(f'<div style="background:#7940f0;border-radius:10px;text-align:center;padding:12px;font-weight:800">{race["no"]}. Koşu</div>',unsafe_allow_html=True)
            with p2: st.markdown(f'**{race["track"]}**<br><span class="small-muted">Hipodrom</span>',unsafe_allow_html=True)
            with p3: st.markdown(f'**{race["name"]}**<br><span class="small-muted">{race["class"]} / {race["age"]} / {race["distance"]} ({race["surface"]})</span>',unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:right;font-size:12px;margin:5px 0 10px">◷ {race["time"]}　|　Koşan At: {race["runners"]}　|　Ödül: {race["prize"]}</div>',unsafe_allow_html=True)
            tab=st.radio("Koşu detayları",["Koşu Bilgisi","Atlar","Sabit Oranlar","Muhtemel Ganyan","Geçmiş Koşular","Galoplar"],horizontal=True,label_visibility="collapsed",key=f"race_detail_{selected}")
            if tab in ["Koşu Bilgisi","Atlar"]: table(pd.DataFrame(detail["horses"]),520)
            elif tab=="Sabit Oranlar": table(pd.DataFrame(detail["fixed_odds"]),520)
            elif tab=="Muhtemel Ganyan": table(pd.DataFrame(detail["probable_odds"]),520)
            elif tab=="Geçmiş Koşular": table(pd.DataFrame(detail["past_runs"]),520)
            else: table(pd.DataFrame(detail["gallops"]),520)
            st.markdown('</div>',unsafe_allow_html=True)
        with right:
            st.markdown('<div class="panel">',unsafe_allow_html=True); title("ⓘ","Koşu Bilgileri")
            for k,v in [("Koşu Türü",race["class"]),("Yaş / Cins",race["age"]),("Mesafe",race["distance"]),("Pist",race["surface"]),("Koşan At Sayısı",race["runners"]),("Ödül",race["prize"])]:
                st.markdown(f'<div class="stat-line"><span>{k}</span><b>{v}</b></div>',unsafe_allow_html=True)
            st.markdown('<div style="font-size:64px;text-align:center;margin-top:14px">🏟️</div><div style="text-align:center;font-weight:700">İstanbul<br><span class="small-muted">Çim Pisti</span></div></div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="hero"><h1><span>GANYAN</span> AYCISI</h1><p>Bu bölüm sonraki geliştirme aşamasında hazırlanacaktır.</p></div>',unsafe_allow_html=True)
    st.info(f"{st.session_state.page} sayfası sonraki aşamada hazırlanacak.")
