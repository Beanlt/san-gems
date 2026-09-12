#!/usr/bin/env python3
# SAN GEMS — MOT script, BA loi.
#   python3 SAN.py nguoc DA-BAO.md     mua con dang ROI  (giam 20-50%/24h, pool >24h)
#   python3 SAN.py nolai DA-BAO.md     mua con DA TUNG TANG roi xep, gio nhich len lai
#   python3 SAN.py dayphang DA-BAO.md  mua con DA XEP ROI NAM IM 24h, gio co nguoi vao
#     (loi DAY PHANG chia 3 buoc vi bash cat o 300 giay:
#      SAN.py dayphang-feed  ·  SAN.py dayphang-nen 0 17  ·  SAN.py dayphang DA-BAO.md)
# Ba loi khac nhau. Cam tron so vao mot bang.
# 🔑 FILE NAY LA NGUON DUY NHAT CUA SO. Cac file .md khac chi TRO toi, cam chep lai.
import json,time,calendar,sys,os,urllib.request,urllib.error,statistics as st

UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
GT ="https://api.geckoterminal.com/api/v2/networks/robinhood/pools"
RPC="https://rpc.mainnet.chain.robinhood.com"
BS ="https://robinhoodchain.blockscout.com"
PM  ="0x8366a39cc670b4001a1121b8f6a443a643e40951"
SWAP="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

# ---- CHUNG CHO CA BA LOI ----
MC_MIN,MC_MAX = 50_000, 1_500_000
CO_LENH       = 250
KHU_HOI_MAX   = 5.0         # 🔴 CUA PHI. Bean chot 07/09: do THANG khu hoi, bo cua doi ung $40K.
                            #    5% ~ doi ung $20.000 voi lenh $250. Ly do day du: LUAT.md muc 3.1
DOI_UNG_SAN   = 4*CO_LENH/(KHU_HOI_MAX/100)      # = 20.000, suy ra tu cua phi, khong go tay
RESERVE_SO    = int(2*DOI_UNG_SAN)               # = 40.000. Loc so bo; reserve = TONG POOL,
                                                 # lon hon doi ung 2,0-4,5 lan (HATANG.md muc 6)
GIO_KHONG_BAO_LAI = 48
VI_TO_MAX     = 5.0         # vi nguoi to nhat ngoai pool. Nguong VUNG duy nhat (>40 ca).
TOP10_MAX     = 25.0
TRANG=10; LO_POOL=12
# 🔴 VA 11/09: may GitHub bi GeckoTerminal siet tan suat nang hon may nha — luot 20:17
#    mat 2 trang feed vi 429. Gian them khi chay tren GitHub.
#    KHONG phai nguong san, chi la nhip goi mang.
GIAN = 3.5 if os.environ.get("GITHUB_ACTIONS") else 2.2
# 🔴 VA 11/09: dai 6.000 khoi = 10,3 phut (do that 11/09 15:09). Pool nho 10 phut khong co
#    lenh nao la chuyen thuong -> hang loat con bi ghi ⛔ OAN. Luot VET nhin lui rong hon.
# ⬜ CHUA DO tran thoi gian cua dai 60.000 khoi voi lo 6 pool. Da do: dai 60.000 voi 1 pool
#    chay sach (ca ATLAS 11/09 15:09). Thay `log query timed out` trong phieu thi ha
#    LO_VET xuong 3, hoac ha DAI_VET xuong 30.000. Sua xong ghi lai ket qua vao day.
DAI_VET=60000; LO_VET=6

# ---- RIENG LOI NGUOC ----
GIA_MIN,GIA_MAX = -50.0,-20.0
TUOI_MIN_H      = 24.0
# ---- RIENG LOI DAY PHANG (luat o LUAT.md muc 2.3) ----
DP_MC_MAX     = 1_000_000
DP_KHU_HOI    = 8.0        # ⬜ chua quet do nhay
DP_RES_SO     = int(2*(4*CO_LENH/(DP_KHU_HOI/100)))
DP_NO_LAN     = 3.0
DP_XEP_TOI    = 0.30
DP_DAI_SAT    = 0.15
DP_GIO_SAT    = 12         # ⬜ sua lan 1 (08/09): 16 -> 12 = mot nua so gio
DP_VOL_LAN    = 3.0        # ⬜ chua kiem
DP_NEN_MIN    = 48
DP_STATE="dp_state.json"; DP_CANDS="dp_cands.json"; DP_SODO="DO-DEM.md"

# ---- RIENG LOI NO LAI ----
NO_LAN     = 3.0      # dinh >= 3x day truoc dinh
XEP_TOI    = 0.32     # da xep >=68% tu dinh, tuc gia nay <= 32% dinh. Bean chot 07/09.
NHIP_H1    = 2.0      # gia 1 gio >= +2%
CUA_SO_NEN = 1000     # 41 ngay. Tran that da do: >=1.000 cay.

# 🔴 NGUON DUY NHAT. Locker da doc ma -> co mat trong bang nguoi giu = pool chinh khoa vinh vien.
KHOA={"0x267444d099b10fb5ed7c3cc7b7c767adca574952":"PonsV2LaunchLocker",
      "0x736d76699c26d0d966744cae304c000d471f7f35":"Locker Pons V3",
      "0x31ca5e101941a93a7dd6d0497928700625cf54b5":"Locker Pons legacy",
      "0x7f03effbd7ceb22a3f80dd468f67ef27826acd85":"LaunchLocker meow",
      "0xba2f330edb16cd8056f5988d8ce19bbc63475a0e":"NoOpMigrator",
      "0xbe0b139abc90723af76a89d3051f60ba1b64c8d9":"PinkLock02"}
# Loc ha tang bang DIA CHI CUNG, khong bang regex (HATANG.md muc 10, bay so 2)
HATANG={"0x8366a39cc670b4001a1121b8f6a443a643e40951":"PoolManager",
        "0xea1cf9606b87773ae96330ee4ca95f6062be81ba":"vi ha tang lo Pons v2",
        "0xf017306a84d1be3a72ae444b303d0c3d92a0d852":"hop dong phat hanh Pons v2",
        "0x000000000000000000000000000000000000dead":"vi dot"}

