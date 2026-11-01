
from copy import deepcopy
import re

WEATHER=[
 {"city":"İstanbul","icon":"🌤️","temp":18,"condition":"Parçalı Bulutlu","wind":"12 km/sa","humidity":"%58","track":"Çim","track_state":"İyi"},
 {"city":"Ankara","icon":"☁️","temp":14,"condition":"Çok Bulutlu","wind":"9 km/sa","humidity":"%66","track":"Kum","track_state":"Normal"},
 {"city":"İzmir","icon":"☀️","temp":21,"condition":"Açık","wind":"11 km/sa","humidity":"%52","track":"Çim","track_state":"İyi"},
 {"city":"Bursa","icon":"🌤️","temp":17,"condition":"Az Bulutlu","wind":"8 km/sa","humidity":"%61","track":"Çim","track_state":"İyi"},
 {"city":"Adana","icon":"☀️","temp":24,"condition":"Açık","wind":"10 km/sa","humidity":"%48","track":"Kum","track_state":"Normal"},
]
AGF=[
 {"Sıra":1,"At Adı":"Kara Rüzgar","AGF Oranı":"%32,1"},{"Sıra":2,"At Adı":"Mavi İnci","AGF Oranı":"%21,4"},
 {"Sıra":3,"At Adı":"Yıldızhan","AGF Oranı":"%14,8"},{"Sıra":4,"At Adı":"Sürat Kralı","AGF Oranı":"%11,9"},
 {"Sıra":5,"At Adı":"Beyaz Şimşek","AGF Oranı":"%8,6"},{"Sıra":6,"At Adı":"Altın Nefes","AGF Oranı":"%6,8"},
 {"Sıra":7,"At Adı":"Deniz Aslanı","AGF Oranı":"%5,1"},{"Sıra":8,"At Adı":"Kırat Beyi","AGF Oranı":"%4,8"},
 {"Sıra":9,"At Adı":"Rüzgarın Oğlu","AGF Oranı":"%3,9"},{"Sıra":10,"At Adı":"Işık Han","AGF Oranı":"%3,1"},
 {"Sıra":11,"At Adı":"Göktuğ","AGF Oranı":"%2,6"},{"Sıra":12,"At Adı":"Bahar Gülü","AGF Oranı":"%2,0"},
 {"Sıra":13,"At Adı":"Gümüş Kanat","AGF Oranı":"%1,8"},{"Sıra":14,"At Adı":"Kuzey Yıldızı","AGF Oranı":"%1,6"},
 {"Sıra":15,"At Adı":"Ateş Kuşu","AGF Oranı":"%1,4"},{"Sıra":16,"At Adı":"Kara İnci","AGF Oranı":"%1,2"},
 {"Sıra":17,"At Adı":"Şimşekhan","AGF Oranı":"%1,0"},{"Sıra":18,"At Adı":"Gökçe Bey","AGF Oranı":"%0,8"},
 {"Sıra":19,"At Adı":"Kızıl Rüzgar","AGF Oranı":"%0,6"},{"Sıra":20,"At Adı":"Ay Işığı","AGF Oranı":"%0,4"},
]
NAMES=["Kara Rüzgar","Mavi İnci","Yıldızhan","Sürat Kralı","Beyaz Şimşek","Altın Nefes","Deniz Aslanı","Kırat Beyi","Rüzgarın Oğlu","Işık Han","Göktuğ","Bahar Gülü","Gümüş Kanat","Kuzey Yıldızı","Ateş Kuşu"]
FORMS=["1 2 4 1 3","2 1 2 3 5","1 3 1 4 2","3 2 2 1 4","1 4 3 2 5","2 5 1 3 2","4 1 3 5 1","3 3 2 4 1","5 2 4 3 2","2 4 5 1 3","4 3 5 2 4","5 4 3 5 2","3 2 4 1 5","2 5 2 3 4","4 2 5 4 1"]
MG=["2,45","3,20","4,10","4,85","7,20","8,10","9,35","11,20","13,50","14,80","18,50","22,00","24,00","27,50","31,00"]
AGF_VALUES=["%32,1","%21,4","%14,8","%11,9","%8,6","%6,8","%5,1","%4,8","%3,9","%3,1","%2,6","%2,0","%1,8","%1,6","%1,4"]
# Altı yarışlık form dizisi HORSES verisindeki son 6 yarış sütunundan oluşturulur.
PROGRAM=[
 {"Koşu":"1. Koşu","Saat":"13:30","Hipodrom":"İstanbul","Mesafe / Pist":"1200 m (Çim)","Sınıf":"Şartlı 4","Koşu Adı":"Günün Açılış Koşusu","Koşan At Sayısı":12},
 {"Koşu":"2. Koşu","Saat":"14:00","Hipodrom":"İstanbul","Mesafe / Pist":"1400 m (Kum)","Sınıf":"Handikap 15","Koşu Adı":"Bahar Handikapı","Koşan At Sayısı":14},
 {"Koşu":"3. Koşu","Saat":"14:30","Hipodrom":"Ankara","Mesafe / Pist":"1600 m (Çim)","Sınıf":"KV-7","Koşu Adı":"Ankara Koşusu","Koşan At Sayısı":9},
 {"Koşu":"4. Koşu","Saat":"15:00","Hipodrom":"İstanbul","Mesafe / Pist":"1900 m (Kum)","Sınıf":"Şartlı 3","Koşu Adı":"Marmara Koşusu","Koşan At Sayısı":11},
]
HORSES=[
 ["1","Kara Rüzgar","3y E","Torok (USA) - Mavi Ay","58,0","A. Çelik","B. Yılmaz","M. Kaya","5","78","1 2 1 4 3 1","92","1,08","3,20","2,45"],
 ["2","Mavi İnci","3y D","Hakeem - İnci Tanesi","56,5","H. Karataş","A. Demir","S. Demir","2","76","2 1 3 5 4 1","88","1,12","4,50","3,20"],
 ["3","Yıldızhan","3y E","Luxor - Yıldız Tozu","56,5","G. Kocakaya","M. Aslan","E. Yılmaz","8","75","1 3 1 4 2 1","91","1,07","6,00","4,10"],
 ["4","Sürat Kralı","3y E","Victory Gallop - Sürat","55,0","Ö. Yıldırım","K. Kaya","H. Çetin","3","74","3 2 2 1 4 2","86","1,14","5,00","4,85"],
 ["5","Beyaz Şimşek","3y D","Perfecto - Beyaz İnci","55,0","M. Akyavuz","E. Kaya","A. Arslan","1","73","1 4 3 2 3 1","84","1,15","7,50","7,20"],
 ["6","Altın Nefes","3y E","Reach The Sun - Altın Yonca","54,5","S. Boyraz","H. Öztürk","K. Güneş","10","72","2 5 1 3 2 1","83","1,16","7,00","8,10"],
 ["7","Deniz Aslanı","3y E","Ocean Crest - Deniz Kızı","54,5","E. Aktuğ","C. Aksoy","B. Tekin","6","71","4 1 3 5 1 2","81","1,18","9,00","9,35"],
 ["8","Kırat Beyi","3y E","Kafkaslı - Kır Çiçeği","54,0","M. M. Bilgin","Y. Usta","C. Polat","7","70","3 3 2 4 1 1","80","1,19","11,00","11,20"],
 ["9","Rüzgarın Oğlu","3y E","Storm Runner - Meltem","53,5","A. Sözen","F. Karaca","M. Aslan","4","69","5 2 4 3 2 2","78","1,21","13,00","13,50"],
 ["10","Işık Han","3y E","Light Speed - Işık Saçan","53,5","K. Tokaçoğlu","D. Yıldız","Y. Usta","9","68","2 4 5 1 3 2","75","1,23","16,00","14,80"],
 ["11","Göktuğ","3y D","King's Honor - Gökyüzü","53,0","U. Demir","S. Yalçın","F. Kaya","12","66","4 3 5 2 4 3","72","1,25","18,00","18,50"],
 ["12","Bahar Gülü","3y D","Flower Alley - Bahar Rengi","52,0","M. Keçeci","N. Şahin","R. Yıldız","11","65","5 4 3 5 2 4","70","1,27","22,00","22,00"],
]
HORSE_COLS=["Sıra","At Adı","Yaş / Cins","Orijin (Baba - Anne)","Sıklet","Jokey","Sahip","Antrenör","St.","HP","Son 6 Y.","KGS","EİD","Sabit Oran","Muhtemel Ganyan"]
FEATURED=[{"Sıra":i+1,"At Adı":NAMES[i],"Son 6 Koşu":" ".join(HORSES[i][10].split()[-6:]),"K / G / Y":["3 / 1 / 1","2 / 2 / 1","2 / 1 / 2","1 / 3 / 1","1 / 2 / 2"][i%5],"AGF":AGF_VALUES[i],"Muhtemel Ganyan":MG[i]} for i in range(len(HORSES))]

