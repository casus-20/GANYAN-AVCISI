
"""Demo veri katmanı. Gerçek veri bağlantıları sonraki aşamada eklenecek."""
from copy import deepcopy

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
FEATURED=[{"Sıra":i+1,"At Adı":NAMES[i],"Son 5 Koşu":FORMS[i],"K / G / Y":["3 / 1 / 1","2 / 2 / 1","2 / 1 / 2","1 / 3 / 1","1 / 2 / 2"][i%5],"Muhtemel Ganyan":MG[i]} for i in range(15)]
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