# 🔴 LOAI THANG TU TEN. Ca da lot that: OPENAI (09/09) · AMD (09/09) · ANTHROPIC (10/09)
#    · RIVN + QUBT (11/09 — lot toi tan danh sach ung vien DAY PHANG, chi tinh co bi
#      cua doi ung chan). Day la lan va thu hai cua danh sach nay.
CO_PHIEU={"SPY","AAPL","NVDA","GLD","MSFT","AMZN","META","GOOGL","QQQ","TSLA","MSTR","MU",
          "HIMS","LIT","TSM","SPCX","AI","ETH","USDG","QC","BTC","COIN","PLTR","RBLX","HOOD","SOL",
          "RIVN","QUBT","AMD","OPENAI","ANTHROPIC","USO"}

# ⚠️ CANH BAO, KHONG LOAI. Ma trung ticker san My nhung CHUA co ca that tren chuoi nay.
#    In ra phieu de nguoi doc tu quyet — dung lam cua chan, vi luat cam loai bang cai ten
#    khi chua mo ra kiem (KYLUAT.md muc 1, ca LUNA9).
# ⬜ CHUA QUET DO NHAY: chua biet danh sach nay co bao gio bao nham mot memecoin that khong.
#    Lan sau doc phieu, dem so lan hien ⚠️ va xem co ca nao bao nham -> roi moi ban co
#    chuyen mot mã nao tu day sang CO_PHIEU khong.
CO_PHIEU_NGO={"INTC","SMH","ASML","QCOM","EWY","SKYHY","COST","GME","AMC","NFLX","DIS","BA","F",
              "GM","UBER","LYFT","SOFI","PYPL","ARM","AVGO","ORCL","CRM","ADBE","IBM","GS","JPM",
              "BAC","WMT","TGT","KO","PEP","MCD","NKE","SBUX","XOM","CVX","PFE","JNJ","UNH","V",
              "MA","T","VZ","CSCO","QS","LCID","NIO","PLUG","RKLB","ACHR","IONQ","RGTI","SMCI"}

T0=time.time(); CU=[0]

def in_nguong():
    """KYLUAT.md muc 14 so 3: script TU IN hang so no dang chay, dong dau moi luot.
    Lech giua file .md va code la thay ngay, khong can ai nho gi."""
    print("NGUONG DANG CHAY: mc $%s-$%s · khu hoi <=%.1f%% · co lenh $%d · KHONG co moc ban"%(
          format(MC_MIN,","),format(MC_MAX,","),KHU_HOI_MAX,CO_LENH))
    print("   NGUOC: gia24 %.0f..%.0f%% · tuoi pool >=%.0fh"%(GIA_MIN,GIA_MAX,TUOI_MIN_H))
    print("   NO LAI: no >=%.1fx · xep <=%.0f%% dinh · nhip 1h >=+%.1f%%"%(
          NO_LAN,XEP_TOI*100,NHIP_H1))
    print("   DAY PHANG: khu hoi <=%.0f%% · xep <=%.0f%% · nam im >=%d/24 · vol >=%.0fx"%(
          DP_KHU_HOI,DP_XEP_TOI*100,DP_GIO_SAT,DP_VOL_LAN))
    print("   CUA NANG: vi to nhat <=%.0f%% · top10 <=%.0f%% · doi ung san $%s"%(
          VI_TO_MAX,TOP10_MAX,format(int(DOI_UNG_SAN),",")))
    print("   KHU HOI = truot gia hai chieu + PHI POOL hai chieu (va 10/09, ca MARIO)")

def khu_hoi(doi_ung,phi_pool=0.0):
    """Phi ra vao that. Day la CUA CHAN, khong phai so tham khao.
    🔴 VA 10/09 (ca MARIO): pool chinh cua no la pool PHI 5% MOI CHIEU. Ban cu chi do
    truot gia -> in ra 0,15% va cho qua cua, trong khi khu hoi that ~10,15%.
    Khu hoi = truot gia di + truot gia ve + phi vao + phi ra."""
    if not doi_ung: return None
    return 4*CO_LENH/doi_ung*100 + 2*(phi_pool or 0.0)

def doc_phi(a):
    """GeckoTerminal: 'pool_fee_percentage' la chuoi phan tram, hoac None voi pool hook cua lo.
    🔴 None KHONG PHAI 0%. Tra ve (so_de_tinh, co_biet_khong)."""
    v=so(a.get("pool_fee_percentage"))
    return (v,True) if v is not None else (0.0,False)

def vung_vao(c):
    """Cua cu quy ra DO. KHONG co so tay nao — xem LUAT.md muc 4.6.
    Doc c['dinh'] va c['day_sau'] do no_va_xep() luu lai. Loi NGUOC khong doc nen
    nen khong co dinh -> in mot dong roi thoi, KHONG bia."""
    P=c.get("gia"); du=c.get("dothat"); dinh=c.get("dinh")
    if not (P and du):   print("   VUNG VAO: ⛔ thieu gia hoac doi ung"); return
    if not dinh:         print("   VUNG VAO: khong ap dung (loi nay khong doc nen)"); return
    n=lambda x:("$%.9f"%x).rstrip("0")
    tran=XEP_TOI*dinh                     # cua 32% dinh, viet bang do
    san =P*(DOI_UNG_SAN/du)**2            # binh phuong: doi ung roi theo CAN BAC HAI cua gia
    kh  =khu_hoi(du,c.get("phi",0.0))     # phi DI VA VE, da gom phi pool
    dat =P*(1+kh/200)                     # truot RIENG chieu mua = mot nua khu hoi
    print("   VUNG DUNG DUOC: %s -> %s"%(n(san),n(tran)))
    print("      tran xep %s = 32%% dinh · san phi %s = noi khu hoi cham 5%%"%(n(tran),n(san)))
    if P>tran:
        print("      🔴 gia nay %s CAO HON tran %.2f lan -> chua xep du, KHONG co gia vao"%(n(P),P/tran))
    elif P<san:
        print("      🔴 gia nay %s THAP HON san %.2f lan -> cua ra da qua dat"%(n(P),san/P))
    else:
        print("      ✅ gia nay %s (%.1f%% dinh) -> GIA DAT LENH: %s"%(n(P),P/dinh*100,n(dat)))
        print("         = gia nay + %.3f%% truot chieu MUA (khu hoi hai chieu %.3f%%, chia doi)"%(kh/2,kh))
    d=c.get("day_sau")
    if d and dinh>d:
        print("      da hoi %.0f%% quang day-sau-dinh -> dinh (0=day, 100=dinh)"%((P-d)/(dinh-d)*100))