def get_dashboard_data():
    legs1=[
     {"Ayak":"1. Ayak","Koşu":"1. Koşu","Kazanan At":"Kara Rüzgar","Ganyan":"2,45","AGF":"%32,1","Bitiş Derecesi":"1:24.36"},
     {"Ayak":"2. Ayak","Koşu":"2. Koşu","Kazanan At":"Mavi İnci","Ganyan":"3,20","AGF":"%21,4","Bitiş Derecesi":"1:37.11"},
     {"Ayak":"3. Ayak","Koşu":"3. Koşu","Kazanan At":"Altın Nefes","Ganyan":"8,10","AGF":"%6,8","Bitiş Derecesi":"1:49.21"},
     {"Ayak":"4. Ayak","Koşu":"4. Koşu","Kazanan At":"Deniz Aslanı","Ganyan":"9,35","AGF":"%5,1","Bitiş Derecesi":"1:23.78"},
     {"Ayak":"5. Ayak","Koşu":"5. Koşu","Kazanan At":"Yıldızhan","Ganyan":"4,10","AGF":"%14,8","Bitiş Derecesi":"1:36.42"},
     {"Ayak":"6. Ayak","Koşu":"6. Koşu","Kazanan At":"Kırat Beyi","Ganyan":"11,20","AGF":"%4,8","Bitiş Derecesi":"2:02.15"}]
    legs2=[{"Ayak":f"{i+1}. Ayak","Koşu":f"{i+5}. Koşu","Kazanan At":NAMES[(i+2)%12],"Ganyan":["4,10","8,10","9,35","11,20","2,45","3,20"][i],"AGF":["%14,8","%6,8","%5,1","%4,8","%32,1","%21,4"][i],"Bitiş Derecesi":["1:36.42","2:02.15","1:24.36","1:37.11","1:49.21","1:23.78"][i]} for i in range(6)]
    return {"weather":deepcopy(WEATHER),"agf":deepcopy(AGF),"featured":deepcopy(FEATURED),
     "probabilities":[{"horse":"(4) Kara Rüzgar","prob":42.1},{"horse":"(7) Mavi İnci","prob":18.6},{"horse":"(2) Yıldızhan","prob":13.9},{"horse":"(5) Sürat Kralı","prob":11.7},{"horse":"(1) Beyaz Şimşek","prob":6.8}],
     "results":{"1. Altılı":{"city":"İstanbul","legs":legs1,"sequence":"4 - 7 - 3 - 1 - 6 - 2","payout":"426.580,00 ₺","winners":"12"},"2. Altılı":{"city":"İstanbul","legs":legs2,"sequence":"3 - 1 - 6 - 2 - 4 - 7","payout":"184.250,00 ₺","winners":"8"}},
     "program":deepcopy(PROGRAM)}

def get_race_program_data():
    base=[
     (1,"13:00","İstanbul","Günün Açılış Koşusu","Şartlı 4","3 yaşlı İngilizler","1200 m","Çim",12,"₺540.000"),
     (2,"13:30","İstanbul","Bahar Handikapı","Handikap 15","4+ yaşlı İngilizler","1400 m","Kum",14,"₺450.000"),
     (3,"14:00","Ankara","Ankara Koşusu","KV-7","3+ yaşlı İngilizler","1600 m","Çim",9,"₺700.000"),
     (4,"14:30","İstanbul","Marmara Koşusu","Şartlı 3","4+ yaşlı Araplar","1900 m","Kum",11,"₺420.000"),
     (5,"15:00","İzmir","Ege Handikapı","Handikap 16","3+ yaşlı İngilizler","2000 m","Çim",13,"₺480.000"),
     (6,"15:30","İstanbul","Boğaziçi Koşusu","Şartlı 5","4+ yaşlı İngilizler","1800 m","Sentetik",10,"₺500.000"),
     (7,"16:00","Ankara","Başkent Koşusu","KV-6","3 yaşlı İngilizler","1400 m","Kum",8,"₺390.000"),
     (8,"16:30","İzmir","Ege Kupası","Şartlı 4","4+ yaşlı Araplar","1500 m","Kum",12,"₺410.000"),
     (9,"17:00","İstanbul","Sonbahar Koşusu","Handikap 14","3+ yaşlı İngilizler","2100 m","Çim",15,"₺460.000"),
     (10,"18:00","İzmir","Günün Kapanış Koşusu","Şartlı 3","4+ yaşlı Araplar","1200 m","Kum",9,"₺380.000")]
    return [dict(zip(["no","time","track","name","class","age","distance","surface","runners","prize"],r)) for r in base]