def thiep(c):
    """DANH THIEP — chi chay cho con DA QUA HET CUA. 1 cu.
    Cho CON TRO: ten day du, web, X, va DEM DIA CHI TRUNG MA.
    Bai hoc MOO 09/09: con len phieu ngoi canh mot con cung ma to gap 154 lan.
    🔴 KHONG phai cua chan, KHONG cham diem. Y TUONG luon ra ⬜ CHUA KIEM."""
    ok,s,ly=get("https://api.dexscreener.com/latest/dex/search?q=%s"%c["ma"])
    if not ok:
        print("   ⛔ DANH THIEP: %s — LOI GOI, khong phai 'khong co du lieu'"%ly); return
    rows=[p for p in (s.get("pairs") or []) if p.get("chainId")=="robinhood"
          and (p["baseToken"].get("symbol") or "").upper()==c["ma"].upper()]
    minh=[p for p in rows if p["baseToken"]["address"].lower()==c["base"].lower()]
    cas={}
    for p in rows:
        a=p["baseToken"]["address"]
        cas[a]=max(cas.get(a,0.0),float(p.get("marketCap") or p.get("fdv") or 0))
    if minh:
        info=minh[0].get("info") or {}
        web=" · ".join(w.get("url","") for w in (info.get("websites") or []))
        xh =" · ".join(x.get("url","") for x in (info.get("socials")  or []))
        print("   ten day du: %s"%minh[0]["baseToken"].get("name"))
        print("   web: %s"%(web or "khong khai"))
        print("   X:   %s"%(xh  or "khong khai"))
    else:
        print("   ten day du: ⛔ tim theo ma khong thay chinh con nay")
    print("   Y TUONG: ⬜ CHUA KIEM — mo web o tren, MO HET CAC TRANG (ca /treasury, /docs...),")
    print("            tu ghi MOT cau. Cam doan tu cai ten, cam dung o trang chu (ca FAB 09/09).")
    print("   DANH GIA Y TUONG — bat buoc dien du 3 o, xem LUAT.md muc 4.5:")
    print("      bac:      [LOP VO / GHEP LAI CO CHO MOI / TU LAM HA TANG]")
    print("      chep cua: [ten cai goc — hoac 'chua thay cai goc', cam bo trong]")
    print("      phep thu: [cai no khai kiem duoc tren chuoi bang gi]")
    print("      🔴 bac KHONG doi co lenh, KHONG doi cua, KHONG doi moc ban.")
    if len(cas)<=1:
        print("   dia chi cung ma tren chuoi nay: 1")
    else:
        a,mc=sorted(cas.items(),key=lambda kv:-kv[1])[0]
        print("   🔴 %d DIA CHI CUNG MA tren chuoi nay (%d pool). To nhat %s von hoa $%s"%(
              len(cas),len(rows),a,format(int(mc),",")))
        print("      /search cat o 50 ket qua nen day la SAN, khong phai tran.")
        print("      🔴 /search tra VON HOA LON NHAT trong moi pool -> pool bui thoi so len")
        print("         (ca CRUMBS 09/09: $4.020.453 o /search, pool chinh that $324.227).")
        print("      🔴 SO DIA CHI DU 42 KY TU, cam so duoi (ca STREAM `f94c` · CRUMBS `9136`")
        print("         · MARIO `420c` — ba ca trong hai ngay).")

def get(url,timeout=20):
    CU[0]+=1
    try:
        hd={"User-Agent":UA,"Accept":"application/json, text/plain, */*",
            "Accept-Language":"en-US,en;q=0.9"}
        # 🔴 Blockscout tra 403 neu THIEU Referer — do that 08/09, ca UA day du van bi.
        # Thieu dong nay thi CA HAI CUA NANG hong im lang. Xem HATANG.md muc 7.
        if "blockscout" in url: hd["Referer"]=BS+"/"
        req=urllib.request.Request(url,headers=hd)
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return True,json.loads(r.read().decode()),""
    except urllib.error.HTTPError as e: return False,None,"HTTP %d"%e.code
    except Exception as e: return False,None,"%s: %s"%(type(e).__name__,e)

def get_lai(url):
    """429 la LOI GOI. Nghi roi thu lai. Cam doc thanh ket qua rong."""
    ok,j,ly=get(url)
    if not ok and "429" in ly:
        time.sleep(15); ok,j,ly=get(url)
    return ok,j,ly