def get_race_detail(race_no=1):
    horses=[dict(zip(HORSE_COLS,row)) for row in HORSES]
    return {"horses":horses,
     "fixed_odds":[{"Sıra":h["Sıra"],"At Adı":h["At Adı"],"Sabit Oran":h["Sabit Oran"]} for h in horses],
     "probable_odds":[{"Sıra":h["Sıra"],"At Adı":h["At Adı"],"Muhtemel Ganyan":h["Muhtemel Ganyan"]} for h in horses],
     "past_runs":[{"Tarih":"19.01.2025","Pist":"Çim","Mesafe":"1200","Derece":"1:11.37","Sıra":1},{"Tarih":"29.12.2024","Pist":"Çim","Mesafe":"1400","Derece":"1:23.12","Sıra":2},{"Tarih":"08.12.2024","Pist":"Kum","Mesafe":"1200","Derece":"1:11.90","Sıra":1},{"Tarih":"17.11.2024","Pist":"Çim","Mesafe":"1200","Derece":"1:12.45","Sıra":3},{"Tarih":"27.10.2024","Pist":"Çim","Mesafe":"1400","Derece":"1:23.80","Sıra":1},{"Tarih":"06.10.2024","Pist":"Kum","Mesafe":"1200","Derece":"1:11.96","Sıra":4}],
     "gallops":[{"At":"Kara Rüzgar","Tarih":"24.01.2025","İş":"600/37,8 - 400/24,2","Pist":"İç pist","Not":"Rahat"},{"At":"Mavi İnci","Tarih":"24.01.2025","İş":"800/50,6 - 400/24,8","Pist":"İç pist","Not":"Canlı"},{"At":"Yıldızhan","Tarih":"23.01.2025","İş":"600/38,1 - 400/24,5","Pist":"İç pist","Not":"İyi"},{"At":"Sürat Kralı","Tarih":"23.01.2025","İş":"1000/1.02,4 - 400/24,9","Pist":"İç pist","Not":"Rahat"}]}

# ============================================================
# TJK RESMİ GÜNLÜK YARIŞ PROGRAMI
# ============================================================
def _tjk_norm(value):
    import unicodedata
    value=str(value or "").translate(str.maketrans({"ı":"i","İ":"i","ş":"s","Ş":"s","ğ":"g","Ğ":"g","ü":"u","Ü":"u","ö":"o","Ö":"o","ç":"c","Ç":"c"}))
    value=unicodedata.normalize("NFKD",value)
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+","",value.lower())

def _tjk_cell_text(cell):
    return re.sub(r"\s+"," ",cell.get_text(" ",strip=True)).strip()

def _tjk_city_links(html,base_url):
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin,urlparse,parse_qs
    soup=BeautifulSoup(html,"html.parser")
    found={}
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        # TJK bağlantılarında SehirId bazı sayfa sürümlerinde bulunmayabilir.
        if not re.search(r"SehirAdi|sehirAdi|Sehir=", href, re.I):
            continue
        full=urljoin(base_url,href)
        query=parse_qs(urlparse(full).query)
        city=(query.get("SehirAdi") or query.get("sehirAdi") or query.get("Sehir") or [""])[0].strip()
        if not city: continue
        label=re.sub(r"\s*\([^)]*\)\s*","",_tjk_cell_text(a)).strip() or city
        if label.lower() not in {"karma"}: found[label]=full
    return found

def _tjk_find_header_row(table):
    rows=table.find_all("tr")
    aliases={"atisimi","atismi","atadi","jokey","siklet","hp"}
    for idx,row in enumerate(rows[:10]):
        cells=row.find_all(["th","td"],recursive=False)
        vals=[_tjk_norm(_tjk_cell_text(c)) for c in cells]
        if len(set(vals)&aliases)>=2: return idx,cells
    return None,None

def _tjk_parse_horse_tables(html):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,"html.parser")
    page_text=soup.get_text("\n",strip=True)
    matches=list(re.finditer(r"(?i)(\d{1,2})\s*\.\s*koşu",page_text))
    meta={}
    for i,m in enumerate(matches):
        no=int(m.group(1)); stop=matches[i+1].start() if i+1<len(matches) else min(len(page_text),m.end()+5000)
        chunk=page_text[m.start():stop]; lines=[x.strip() for x in chunk.splitlines() if x.strip()]
        tm=re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",chunk)
        dist=re.search(r"\b(\d{3,4})\s*(?:m|metre)\b",chunk,re.I)
        surf=re.search(r"\b(Çim|Kum|Sentetik)\b",chunk,re.I)
        prize=re.search(r"(?:₺\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{2})?)\s*(?:₺|TL)",chunk,re.I)
        name=next((x for x in lines[1:10] if len(x)<=110 and re.search(r"(?i)(koşusu|kupası|ödülü)",x)),"")
        cls_match=re.search(r"(?i)(maiden|şartlı\s*\d*|handikap\s*\d*|kv-\s*\d+|satış\s*\d*)",chunk)
        cls=cls_match.group(0).strip() if cls_match else ""
        age_match=re.search(r"(?i)(\d+\s*(?:ve\s*yukarı\s*)?yaşlı\s+(?:ingilizler|araplar)|\d+\s*yaşlı\s+(?:ingiliz|arap))",chunk)
        age=age_match.group(0).strip() if age_match else ""
        meta[no]={"no":no,"time":tm.group(0) if tm else "","name":name,"class":cls,"age":age,"distance":f"{dist.group(1)} m" if dist else "","surface":surf.group(1).title() if surf else "","prize":f"{prize.group(1)} ₺" if prize else ""}

    # TJK programında eküri bilgisi çoğunlukla tablonun altında
    # [(1)AT ADI,(5)DİĞER AT] eküridir. biçiminde yayımlanır.
    ekuri_names = set()
    for group in re.findall(r"\[([^\]]+)\]\s*ek[uü]r[iı]dir", page_text, flags=re.I):
        for entry in re.split(r"\s*,\s*", group):
            entry = re.sub(r"^\(?\d+\)?\s*", "", entry).strip(" ()")
            if entry:
                ekuri_names.add(_tjk_norm(entry))

    tables=[]
    for table in soup.find_all("table"):
        hidx,hcells=_tjk_find_header_row(table)
        if hidx is None: continue
        headers=[_tjk_norm(_tjk_cell_text(c)) for c in hcells]
        horses=[]
        for row in table.find_all("tr")[hidx+1:]:
            cells=row.find_all(["td","th"],recursive=False); vals=[_tjk_cell_text(c) for c in cells]
            if not vals or not any(vals): continue
            rowmap={h:(vals[j] if j<len(vals) else "") for j,h in enumerate(headers)}
            name=rowmap.get("atisimi") or rowmap.get("atismi") or rowmap.get("atadi")
            if not name or _tjk_norm(name) in {"atisimi","atismi","atadi"}: continue
            horses.append(rowmap)
        if horses: tables.append((table,horses,hidx))

    result={}
    for idx,(table,rows,table_header_index) in enumerate(tables,1):
        no=idx
        meta.setdefault(no,{"no":no,"time":"","name":"","class":"","age":"","distance":"","surface":"","prize":""})
        horses=[]
        source_rows = table.find_all("tr")
        for row_index, row in enumerate(rows):
            def v(*keys):
                return next((row[k] for k in keys if row.get(k)),"")
            source_cells = source_rows[table_header_index + 1 + row_index].find_all(["td", "th"], recursive=False) if table_header_index + 1 + row_index < len(source_rows) else []
            at_id = ""
            for cell in source_cells:
                for anchor in cell.find_all("a", href=True):
                    match = re.search(r"(?:AtId|AtID|atId)=(\d+)", anchor.get("href", ""), re.I)
                    if match:
                        at_id = match.group(1)
                        break
                if at_id:
                    break
            eid_info = ""
            eid_index = next((i for i, key in enumerate(headers) if key in {"eniyid", "eniyiderece", "eid"}), None)
            if eid_index is not None and eid_index < len(source_cells):
                eid_cell = source_cells[eid_index]
                info_parts = []
                for node in [eid_cell] + eid_cell.find_all(True):
                    for attr in ("title", "data-original-title", "data-content", "data-tooltip", "aria-label"):
                        value = node.get(attr) if hasattr(node, "get") else None
                        if value:
                            cleaned = re.sub(r"\\s+", " ", str(value)).strip()
                            if cleaned and cleaned not in info_parts:
                                info_parts.append(cleaned)
                eid_info = " | ".join(info_parts)
            raw_horse_name = v("atisimi","atismi","atadi")
            status_is_nonrunner = bool(re.search(r"\(\s*ko[sş]maz\s*\)", raw_horse_name, flags=re.I))
            clean_horse_name = re.sub(r"\s*\(\s*ko[sş]maz\s*\)", "", raw_horse_name, flags=re.I).strip()
            name_for_ekuri = re.sub(r"\s*\(\d{1,2}\)", "", clean_horse_name)
            name_for_ekuri = re.sub(r"\s*image\s*$", "", name_for_ekuri, flags=re.I).strip()
            is_ekuri = _tjk_norm(name_for_ekuri) in ekuri_names
            horses.append({
                "_at_id": at_id,
                "Koşmaz": status_is_nonrunner,
                "Eküri": is_ekuri,
                "EİD Bilgi": eid_info,
                "Sıra":v("n","sira","forma"),"At Adı":clean_horse_name,
                "Yaş / Cins":v("yas","yascins","yascinsiyet"),"Orijin (Baba - Anne)":v("orijinbabaanne","orijinbabaannen","orijinbabaannesi","orijin"),
                "Sıklet":v("siklet","kilo"),"Jokey":v("jokey"),"Sahip":v("sahip","atsahibi"),
                "Antrenör":v("antrenor"),"St.":v("st","start"),"HP":v("hp"),"Son 6 Y.":v("son6y","son6yaris","form"),
                "KGS":v("kgs"),"s20":v("s20","son20","son20y","son20yaris","son20kosu","son20kosular"),"EİD":v("eniyid","eniyiderece","eid"),"Sabit Oran":v("sabit oran","oran"),
                "Muhtemel Ganyan":v("gny","ganyan")})
        race=meta[no]; race["runners"]=len(horses)
        result[no]={"race":race,"horses":horses,
            "fixed_odds":[{"Sıra":h["Sıra"],"At Adı":h["At Adı"],"Sabit Oran":h["Sabit Oran"]} for h in horses if h["Sabit Oran"]],
            "probable_odds":[{"Sıra":h["Sıra"],"At Adı":h["At Adı"],"Muhtemel Ganyan":h["Muhtemel Ganyan"]} for h in horses if h["Muhtemel Ganyan"]],
            "past_runs":[],"gallops":[]}
    return result