def post(url,payload,timeout=25):
    CU[0]+=1
    try:
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),
            headers={"Content-Type":"application/json","User-Agent":UA,"Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return True,json.loads(r.read().decode()),""
    except urllib.error.HTTPError as e: return False,None,"HTTP %d"%e.code
    except Exception as e: return False,None,"%s: %s"%(type(e).__name__,e)

def rpc(batch,retry=3):
    for k in range(retry):
        ok,d,ly=post(RPC,batch)
        if ok: return True,d,""
        if "429" not in ly: return False,None,ly
        time.sleep(15)
    return False,None,"429 sau %d lan"%retry

def so(x):
    try: return float(x)
    except (TypeError,ValueError): return None

def dia_chi(rel,ten):
    try: return rel[ten]["data"]["id"].split("_",1)[1].lower()
    except Exception: return None

# ---------- 1. FEED — chung ----------
def feed():
    pools={}; hong=0; loi=[]
    for sort in ("h24_volume_usd_desc","h24_tx_count_desc"):
        for pg in range(1,TRANG+1):
            ok,j,ly=get_lai("%s?sort=%s&page=%d"%(GT,sort,pg))
            if not ok:
                hong+=1; loi.append("%s trang %d: %s"%(sort,pg,ly)); time.sleep(GIAN); continue
            for p in j.get("data",[]): pools[p["attributes"]["address"]]=p
            time.sleep(GIAN)
    return pools,hong,loi

def chung(addr,p):
    """Phan chung cua moi ung vien. None = truot cua chung."""
    a=p["attributes"]; rel=p.get("relationships") or {}
    mc =so(a.get("market_cap_usd")) or so(a.get("fdv_usd"))
    res=so(a.get("reserve_in_usd"))
    ten=(a.get("name") or "").split("/")[0].strip()
    if mc is None or res is None: return None
    if ten.upper() in CO_PHIEU:   return None
    if not (MC_MIN<=mc<=MC_MAX):  return None
    if res < RESERVE_SO:          return None
    phi,biet=doc_phi(a)
    pc=a.get("price_change_percentage") or {}; vol=a.get("volume_usd") or {}
    return {"pool":addr,"ma":ten,"mc":mc,"res":res,"phi":phi,"biet_phi":biet,
            "h1":so(pc.get("h1")),"h24":so(pc.get("h24")),
            "v1":so(vol.get("h1")) or 0,"vol":so(vol.get("h24")) or 0,
            "base":dia_chi(rel,"base_token"),"quote":dia_chi(rel,"quote_token"),
            "gia":so(a.get("base_token_price_usd")),
            "cap":(a.get("name") or "/").split("/")[-1].strip(),
            "tao":a.get("pool_created_at")}

# ---------- 2A. CHIEU LOI NGUOC ----------
def sang_nguoc(pools):
    ra=[]
    for addr,p in pools.items():
        c=chung(addr,p)
        if not c or c["h24"] is None or not c["tao"]: continue
        # calendar.timegm doc dung UTC. time.mktime doc theo gio may -> SAI.
        tuoi=(time.time()-calendar.timegm(time.strptime(c["tao"][:19],"%Y-%m-%dT%H:%M:%S")))/3600
        if tuoi < TUOI_MIN_H:                continue
        if not (GIA_MIN<=c["h24"]<=GIA_MAX): continue
        c["tuoi"]=tuoi; ra.append(c)
    return ra

# ---------- 2B. CHIEU LOI NO LAI ----------
def sang_nolai(pools):
    ra=[]
    for addr,p in pools.items():
        c=chung(addr,p)
        if not c or c["h1"] is None: continue
        if c["h1"] < NHIP_H1: continue        # dang co nhip len lai
        ra.append(c)
    return ra

def no_va_xep(cands):
    """Doc nen: da tung tang chua, da xep chua. Moi con 1 cu."""
    qua=[]
    for c in cands:
        c["no_lan"]=None; c["xep"]=None; c["gio_tu_dinh"]=0; c["ly_nen"]=""
        ok,j,ly=get_lai("%s/%s/ohlcv/hour?aggregate=1&limit=%d"%(GT,c["pool"],CUA_SO_NEN))
        time.sleep(GIAN)
        if not ok: c["ly_nen"]="LOI GOI: "+ly; continue
        ol=(((j.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
        if len(ol)<6: c["ly_nen"]="chi co %d cay nen"%len(ol); continue
        n=sorted(ol,key=lambda x:int(x[0]))
        hi=[float(x[2]) for x in n]; lo=[float(x[3]) for x in n]
        i=max(range(len(hi)),key=lambda k:hi[k]); dinh=hi[i]
        day=min(lo[:i+1]) if i>0 else lo[0]
        if day<=0 or dinh<=0: c["ly_nen"]="nen co gia 0"; continue
        c["no_lan"]=dinh/day; c["xep"]=float(n[-1][4])/dinh
        c["dinh"]=dinh; c["day_sau"]=min(lo[i:])      # cho vung_vao(), 0 cu goi them
        c["gio_tu_dinh"]=(int(n[-1][0])-int(n[i][0]))/3600
        if c["no_lan"]>=NO_LAN and c["xep"]<=XEP_TOI: qua.append(c)
    return qua

def gop4(n1):
    """Gop nen 1h -> 4h TRONG CODE. Goi rieng aggregate=4 lam 429 hang loat (do 08/09)."""
    o=[]
    for i in range(0,len(n1)-len(n1)%4,4):
        b=n1[i:i+4]
        o.append([int(b[0][0]),max(float(x[2]) for x in b),
                  min(float(x[3]) for x in b),float(b[-1][4])])
    return o

# ---------- GIAI DOAN 1 ----------
def loc_tho(pools):
    ra=[]
    for a,p in pools.items():
        at=p["attributes"]; rel=p.get("relationships") or {}
        mc=so(at.get("market_cap_usd")) or so(at.get("fdv_usd")); res=so(at.get("reserve_in_usd"))
        ten=(at.get("name") or "").split("/")[0].strip()
        if mc is None or res is None: continue
        if ten.upper() in CO_PHIEU: continue
        if not (MC_MIN<=mc<=DP_MC_MAX): continue
        if res<DP_RES_SO: continue
        phi,biet=doc_phi(at)
        ra.append({"pool":a,"ma":ten,"mc":mc,"res":res,"phi":phi,"biet_phi":biet,
                   "base":dia_chi(rel,"base_token"),"quote":dia_chi(rel,"quote_token"),
                   "gia":so(at.get("base_token_price_usd")),
                   "cap":(at.get("name") or "/").split("/")[-1].strip()})
    return ra

def doc_nen(c):
    """MOT cu goi cho moi con. Tra ve None neu khong doc duoc."""
    ok,j,ly=get_lai("%s/%s/ohlcv/hour?aggregate=1&limit=1000"%(GT,c["pool"]))
    time.sleep(GIAN)
    if not ok: c["ly_nen"]="LOI GOI: "+ly; return None
    o=(((j.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
    n1=sorted(o,key=lambda x:int(x[0]))
    if len(n1)<DP_NEN_MIN:
        c["ly_nen"]="chi %d cay nen 1h (can >=%d, pool qua non)"%(len(n1),DP_NEN_MIN); return None
    n4=gop4(n1)
    hi=[x[1] for x in n4]; lo=[x[2] for x in n4]
    i=max(range(len(hi)),key=lambda k:hi[k]); dinh=hi[i]
    day=min(lo[:i+1]) if i>0 else lo[0]
    if day<=0 or dinh<=0: c["ly_nen"]="nen co gia 0"; return None
    d24=n1[-24:]
    dong=[float(x[4]) for x in d24]; tv=st.median(dong)
    c["so_nen"]=len(n1); c["no_lan"]=dinh/day
    c["xep_tv"]=tv/dinh; c["xep_nay"]=dong[-1]/dinh
    c["gio_sat"]=sum(1 for x in dong if abs(x/tv-1)<=DP_DAI_SAT) if tv else 0
    c["gio_tu_dinh"]=(n4[-1][0]-n4[i][0])/3600
    v=[float(x[5]) for x in d24]
    c["vol_nen"]=st.median(v[:-1]); c["vol_1h"]=v[-1]
    c["vol_lan"]=(v[-1]/c["vol_nen"]) if c["vol_nen"]>0 else None
    c["gia_1h"]=(dong[-1]/dong[-2]-1)*100 if len(dong)>1 and dong[-2] else None
    c["ly_nen"]=""
    # KHONG luu c["dinh"] o day: dinh nay tinh tren nen 4 gio, tron voi vung_vao()
    # (dung nen 1 gio) la tron hai loai nen — LUAT.md 4.6 ghi ro chua ap cho loi nay.
    return c

def ghi_so_do(rows):
    """CO CHE TU CAI THIEN: moi luot quet ghi so do cua MOI con doc duoc nen.
    Khong can Bean lam gi. Du 30 dong la chot duoc nguong buoc 3."""
    moi = not os.path.exists(DP_SODO)
    with open(DP_SODO,"a",encoding="utf-8") as f:
        if moi:
            f.write("# SO DO TICH LUY — loi DAY PHANG\n\n")
            f.write("> Script tu ghi moi luot quet. Muc dich: gom du 30 con de chot nguong buoc 3\n")
            f.write("> (gio nam sat trung vi) va buoc 7 (khoi luong). CAM sua tay.\n")
            f.write("> Du 30 dong -> quet do nhay 12/14/16/18/20 gio, roi sua LUAT.md muc 2.3.\n\n")
            f.write("| gio do UTC | ma | dia chi | so nen | da no | gia/dinh | gio sat TV | h tu dinh | vol 1h/nen | von hoa |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        g=time.strftime("%Y-%m-%d %H:%M",time.gmtime())
        for c in rows:
            f.write("| %s | %s | `%s` | %d | %.1fx | %.1f%% | **%d/24** | %.0fh | %s | $%s |\n"%(
                g,c["ma"],c["base"] or "?",c["so_nen"],c["no_lan"],c["xep_tv"]*100,
                c["gio_sat"],c["gio_tu_dinh"],
                ("%.1fx"%c["vol_lan"]) if c["vol_lan"] else "—",
                format(int(c["mc"]),",")))
    return len(rows)

# ---------- 3. DOI UNG THAT tu log Swap — chung ----------
def doi_ung_that(cands):
    ok,d,ly=rpc([{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}])
    if not ok: return "RPC CHET: "+ly
    H=int(d[0]["result"],16); last={}; hong={}
    def keo(lo,span,sau=0):
        ok,d,ly=rpc([{"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[
            {"address":PM,"topics":[SWAP,lo],"fromBlock":hex(H-span),"toBlock":hex(H)}]}])
        loi=ly if not ok else (d[0].get("error",{}) or {}).get("message","")
        if not loi:
            for l in d[0]["result"]:
                p=l["topics"][1]; b=int(l["blockNumber"],16)
                if b>=last.get(p,(0,))[0]:
                    dt=l["data"][2:]
                    o=[int(dt[j:j+64],16) for j in range(0,len(dt),64)]
                    last[p]=(b,o[2],o[3])
            return True
        if len(lo)>1 and sau<3:
            time.sleep(1.0); g=len(lo)//2
            a1=keo(lo[:g],span,sau+1); time.sleep(1.0); a2=keo(lo[g:],span,sau+1)
            return a1 and a2
        for p in lo: hong[p]=loi
        return False
    # Chi pool V4 (id 66 ky tu) moi loc duoc bang topics. Pool 42 ky tu -> ⛔, cam tron vao lo.
    v4=[c["pool"] for c in cands if len(c["pool"])==66]
    for c in cands:
        if len(c["pool"])!=66: hong[c["pool"]]="pool khong phai V4 (id %d ky tu)"%len(c["pool"])
    for i in range(0,len(v4),LO_POOL):
        keo(v4[i:i+LO_POOL],6000); time.sleep(1.0)
    # LUOT VET: pool nao chua thay Swap thi nhin lui rong hon truoc khi ghi ⛔.
    # Chi them co hoi do, KHONG doi bat ky nguong san nao.
    thieu=[p for p in v4 if p not in last]
    if thieu:
        print("   luot vet: %d pool chua thay Swap trong 6.000 khoi -> nhin lui %s khoi"%(
              len(thieu),format(DAI_VET,",")))
        for i in range(0,len(thieu),LO_VET):
            keo(thieu[i:i+LO_VET],DAI_VET); time.sleep(1.0)
        con=[p for p in thieu if p not in last]
        print("   luot vet xong: do them duoc %d, con lai %d"%(len(thieu)-len(con),len(con)))
    for c in cands:
        c["dothat"]=None; c["ly_do"]=""
        if not c["base"] or not c["quote"]: c["ly_do"]="thieu dia chi token"; continue
        if c["pool"] not in last:
            c["ly_do"]=("LOI GOI: "+hong[c["pool"]]) if c["pool"] in hong \
                       else "khong co Swap trong %s khoi gan nhat (da chay luot vet)"%format(DAI_VET,",")
            continue
        if not c["gia"]: c["ly_do"]="khong co gia USD"; continue
        b,sq,L=last[c["pool"]]; sqrtP=sq/(2**96)
        if sqrtP==0: c["ly_do"]="sqrtPriceX96 = 0"; continue
        # V4 xep currency0 < currency1 theo GIA TRI SO cua dia chi. Xac dinh bang du kien.
        base_la_c0=int(c["base"],16)<int(c["quote"],16)
        tok=(L/sqrtP) if base_la_c0 else (L*sqrtP)
        v=tok/1e18*c["gia"]
        # PHEP THU LAM SAI: doi ung khong the lon hon tong pool, cung khong the ~0.
        if v>c["res"] or v<100:
            c["ly_do"]="tinh ra $%s — vo ly so voi tong pool $%s, pool thanh khoan co cum"%(
                format(int(v),","),format(int(c["res"]),","))
            continue
        c["dothat"]=v
    return None

# ---------- 3B. HAI CUA NANG: ai rut duoc pool + vi nguoi to nhat ----------
def cua_nguoi_giu(ca,lan=5):
    """Tra ve dict. ra['loi'] khac None = KHONG DO DUOC — khac han do ra so xau."""
    ra={"loi":None,"khoa":None,"vi_to":None,"top10":None}
    h=None
    for k in range(lan):
        ok,j,ly=get("%s/api/v2/tokens/%s/holders"%(BS,ca))
        if ok and "items" in j: h=j; break
        time.sleep(3)
    if not h:
        ra["loi"]="bang nguoi giu hong sau %d lan (Blockscout hay tra 500)"%lan; return ra
    ok,d,ly=rpc([{"jsonrpc":"2.0","id":1,"method":"eth_call",
                  "params":[{"to":ca,"data":"0x18160ddd"},"latest"]}])
    if not ok: ra["loi"]="khong doc duoc totalSupply: "+ly; return ra
    try: TS=int(d[0]["result"],16)
    except Exception: ra["loi"]="totalSupply tra ve rong"; return ra
    if TS<=0: ra["loi"]="totalSupply = 0"; return ra
    items=h["items"][:25]; addrs=[i["address"]["hash"].lower() for i in items]
    ok,c,ly=rpc([{"jsonrpc":"2.0","id":n,"method":"eth_getCode","params":[a,"latest"]}
                 for n,a in enumerate(addrs)])
    if not ok: ra["loi"]="eth_getCode hong: "+ly; return ra
    code={addrs[r["id"]]:r["result"] for r in c}
    nguoi=[]
    for i in items:
        a=i["address"]["hash"].lower(); pct=int(i["value"])/TS*100
        if a in KHOA:
            if not ra["khoa"]: ra["khoa"]=(KHOA[a],pct)
            continue
        if a in HATANG: continue
        cd=code.get(a,"?")
        # 0xef0100... la vi nguoi EIP-7702, KHONG phai hop dong (HATANG.md muc 10, bay so 3)
        if cd=="0x" or cd.startswith("0xef0100"): nguoi.append(pct)
    if not nguoi: ra["loi"]="khong con vi nguoi nao sau khi loc ha tang"; return ra
    ra["vi_to"]=max(nguoi); ra["top10"]=sum(sorted(nguoi,reverse=True)[:10])
    return ra

def doc_cua(r):
    if r["loi"]: return "⛔ CHUA DO DUOC: "+r["loi"]
    k=("khoa %s giu %.2f%% cung -> KHONG rut duoc pool chinh"%r["khoa"]) if r["khoa"] \
      else "KHONG THAY locker nao trong top -> coi nhu RUT DUOC"
    return "%s · vi to nhat %.2f%% (cua %.0f%%) · top10 %.2f%% (cua %.0f%%)"%(
        k,r["vi_to"],VI_TO_MAX,r["top10"],TOP10_MAX)

def qua_cua_nang(r):
    return (r["loi"] is None and r["khoa"] is not None
            and r["vi_to"]<=VI_TO_MAX and r["top10"]<=TOP10_MAX)

def in_phi(c):
    """In phi pool ra phieu. `?` = GT khong khai, KHONG phai 0%."""
    return ("phi pool %.3f%%/chieu"%c["phi"]) if c.get("biet_phi") else "phi pool ? (GT khong khai)"

# ---------- 4. SO DA BAO — chung, tach theo cot loi ----------
def doc_da_bao(path,loi="NGUOC"):
    cu={}
    if path and os.path.exists(path):
        for dong in open(path,encoding="utf-8"):
            dong=dong.strip()
            if not dong or dong.startswith("#"): continue
            ph=[x.strip() for x in dong.split("|")]
            if len(ph)<2: continue
            if (ph[3].upper() if len(ph)>=4 else "NGUOC")!=loi: continue   # lo loi khac khong chan
            try: cu[ph[0].lower()]=calendar.timegm(time.strptime(ph[1][:19],"%Y-%m-%dT%H:%M:%S"))
            except Exception: pass
    return cu


# ---------- LOI DAY PHANG: ba buoc, dung chung moi ham o tren ----------
def dp_feed():
    in_nguong()
    pools,hong,loi_feed=feed()
    print("LOI DAY PHANG · %s"%time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime()))
    print("feed: %d pool · %d trang loi"%(len(pools),hong))
    if hong>8: print("FEED HONG — hon 8 trang loi. KHONG KET LUAN."); return
    if not pools: print("FEED HONG — 0 pool. LOI GOI, khong phai 'khong co du lieu'."); return
    cands=loc_tho(pools)
    print("qua loc tho (mc %s-%s · reserve>=%s): %d"%(
        format(MC_MIN,","),format(DP_MC_MAX,","),format(DP_RES_SO,","),len(cands)))
    json.dump(cands,open(DP_CANDS,"w"))
    if os.path.exists(DP_STATE): os.remove(DP_STATE)
    print("da luu -> chay tiep: python3 SAN.py dayphang-nen 0 17")
    print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0))

def dp_nen(tu,den):
    cands=json.load(open(DP_CANDS))[tu:den]
    doc=[]; non=0; loi_nen=0
    for c in cands:
        if doc_nen(c): doc.append(c)
        elif "qua non" in c.get("ly_nen",""): non+=1
        else: loi_nen+=1
    print("doc duoc nen: %d · pool qua non (<%d nen): %d · loi goi: %d"%(
        len(doc),DP_NEN_MIN,non,loi_nen))
    if doc: print("da ghi %d dong vao %s (co che tu cai thien)"%(ghi_so_do(doc),DP_SODO))
    qua=[c for c in doc if c["no_lan"]>=DP_NO_LAN and c["xep_tv"]<=DP_XEP_TOI
                        and c["gio_sat"]>=DP_GIO_SAT]
    print("qua no>=%.0fx VA xep<=%.0f%% VA nam im>=%d/24: %d"%(
        DP_NO_LAN,DP_XEP_TOI*100,DP_GIO_SAT,len(qua)))
    cu={"qua":[],"doc":[]}
    if os.path.exists(DP_STATE): cu=json.load(open(DP_STATE))
    json.dump({"qua":cu["qua"]+qua,"doc":cu["doc"]+doc},open(DP_STATE,"w"))
    print("\n%-12s %8s %9s %10s %9s"%("MA","da no","gia/dinh","gio sat TV","vol 1h/nen"))
    for c in sorted(doc,key=lambda x:-x["gio_sat"]):
        print("%-12s %7.1fx %8.1f%% %8d/24 %8s"%(c["ma"],c["no_lan"],c["xep_tv"]*100,
            c["gio_sat"],("%.1fx"%c["vol_lan"]) if c["vol_lan"] else "—"))
    print("\n[%d cu · %.0f giay]"%(CU[0],time.time()-T0))

def dp_phieu(so_da_bao):
    if not os.path.exists(DP_STATE): print("Chua co %s. Chay dayphang-feed roi dayphang-nen."%DP_STATE); return
    cands=json.load(open(DP_STATE))["qua"]
    da_bao=doc_da_bao(so_da_bao,"DAYPHANG")
    in_nguong()
    print("LOI DAY PHANG · phieu · %s"%time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime()))
    if not cands: print("KHONG CO UNG VIEN"); print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0)); return
    err=doi_ung_that(cands)
    if err: print(err); print("KHONG KET LUAN — RPC hong."); return
    nguong=time.time()-GIO_KHONG_BAO_LAI*3600; qua=[]
    for c in sorted(cands,key=lambda x:-(x["dothat"] or 0)):
        kh=khu_hoi(c["dothat"],c.get("phi",0.0)) if c["dothat"] else None
        if c["dothat"] is None: tt="⛔ LOAI: chua do duoc doi ung (%s)"%c["ly_do"]
        elif kh>DP_KHU_HOI:
            tt="LOAI VI PHI: khu hoi $%d = %.2f%% > cua %.2f%%"%(CO_LENH,kh,DP_KHU_HOI)
        elif c["vol_lan"] is None or c["vol_lan"]<DP_VOL_LAN:
            tt="CHUA CO TIN HIEU VAO: khoi luong 1h = %sx nen (cua >=%.0fx)"%(
                ("%.1f"%c["vol_lan"]) if c["vol_lan"] else "?",DP_VOL_LAN)
        elif c["gia_1h"] is not None and c["gia_1h"]<0:
            tt="CHUA CO TIN HIEU VAO: gia 1h %.1f%% (cua: khong am)"%c["gia_1h"]
        elif c["base"] in da_bao and da_bao[c["base"]]>=nguong:
            tt="BO QUA: da bao o loi nay trong %d gio qua"%GIO_KHONG_BAO_LAI
        else:
            r=cua_nguoi_giu(c["base"]); c["cua"]=r; time.sleep(1.0)
            if qua_cua_nang(r): tt="UNG VIEN"; qua.append(c)
            elif r["loi"]:      tt="⛔ LOAI: "+doc_cua(r)
            else:               tt="LOAI VI NGUOI GIU: "+doc_cua(r)
        print("\n%s  %s"%(c["ma"],c["base"]))
        if c["ma"].upper() in CO_PHIEU_NGO:
            print("   ⚠️ MA TRUNG TICKER SAN MY — canh bao, KHONG phai cua chan. Mo ra kiem.")
        print("   da no %.1fx · gia %.1f%% dinh (cua <=%.0f%%) · %.0fh tu dinh"%(
            c["no_lan"],c["xep_tv"]*100,DP_XEP_TOI*100,c["gio_tu_dinh"]))
        print("   NAM IM: %d/24 gio sat trung vi (cua >=%d)"%(c["gio_sat"],DP_GIO_SAT))
        print("   doi ung that: %s (GT bao tong pool $%s) · %s"%(
            ("$"+format(int(c["dothat"]),",")) if c["dothat"] else "CHUA DO DUOC",
            format(int(c["res"]),","),in_phi(c)))
        print("   von hoa $%s · cap %s · pool %s"%(format(int(c["mc"]),","),c["cap"],c["pool"]))
        print("   %s"%tt)
        if tt=="UNG VIEN":
            print("   %s"%doc_cua(c["cua"]))
            print("   khu hoi $%d: %.2f%% / cua %.2f%%  (truot gia + %s)"%(
                  CO_LENH,kh,DP_KHU_HOI,in_phi(c)))
            vung_vao(c)          # loi nay chua co c['dinh'] -> in "khong ap dung", KHONG bia
            thiep(c)
            print("   tin hieu vao: khoi luong 1h = %.1fx nen · gia 1h %+.1f%%"%(
                c["vol_lan"],c["gia_1h"] or 0))
            print("   ⏰ GIO IN PHIEU: %s — vao tien muon hon thi DO LAI truoc"%
                  time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime()))
            print("   DONG DAN VAO SO DA BAO: %s | %s | %s | DAYPHANG"%(
                c["base"],time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),c["ma"]))
    print("\nung vien: %d"%len(qua))
    if not qua: print("KHONG CO UNG VIEN MOI")
    print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0))