@__import__("functools").lru_cache(maxsize=32)
def get_tjk_race_program(date_text):
    """TJK günlük programını tarih başına bir kez indirir; hipodrom sayfalarını paralel okur."""
    import requests
    from concurrent.futures import ThreadPoolExecutor
    from urllib.parse import urljoin

    base = "https://www.tjk.org/TR/Kurumsal/Info/Page/GunlukYarisProgrami"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.7",
        "Referer": "https://www.tjk.org/",
    }

    # Ana sayfa yalnızca bir kez alınır; hipodrom listesi bunun içinden çıkarılır.
    with requests.Session() as session:
        session.headers.update(headers)
        response = session.get(base, params={"QueryParameter_Tarih": date_text}, timeout=(6, 20))
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        links = _tjk_city_links(response.text, response.url)

    if not links:
        raise RuntimeError("TJK sayfasında seçilen tarihe ait hipodrom bağlantıları bulunamadı.")

    def fetch_city(item):
        city, url = item
        # requests.Session nesnesi thread'ler arasında paylaşılmaz.
        with requests.Session() as city_session:
            city_session.headers.update(headers)
            last_error = None
            for attempt in range(2):
                try:
                    page = city_session.get(url, timeout=(6, 20))
                    page.raise_for_status()
                    page.encoding = page.apparent_encoding or "utf-8"
                    parsed = _tjk_parse_horse_tables(page.text)
                    if not parsed:
                        return city, None
                    races = []
                    details = {}
                    for no in sorted(parsed):
                        detail = parsed[no]
                        race = dict(detail["race"])
                        race["track"] = city
                        races.append(race)
                        details[f"{city}|{no}"] = {k: v for k, v in detail.items() if k != "race"}
                    return city, (races, details)
                except requests.RequestException as exc:
                    last_error = exc
            raise RuntimeError(f"TJK {city} sayfası alınamadı: {last_error}")

    # Şehir sayfalarını seri beklemek yerine eşzamanlı indir. Sonuçlar link sırasıyla birleştirilir.
    items = list(links.items())
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as pool:
        results = list(pool.map(fetch_city, items))

    tracks, races_by_track, details = [], {}, {}
    errors = []
    for city, payload in results:
        if payload is None:
            continue
        races, city_details = payload
        tracks.append(city)
        races_by_track[city] = races
        details.update(city_details)

    if not tracks:
        raise RuntimeError("TJK sayfasına erişildi ancak seçilen tarihin koşu tabloları okunamadı.")
    return {"tracks": tracks, "races_by_track": races_by_track, "details": details}


@__import__("functools").lru_cache(maxsize=512)
def _cached_tjk_horse_history(at_id):
    """AtKosuBilgileri sayfasından geçmiş yarışları doğrudan TJK'dan alır."""
    import requests
    from bs4 import BeautifulSoup
    urls = [
        f"https://www.tjk.org/TR/kurumsal/Query/ConnectedPage/AtKosuBilgileri?1=1&QueryParameter_AtId={at_id}",
        f"https://www.tjk.org/TR/map/Query/ConnectedPage/AtKosuBilgileri?1=1&QueryParameter_AtId={at_id}",
    ]
    session = requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Referer":"https://www.tjk.org/"})
    last_error = None
    aliases = {"tarih":"Tarih", "sehir":"Hipodrom", "msf":"Mesafe", "mesafe":"Mesafe", "pist":"Pist", "s":"Sıra", "derece":"Derece", "siklet":"Sıklet", "jokey":"Jokey", "st":"St.", "gny":"Gny", "grup":"Grup", "ant":"Antrenör", "sahip":"Sahip", "hp":"HP", "ikramiye":"İkramiye", "s20":"Son 20"}
    def norm(x):
        x=x.lower().translate(str.maketrans("ıişğüöç","iisguoc"))
        return re.sub(r"[^a-z0-9]+","",x)
    for url in urls:
        try:
            r=session.get(url,timeout=25); r.raise_for_status()
            soup=BeautifulSoup(r.text,"html.parser")
            for table in soup.find_all("table"):
                trs=table.find_all("tr")
                for hi,tr in enumerate(trs[:12]):
                    hs=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["th","td"],recursive=False)]
                    if "tarih" not in hs or not ({"derece","pist"}&set(hs)):
                        continue
                    cols=[aliases.get(h,h) for h in hs]
                    out=[]
                    for rr in trs[hi+1:]:
                        vals=[c.get_text(" ",strip=True) for c in rr.find_all(["td","th"],recursive=False)]
                        if len(vals)<5 or not re.search(r"\d{1,2}[./]\d{1,2}[./]20\d{2}", vals[0] if vals else ""):
                            continue
                        item={cols[i]:(vals[i] if i<len(vals) else "") for i in range(len(cols))}
                        item["Tarih"]=vals[0]
                        out.append(item)
                    if out:
                        return out
            last_error="TJK geçmiş yarış tablosu bulunamadı veya boş döndü"
        except Exception as exc:
            last_error=str(exc)
    raise RuntimeError(last_error or "TJK geçmiş yarış bilgisi alınamadı")