# ---------- MAIN ----------
def main():
    loi = (sys.argv[1].upper() if len(sys.argv)>1 else "NGUOC")
    if loi=="DAYPHANG-FEED": return dp_feed()
    if loi=="DAYPHANG-NEN":  return dp_nen(int(sys.argv[2]),int(sys.argv[3]))
    if loi=="DAYPHANG":      return dp_phieu(sys.argv[2] if len(sys.argv)>2 else None)
    if loi not in ("NGUOC","NOLAI"):
        print("Dung: python3 SAN.py [nguoc|nolai|dayphang-feed|dayphang-nen T D|dayphang] [DA-BAO.md]"); return
    so_da_bao = sys.argv[2] if len(sys.argv)>2 else None
    da_bao = doc_da_bao(so_da_bao,loi)
    gio=time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime())

    in_nguong()
    pools,hong,loi_feed=feed()
    print("LOI %s · %s"%(loi,gio))
    print("feed: %d pool doc duoc · %d trang loi"%(len(pools),hong))
    for x in loi_feed: print("   loi feed: "+x)
    if hong>8:
        print("FEED HONG — hon 8 trang loi. KHONG KET LUAN, khong doc thanh 'khong co ung vien'."); return
    if not pools:
        print("FEED HONG — 0 pool doc duoc. Day la LOI GOI, khong phai 'khong co du lieu'."); return

    if loi=="NGUOC":
        cands=sang_nguoc(pools)
        print("qua so bo (tuoi>%.0fh · mc 50K-1,5M · gia24 %.0f%%..%.0f%% · reserve>=%s): %d"%(
            TUOI_MIN_H,GIA_MIN,GIA_MAX,format(RESERVE_SO,","),len(cands)))
    else:
        so_bo=sang_nolai(pools)
        print("qua nhip so bo (mc 50K-1,5M · reserve>=%s · gia 1h>=+%.0f%%): %d"%(
            format(RESERVE_SO,","),NHIP_H1,len(so_bo)))
        cands=no_va_xep(so_bo) if so_bo else []
        for c in so_bo:
            if c["ly_nen"].startswith("LOI GOI"): print("   ⛔ %s: %s"%(c["ma"],c["ly_nen"]))
        print("da tung tang >=%.0fx VA da xep ve <=%.0f%% dinh: %d"%(NO_LAN,XEP_TOI*100,len(cands)))

    if not cands:
        print("KHONG CO UNG VIEN"); print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0)); return

    err=doi_ung_that(cands)
    if err:
        print(err); print("KHONG KET LUAN — RPC hong, khong phai khong co ung vien."); return

    nguong=time.time()-GIO_KHONG_BAO_LAI*3600; qua=[]
    for c in sorted(cands,key=lambda x:-(x["dothat"] or 0)):
        if c["dothat"] is None:
            tt="⛔ LOAI: chua do duoc doi ung (%s)"%c["ly_do"]
        elif khu_hoi(c["dothat"],c.get("phi",0.0))>KHU_HOI_MAX:
            # 🔴 Cua dat tren PHI, khong dat tren doi ung. Xem LUAT.md muc 3.1.
            #    Tu 10/09 khu hoi da gom PHI POOL hai chieu (ca MARIO: pool phi 5%/chieu).
            tt="LOAI VI PHI: khu hoi $%d = %.2f%% > cua %.2f%%  (doi ung $%s · %s)"%(
                CO_LENH,khu_hoi(c["dothat"],c.get("phi",0.0)),KHU_HOI_MAX,
                format(int(c["dothat"]),","),in_phi(c))
        elif c["base"] in da_bao and da_bao[c["base"]]>=nguong:
            tt="BO QUA: da bao o loi nay trong %d gio qua"%GIO_KHONG_BAO_LAI
        else:
            # Hai cua nang. Chi chay cho con da qua phi -> khong ton cu cho con da loai.
            r=cua_nguoi_giu(c["base"]); c["cua"]=r; time.sleep(1.0)
            if qua_cua_nang(r): tt="UNG VIEN"; qua.append(c)
            elif r["loi"]:      tt="⛔ LOAI: "+doc_cua(r)
            else:               tt="LOAI VI NGUOI GIU: "+doc_cua(r)
        print("\n%s  %s"%(c["ma"],c["base"]))
        if c["ma"].upper() in CO_PHIEU_NGO:
            print("   ⚠️ MA TRUNG TICKER SAN MY — canh bao, KHONG phai cua chan. Mo ra kiem.")
        if loi=="NGUOC":
            print("   gia 24h %.1f%% · tuoi pool %.0fh"%(c["h24"],c["tuoi"]))
        else:
            print("   da tang %.1fx · da xep ve %.0f%% dinh · %.0fh tu dinh"%(
                c["no_lan"],c["xep"]*100,c["gio_tu_dinh"]))
            print("   nhip lai: gia 1h %+.1f%% · vol 1h $%s"%(c["h1"],format(int(c["v1"]),",")))
        print("   doi ung that: %s   (GeckoTerminal bao tong pool $%s) · %s"%(
            ("$"+format(int(c["dothat"]),",")) if c["dothat"] else "CHUA DO DUOC",
            format(int(c["res"]),","),in_phi(c)))
        print("   von hoa $%s · cap %s · vol24 $%s"%(
            format(int(c["mc"]),","),c["cap"],format(int(c["vol"]),",")))
        print("   pool %s"%c["pool"])
        print("   %s"%tt)
        if tt=="UNG VIEN":
            print("   %s"%doc_cua(c["cua"]))
            print("   khu hoi $%d: %.2f%% / cua %.2f%%  (truot gia hai chieu + %s)"%(
                  CO_LENH,khu_hoi(c["dothat"],c.get("phi",0.0)),KHU_HOI_MAX,in_phi(c)))
            vung_vao(c)          # LUAT.md muc 4.6 — cua cu quy ra DO, khong co so tay
            thiep(c)
            print("   ⏰ GIO IN PHIEU: %s  — vao tien muon hon thi DO LAI truoc, xu theo so moi"%
                  time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime()))
            print("   DONG DAN VAO SO DA BAO: %s | %s | %s | %s"%(
                c["base"],time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),c["ma"],loi))
    print("\nung vien: %d"%len(qua))
    if not qua: print("KHONG CO UNG VIEN MOI")
    print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0))

main()