def get_tjk_horse_history(at_id):
    if not at_id:
        return []
    return _cached_tjk_horse_history(str(at_id))


# Yarış Programı sayfası için fetch.py veri adaptörleri.
def get_tjk_active_cities(date_value):
    from datetime import datetime, date
    if isinstance(date_value, (datetime, date)):
        date_text = date_value.strftime("%d/%m/%Y")
    else:
        raw = str(date_value or "").strip()
        try:
            date_text = datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            date_text = raw
    data = get_tjk_race_program(date_text)
    return list(data.get("tracks") or [])

def get_tjk_program(date_value, city):
    from datetime import datetime, date
    if isinstance(date_value, (datetime, date)):
        date_text = date_value.strftime("%d/%m/%Y")
        iso_date = date_value.strftime("%Y-%m-%d")
    else:
        raw = str(date_value or "").strip()
        try:
            parsed_date = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            parsed_date = datetime.strptime(raw, "%d/%m/%Y")
        date_text = parsed_date.strftime("%d/%m/%Y")
        iso_date = parsed_date.strftime("%Y-%m-%d")
    data = get_tjk_race_program(date_text)
    tracks = data.get("tracks") or []
    actual_city = next((x for x in tracks if _tjk_norm(x) == _tjk_norm(city)), None)
    if not actual_city:
        raise RuntimeError(f"TJK {date_text} tarihinde {city} için yarış programı döndürmedi.")
    races = []
    for race_meta in (data.get("races_by_track") or {}).get(actual_city, []):
        no = int(race_meta.get("no") or 0)
        detail = (data.get("details") or {}).get(f"{actual_city}|{no}", {})
        horses = []
        for h in detail.get("horses", []):
            horses.append({
                "no": h.get("Sıra") or "",
                "name": h.get("At Adı") or "",
                "age": h.get("Yaş / Cins") or "",
                "origin": h.get("Orijin (Baba - Anne)") or "",
                "weight": h.get("Sıklet") or "",
                "jockey": h.get("Jokey") or "", "owner": h.get("Sahip") or "",
                "trainer": h.get("Antrenör") or "", "st": h.get("St.") or "",
                "hp": h.get("HP") or "", "last6": h.get("Son 6 Y.") or "",
                "kgs": h.get("KGS") or "", "s20": h.get("s20") or h.get("Son 20") or "", "bestTime": h.get("EİD") or "",
                "bestInfo": h.get("EİD Bilgi") or "",
                "odds": h.get("Muhtemel Ganyan") or h.get("Sabit Oran") or "", "agf": "",
                "atId": h.get("_at_id") or "",
            })
        races.append({
            "no": no, "time": race_meta.get("time") or "", "name": race_meta.get("name") or f"{no}. Koşu",
            "class": race_meta.get("class") or "", "age": race_meta.get("age") or "",
            "distance": race_meta.get("distance") or "", "surface": race_meta.get("surface") or "",
            "prize": race_meta.get("prize") or "", "horses": horses,
        })
    if not races:
        raise RuntimeError(f"TJK {actual_city} programı bulundu ancak koşu/at tablosu ayrıştırılamadı.")
    return {"ok": True, "date": iso_date, "city": actual_city, "races": races,
            "raceCount": len(races), "horseCount": sum(len(x["horses"]) for x in races),
            "source": "TJK resmi günlük yarış programı"}
