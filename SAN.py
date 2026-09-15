#!/usr/bin/env python3
# SAN GEMS — MOT loi duy nhat, NAM VE. Bean chot 13/09.
#   python3 SAN.py DA-BAO.md
#
# SO VE = THU TU CHAY. Doc tu tren xuong la dung thu tu script lam.
#
# LOC THO           : dai von hoa · doi ung san · loai thang tu ten          (0 cu them)
# VE 1  da rot nat  : gia dong cua nen 1h <= 25% DINH  (dinh = CLOSE cao nhat, KHONG lay rau)
# VE 2  da nam li   : >=20 trong 24 gio gan nhat co close <= nguong do
# VE 3  het tao day : day nua sau >= day nua truoc cua quang nam im
#       -> ba ve tren doc CUNG MOT chuoi nen, 1 cu cho moi con. Truot la dung.
# VE 4  sach nang   : locker · vi to nhat · top10 · GoPlus · khu hoi that    (TON CU)
#       -> chi chay cho con da qua 1-2-3. Qua = DANH SACH THEO DOI, ghi anh chup.
# VE 5  co nguoi vao: so vi giu TANG va doi ung KHONG bi rut, so voi anh chup cu (0 cu them)
#       -> chi cham duoc khi da co anh cu. Qua = UNG VIEN.
#
# 🔑 DANH SACH THEO DOI (qua 1-2-3-4) KHONG PHAI UNG VIEN. Chua co su kien nao xay ra.
# 🔑 FILE NAY LA NGUON DUY NHAT CUA SO. Cac file .md khac chi TRO toi, cam chep lai.
import json,time,calendar,sys,os,urllib.request,urllib.error,statistics as st

UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
GT ="https://api.geckoterminal.com/api/v2/networks/robinhood/pools"
RPC="https://rpc.mainnet.chain.robinhood.com"
BS ="https://robinhoodchain.blockscout.com"
GOPLUS="https://api.gopluslabs.io/api/v1/token_security/4663"  # chain 4663 = Robinhood
PM  ="0x8366a39cc670b4001a1121b8f6a443a643e40951"
SWAP="0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

# ---- CUA AN TOAN (giu nguyen tu v4, KHONG doi mot so nao) ----
MC_MIN,MC_MAX = 50_000, 1_500_000
CO_LENH       = 250
KHU_HOI_MAX   = 5.0         # 🔴 CUA PHI. Ly do day du: LUAT.md muc 3.1
DOI_UNG_SAN   = 4*CO_LENH/(KHU_HOI_MAX/100)      # = 20.000, suy ra, khong go tay
RESERVE_SO    = int(2*DOI_UNG_SAN)               # = 40.000. Loc so bo (reserve = TONG POOL)
GIO_KHONG_BAO_LAI = 48
VI_TO_MAX     = 5.0         # Nguong VUNG duy nhat cua ca he (>40 ca)
TOP10_MAX     = 25.0

# ---- NAM VE CUA LOI DUY NHAT (Bean chot 13/09 — so ve = thu tu chay) ----
XEP_TOI   = 0.25   # VE 1: gia nay <= 25% dinh, tuc da rot >=75%. 25% la MUC SAN:
                   #       rot sau hon thi cang hop. ⬜ CHUA QUET DO NHAY (20/25/30%)
GIO_NAM   = 24     # VE 2: cua so dem, tinh bang gio. 24 la SAN, nam lau hon van tinh.
GIO_CUA   = 20     # VE 2: trong GIO_NAM gio do phai co >=20 gio nam duoi nguong.
                   #       Cho ngoi len toi da 4 gio — thanh khoan mong nhay 30-40% la thuong.
                   #       ⬜ CHUA QUET DO NHAY (18/20/22/24)
NUA_DAY   = 12     # VE 3: chia quang nam im lam hai nua, moi nua NUA_DAY gio.
NEN_MIN   = 48     # can it nhat 48 cay nen 1h moi doc duoc (24 nam im + 24 de dung day)
CUA_SO_NEN= 1000   # 41 ngay. Tran that da do: >=1.000 cay.

# ---- VE 5 — CO NGUOI VAO. Bean chot 13/09 ----
# 🔴 CUA LA DAU, KHONG PHAI MUC. "So vi tang" = tang bat ky bao nhieu. Chua co ca nao
#    de dat mot muc, va dat muc bay gio la bia (KYLUAT.md muc 11). Toc do %/gio duoc IN
#    va GHI SO de sau nay quet do nhay, nhung KHONG tham gia quyet dinh qua/truot.
VE5_CACH_MIN = 1.0    # anh cu gan hon 1 gio -> qua sat, khong cham
VE5_CACH_MAX = 24.0   # anh cu xa hon 24 gio -> khac tap, khong cham (KYLUAT.md muc 4)
THUOC2_SAN   = 0.8    # doi ung / ky vong theo can bac hai. Duoi = CO NGUOI RUT
THUOC2_TRAN  = 1.25   # tren = CO NGUOI BOM. Dai 0,8-1,25 = khong ai dong vao
KQ_MOC       = (6,24,72)   # gio: cham ket qua cho anh cu tai ba moc nay
KQ_LECH      = 0.35        # sai so cho phep quanh moc (35% cua so moc)

VOL_LAN   = 3.0    # ⚠️ KHONG CON LA CUA. Tu 13/09 chi de IN va ghi so.
                   #    Ly do: do 3 luot lien tiep, con tang 470% co vol 0.62x, con sap
                   #    95% cung duoi nen -> thuoc nay khong phan biet duoc (LUAT.md 2.5).
NHIP_CAO  = 1.5    # NHIP LENH: mua/ban >= 1.5 -> "nhieu lenh nho bat day". ⬜ NGUONG TAM,
NHIP_THAP = 0.67   #   chua quet do nhay. CHI DE IN RA, TUYET DOI KHONG LAM CUA CHAN.
                   #   Ly do: do tren 11 con 13/09 thi ty le cao di kem gia SAP (LUAT.md 7.4).
SO_ANH    = "DO-DEM.md"     # so anh chup — script tu ghi, CAM sua tay

TRANG=10; LO_POOL=12
GIAN = 3.5 if os.environ.get("GITHUB_ACTIONS") else 2.2
DAI_VET=60000; LO_VET=6

# 🔴 NGUON DUY NHAT. Locker da doc ma -> co mat trong bang nguoi giu = pool chinh khoa vinh vien.
KHOA={"0x267444d099b10fb5ed7c3cc7b7c767adca574952":"PonsV2LaunchLocker",
      "0x736d76699c26d0d966744cae304c000d471f7f35":"Locker Pons V3",
      "0x31ca5e101941a93a7dd6d0497928700625cf54b5":"Locker Pons legacy",
      "0x7f03effbd7ceb22a3f80dd468f67ef27826acd85":"LaunchLocker meow",
      "0xba2f330edb16cd8056f5988d8ce19bbc63475a0e":"NoOpMigrator",
      "0xbe0b139abc90723af76a89d3051f60ba1b64c8d9":"PinkLock02",
      # 🆕 12/09 ca LPAD: locker cua lo launchpad.meme. Da doc ma, 491 dong, da xac minh:
      #    decreaseLiquidity 0 lan · safeTransferFrom 0 · onlyOwner 0 · unlock 0.
      "0xb21bb2473c1523d966337e6a6374a75e4a7181fb":"RevenueEscrowAutoSwapFeeLockerV1843"}
HATANG={"0x8366a39cc670b4001a1121b8f6a443a643e40951":"PoolManager",
        "0xea1cf9606b87773ae96330ee4ca95f6062be81ba":"vi ha tang lo Pons v2",
        "0xf017306a84d1be3a72ae444b303d0c3d92a0d852":"hop dong phat hanh Pons v2",
        "0x3711cea4feade896c913c68f01eda97cb06d1a42":"hop dong phat hanh Pons v2 (ban 2)",
        "0x73991a25c818bf1f1128deaab1492d45638de0d3":"NonfungiblePositionManager v3",
        "0x000000000000000000000000000000000000dead":"vi dot"}

# 🔴 LOAI THANG TU TEN.
# 🆕 v5.1: bat ca MA DON BAY an theo ticker — NVDAx3L · OPENAIx1L · ANTHROPICx1L · TSLA3S...
#    Ca that: NVDAx3L lot qua loc tho ngay 12/09 (ca thu SAU cua lo hong danh sach ten).
#    Chi cat hau to khi PHAN GOC nam trong danh sach -> memecoin that ten dang "MOON2L"
#    KHONG bi loai oan.
import re as _re
_DON_BAY=_re.compile(r"^(.+?)[Xx]?(\d+)[LSls]$")
def goc_ten(t):
    """NVDAx3L -> NVDA · OPENAIx1L -> OPENAI · TSLA3S -> TSLA · MOON -> MOON"""
    m=_DON_BAY.match(t or "")
    return m.group(1) if m else (t or "")

def loai_tu_ten(ten):
    """True = loai thang. Kiem ca ten nguyen lan ten da cat hau to don bay."""
    t=(ten or "").upper()
    return t in CO_PHIEU or goc_ten(t).upper() in CO_PHIEU

def canh_bao_ten(ten):
    """True = in ⚠️, KHONG loai (KYLUAT.md muc 1, ca LUNA9)."""
    t=(ten or "").upper()
    return t in CO_PHIEU_NGO or goc_ten(t).upper() in CO_PHIEU_NGO

CO_PHIEU={"SPY","AAPL","NVDA","GLD","MSFT","AMZN","META","GOOGL","QQQ","TSLA","MSTR","MU",
          "HIMS","LIT","TSM","SPCX","AI","ETH","USDG","QC","BTC","COIN","PLTR","RBLX","HOOD","SOL",
          "RIVN","QUBT","AMD","OPENAI","ANTHROPIC","USO"}
# ⚠️ CANH BAO, KHONG LOAI (KYLUAT.md muc 1, ca LUNA9).
CO_PHIEU_NGO={"INTC","SMH","ASML","QCOM","EWY","SKYHY","COST","GME","AMC","NFLX","DIS","BA","F",
              "GM","UBER","LYFT","SOFI","PYPL","ARM","AVGO","ORCL","CRM","ADBE","IBM","GS","JPM",
              "BAC","WMT","TGT","KO","PEP","MCD","NKE","SBUX","XOM","CVX","PFE","JNJ","UNH","V",
              "MA","T","VZ","CSCO","QS","LCID","NIO","PLUG","RKLB","ACHR","IONQ","RGTI","SMCI"}

T0=time.time(); CU=[0]

def in_nguong():
    """KYLUAT.md muc 14 so 3: script TU IN hang so no dang chay, dong dau moi luot."""
    print("NGUONG DANG CHAY · MOT LOI DUY NHAT, NAM VE (Bean chot 13/09 — so ve = thu tu chay)")
    print("   LOC THO : mc $%s-$%s · reserve >= $%s · loai thang tu ten"%(
          format(MC_MIN,","),format(MC_MAX,","),format(RESERVE_SO,",")))
    print("   VE 1 da rot nat : gia <= %.0f%% dinh (dinh = CLOSE nen 1h cao nhat, KHONG lay rau)"%(
          XEP_TOI*100))
    print("   VE 2 da nam li  : >=%d/%d gio gan nhat co close <= nguong tren"%(GIO_CUA,GIO_NAM))
    print("   VE 3 het tao day: day %d gio sau >= day %d gio truoc"%(NUA_DAY,NUA_DAY))
    print("   VE 4 sach nang  : khu hoi <=%.1f%% (lenh $%d) · locker · vi to nhat <=%.0f%% ·"%(
          KHU_HOI_MAX,CO_LENH,VI_TO_MAX))
    print("                     top10 <=%.0f%% · GoPlus · doi ung san $%s"%(
          TOP10_MAX,format(int(DOI_UNG_SAN),",")))
    print("   VE 5 co nguoi vao: so vi TANG va thuoc 2 >= %.2f, so anh chup cach %.0f-%.0f gio"%(
          THUOC2_SAN,VE5_CACH_MIN,VE5_CACH_MAX))
    print("      🔑 cua ve 5 la DAU, khong phai muc. Toc do %/gio chi de ghi so.")
    print("   KHU HOI = truot gia hai chieu + PHI POOL hai chieu (va 10/09, ca MARIO)")
    print("   KHONG CO MOC BAN. Qua 1-2-3-4 = DANH SACH THEO DOI, chua phai ung vien.")
    print("   SO MO TA, KHONG chan ai: khoi luong 1h/nen · nhip lenh (LUAT.md 2.5 va 7.4)")

def khu_hoi(doi_ung,phi_pool=0.0):
    """Phi ra vao that. CUA CHAN, khong phai so tham khao.
    Khu hoi = truot gia di + truot gia ve + phi vao + phi ra (ca MARIO 10/09)."""
    if not doi_ung: return None
    return 4*CO_LENH/doi_ung*100 + 2*(phi_pool or 0.0)

def doc_phi(a):
    """None KHONG PHAI 0%. Tra ve (so_de_tinh, co_biet_khong)."""
    v=so(a.get("pool_fee_percentage"))
    return (v,True) if v is not None else (0.0,False)

def get(url,timeout=20):
    CU[0]+=1
    try:
        hd={"User-Agent":UA,"Accept":"application/json, text/plain, */*",
            "Accept-Language":"en-US,en;q=0.9"}
        # 🔴 Blockscout tra 403 neu THIEU Referer (do that 08/09). HATANG.md muc 7.
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

# ---------- 1. FEED ----------
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

def loc_tho(pools):
    """Loc bang thu KHONG can goi them cu nao. None = truot."""
    ra=[]
    for addr,p in pools.items():
        a=p["attributes"]; rel=p.get("relationships") or {}
        mc =so(a.get("market_cap_usd")) or so(a.get("fdv_usd"))
        res=so(a.get("reserve_in_usd"))
        ten=(a.get("name") or "").split("/")[0].strip()
        if mc is None or res is None: continue
        if loai_tu_ten(ten):          continue
        if not (MC_MIN<=mc<=MC_MAX):  continue
        if res < RESERVE_SO:          continue
        phi,biet=doc_phi(a)
        vol=a.get("volume_usd") or {}
        ra.append({"pool":addr,"ma":ten,"mc":mc,"res":res,"phi":phi,"biet_phi":biet,
                   "v1":so(vol.get("h1")) or 0,"vol":so(vol.get("h24")) or 0,
                   "tx":(a.get("transactions") or {}),
                   "base":dia_chi(rel,"base_token"),"quote":dia_chi(rel,"quote_token"),
                   "gia":so(a.get("base_token_price_usd")),
                   "gia_quote":so(a.get("quote_token_price_usd")),
                   "cap":(a.get("name") or "/").split("/")[-1].strip(),
                   "tao":a.get("pool_created_at")})
    return ra

# ---------- 2. VE 1-2-3 — doc tren nen 1 gio, MOT cu cho moi con ----------
def ba_ve(c):
    """Tra ve True neu qua CA BA ve doc duoc tu nen. Ve 4 va ve 5 chay sau, o main().
    🔴 DINH = CLOSE cao nhat cua nen 1h, KHONG lay high (rau nen). Bean chot 12/09.
       Ly do: mot cay rau don doc khong phai gia ma thi truong tung chap nhan."""
    c["ve1"]=c["ve2"]=c["ve3"]=False; c["ve4"]=None; c["ve5"]=None; c["ly_nen"]=""
    ok,j,ly=get_lai("%s/%s/ohlcv/hour?aggregate=1&limit=%d"%(GT,c["pool"],CUA_SO_NEN))
    time.sleep(GIAN)
    if not ok: c["ly_nen"]="LOI GOI: "+ly; return False
    o=(((j.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
    n=sorted(o,key=lambda x:int(x[0]))
    c["so_nen"]=len(n)
    if len(n)<NEN_MIN:
        # 🆕 v7.1 (14/09, Bean chot): con non VAN tinh dinh tu so nen it oi no co.
        #   Truoc day return thang -> dong DC trong so chi co gia, khong co 'gia/dinh'
        #   va 'h tu dinh' => khong bao gio tra loi duoc cau "36 hay 48 nen".
        #   🔴 KHONG doi ket qua cham: van return False, con non van KHONG vao hang san.
        if n:
            _d=[float(x[4]) for x in n]; _dinh=max(_d)
            if _dinh>0:
                c["dinh"]=_dinh; c["gia_nen"]=_d[-1]; c["xep"]=_d[-1]/_dinh
                c["gio_tu_dinh"]=(int(n[-1][0])-int(n[_d.index(_dinh)][0]))/3600
        c["ly_nen"]="chi %d cay nen 1h (can >=%d, pool qua non)"%(len(n),NEN_MIN); return False
    dong=[float(x[4]) for x in n]          # CLOSE — dung cho ca dinh, gia nay, va day
    volk=[float(x[5]) for x in n]
    dinh=max(dong)
    if dinh<=0: c["ly_nen"]="nen co gia 0"; return False
    gia=dong[-1]
    nguong=XEP_TOI*dinh
    c["dinh"]=dinh; c["gia_nen"]=gia; c["nguong"]=nguong
    c["xep"]=gia/dinh
    c["gio_tu_dinh"]=(int(n[-1][0])-int(n[dong.index(dinh)][0]))/3600

    # VE 1 — da rot nat
    c["ve1"] = gia<=nguong

    # VE 2 — da nam li: dem trong GIO_NAM gio gan nhat
    cua_so=dong[-GIO_NAM:]
    c["gio_duoi"]=sum(1 for x in cua_so if x<=nguong)
    c["ve2"] = c["gio_duoi"]>=GIO_CUA

    # VE 3 — het tao day: day nua sau >= day nua truoc
    #   Dung CLOSE cho nhat quan voi ve 1 (khong lay rau).
    truoc=dong[-GIO_NAM:-NUA_DAY]; sau=dong[-NUA_DAY:]
    c["day_truoc"]=min(truoc) if truoc else None
    c["day_sau"]  =min(sau)   if sau   else None
    c["ve3"] = (c["day_truoc"] is not None and c["day_sau"] is not None
                and c["day_sau"]>=c["day_truoc"])

    # SO MO TA — khoi luong 1h so voi nen. 🔴 KHONG chan con nao (LUAT.md 2.5).
    nen_vol=volk[-GIO_NAM:-1]
    c["vol_nen"]=st.median(nen_vol) if nen_vol else 0
    c["vol_1h"]=volk[-1]
    c["vol_lan"]=(volk[-1]/c["vol_nen"]) if c["vol_nen"]>0 else None

    c["ly_nen"]=""
    return c["ve1"] and c["ve2"] and c["ve3"]

def in_ba_ve(c):
    d=lambda b:"✅" if b else "🔴"
    n=lambda x:("$%.9f"%x).rstrip("0")
    print("   VE 1 %s da rot nat : gia %s = %.1f%% dinh %s (cua <=%.0f%%) · dinh %s · %.0fh tu dinh"%(
          d(c["ve1"]),n(c["gia_nen"]),c["xep"]*100,"" if c["ve1"] else "CHUA DU",
          XEP_TOI*100,n(c["dinh"]),c["gio_tu_dinh"]))
    print("   VE 2 %s da nam li  : %d/%d gio nam duoi %s (cua >=%d)"%(
          d(c["ve2"]),c["gio_duoi"],GIO_NAM,n(c["nguong"]),GIO_CUA))
    print("   VE 3 %s het tao day: day %dh sau %s / day %dh truoc %s"%(
          d(c["ve3"]),NUA_DAY,n(c["day_sau"] or 0),NUA_DAY,n(c["day_truoc"] or 0)))
    print("   KHOI LUONG (mo ta, KHONG phai cua chan): 1h = %s nen · $%s / nen $%s"%(
          ("%.1fx"%c["vol_lan"]) if c.get("vol_lan") else "?",
          format(int(c.get("vol_1h") or 0),","),format(int(c.get("vol_nen") or 0),",")))
    t1,v1,l1,nhan1 = nhip_lenh(c,"h1")
    t24,v24,l24,_  = nhip_lenh(c,"h24")
    print("   NHIP LENH (mo ta, KHONG phai cua chan)")
    print("      mua/ban  h1 %s · h24 %s   -> %s"%(
          ("%.2f"%t1) if t1 is not None else "—",
          ("%.2f"%t24) if t24 is not None else "—", nhan1))
    print("      vi mua/vi ban h1 %s · lenh tren moi vi %s%s"%(
          ("%.2f"%v1) if v1 is not None else "—",
          ("%.1f"%l1) if l1 is not None else "—",
          "  (cao = may chay vong)" if (l1 or 0)>=4 else ""))
    print("      🔴 Ty le cao KHONG co nghia gia se len — xem LUAT.md 7.4")

# ---------- 3. DOI UNG THAT ----------
def doi_ung_v4(cands):
    """Doc tu log Swap. CHI pool V4 (id 66 ky tu)."""
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
    v4=[c["pool"] for c in cands if len(c["pool"])==66]
    for i in range(0,len(v4),LO_POOL):
        keo(v4[i:i+LO_POOL],6000); time.sleep(1.0)
    thieu=[p for p in v4 if p not in last]
    if thieu:
        print("   luot vet: %d pool chua thay Swap trong 6.000 khoi -> nhin lui %s khoi"%(
              len(thieu),format(DAI_VET,",")))
        for i in range(0,len(thieu),LO_VET):
            keo(thieu[i:i+LO_VET],DAI_VET); time.sleep(1.0)
    for c in cands:
        if len(c["pool"])!=66: continue
        c["dothat"]=None; c["ly_do"]=""
        if not c["base"] or not c["quote"]: c["ly_do"]="thieu dia chi token"; continue
        if c["pool"] not in last:
            c["ly_do"]=("LOI GOI: "+hong[c["pool"]]) if c["pool"] in hong \
                       else "khong co Swap trong %s khoi gan nhat (da chay luot vet)"%format(DAI_VET,",")
            continue
        if not c["gia"]: c["ly_do"]="khong co gia USD"; continue
        b,sq,L=last[c["pool"]]; sqrtP=sq/(2**96)
        if sqrtP==0: c["ly_do"]="sqrtPriceX96 = 0"; continue
        base_la_c0=int(c["base"],16)<int(c["quote"],16)
        tok=(L/sqrtP) if base_la_c0 else (L*sqrtP)
        v=tok/1e18*c["gia"]
        if v>c["res"] or v<100:
            c["ly_do"]="tinh ra $%s — vo ly so voi tong pool $%s, pool thanh khoan co cum"%(
                format(int(v),","),format(int(c["res"]),","))
            continue
        c["dothat"]=v
    return None

def doi_ung_v3(cands):
    """🆕 v5: POOL V3 (id 42 ky tu) — doc THANG balanceOf cua token doi ung TAI dia chi pool.
    Truoc v5, moi pool 42 ky tu deu bi ghi ⛔ 'khong phai V4' -> 36% feed bi vut vi CONG CU,
    khong phai vi con xau (ca LPAD 12/09).
    🔴 So nay la BAO THU: balanceOf gom ca phan ngoai dai gia hien tai. Do that ca LPAD:
       balanceOf $46.257 so voi L/sqrtP $50.786 — balanceOf THAP hon 9,8%, tuc CHAT hon."""
    v3=[c for c in cands if len(c["pool"])==42]
    if not v3: return
    pad=lambda a:"000000000000000000000000"+a[2:].lower()
    for i in range(0,len(v3),20):
        lo=v3[i:i+20]
        req=[]
        for k,c in enumerate(lo):
            if not c.get("quote"): continue
            req.append({"jsonrpc":"2.0","id":k,"method":"eth_call",
                        "params":[{"to":c["quote"],"data":"0x70a08231"+pad(c["pool"])},"latest"]})
        if not req: continue
        ok,d,ly=rpc(req)
        if not ok:
            for c in lo: c["dothat"]=None; c["ly_do"]="LOI GOI (balanceOf V3): "+ly
            continue
        m={r["id"]:r.get("result") for r in d}
        for k,c in enumerate(lo):
            c["dothat"]=None; c["ly_do"]=""
            r=m.get(k)
            if not r or len(r)<3: c["ly_do"]="balanceOf tra rong"; continue
            if not c.get("gia_quote"): c["ly_do"]="khong co gia token doi ung"; continue
            try: bal=int(r,16)/1e18
            except Exception: c["ly_do"]="balanceOf khong doc duoc"; continue
            v=bal*c["gia_quote"]
            if v>c["res"]*1.05 or v<100:
                c["ly_do"]="tinh ra $%s — vo ly so voi tong pool $%s"%(
                    format(int(v),","),format(int(c["res"]),","))
                continue
            c["dothat"]=v
        time.sleep(1.0)

def doi_ung_that(cands):
    err=doi_ung_v4(cands)
    if err: return err
    doi_ung_v3(cands)
    for c in cands:
        if "dothat" not in c:
            c["dothat"]=None; c["ly_do"]="pool id %d ky tu — khong phai V4 cung khong phai V3"%len(c["pool"])
    return None

# ---------- 3b. GOPLUS — quet ma hop dong (them 13/09) ----------
#  🔴 KY LUAT DOC: O TRONG LA "KHONG BIET", KHONG PHAI "AN TOAN" (KYLUAT.md rang buoc 1).
#     Loi goi -> ⛔ ghi ro, KHONG chan con nao. Chi chan khi co GIA TRI RO RANG.
GP_CHAN  = {"is_honeypot":"1","cannot_sell_all":"1","is_open_source":"0"}
GP_CANH  = ["transfer_pausable","is_blacklisted","owner_change_balance",
            "hidden_owner","can_take_back_ownership","is_mintable","selfdestruct"]

def goplus(dia_chis):
    """MOT cu cho ca lo (<=20 dia chi). Tra ve {dia_chi_thuong: dict} — thieu con nao
    nghia la GoPlus khong co du lieu con do, KHONG phai con do sach."""
    ra={}
    if not dia_chis: return ra
    for i in range(0,len(dia_chis),20):
        lo=[a for a in dia_chis[i:i+20] if a]
        if not lo: continue
        ok,j,ly=get_lai("%s?contract_addresses=%s"%(GOPLUS,",".join(lo)))
        if not ok:
            print("   ⛔ GoPlus LOI GOI: %s — KHONG doc thanh 'sach'"%ly); continue
        for k,v in (j.get("result") or {}).items():
            ra[k.lower()]=v
        time.sleep(1.0)
    return ra

def doc_goplus(g):
    """Tra ve (chan_hay_khong, dong_in)."""
    if g is None:
        return False,"   GOPLUS: ⛔ khong co du lieu con nay — KHONG BIET, khong phai sach"
    xau=[k for k,v in GP_CHAN.items() if str(g.get(k,"")).strip()==v]
    canh=[k for k in GP_CANH if str(g.get(k,"")).strip()=="1"]
    bt=str(g.get("buy_tax","")).strip(); st=str(g.get("sell_tax","")).strip()
    thue=("thue mua %s · thue ban %s"%(bt or "?",st or "?")) if (bt or st) else "thue: khong khai"
    dong="   GOPLUS: ma %s · %s%s"%(
        "MO" if str(g.get("is_open_source","")).strip()=="1" else
        ("DONG 🔴" if str(g.get("is_open_source","")).strip()=="0" else "? khong khai"),
        thue,
        ("  ⚠️ "+" · ".join(canh)) if canh else "")
    if xau: dong+="\n   🔴 GOPLUS CHAN: "+" · ".join(xau)
    return bool(xau),dong

# ---------- 4. HAI CUA NANG ----------
def cua_nguoi_giu(ca,lan=5):
    """ra['loi'] khac None = KHONG DO DUOC — khac han do ra so xau.
    🆕 v5 tra them 'so_vi' de ghi vao so anh chup."""
    ra={"loi":None,"khoa":None,"vi_to":None,"top10":None,"so_vi":None}
    h=None
    for k in range(lan):
        ok,j,ly=get("%s/api/v2/tokens/%s/holders"%(BS,ca))
        if ok and "items" in j: h=j; break
        time.sleep(3)
    if not h:
        ra["loi"]="bang nguoi giu hong sau %d lan (Blockscout hay tra 500)"%lan; return ra
    ok,j2,_=get("%s/api/v2/tokens/%s/counters"%(BS,ca))
    if ok: ra["so_vi"]=so(j2.get("token_holders_count"))
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
        # 0xef0100... la vi nguoi EIP-7702 (HATANG.md muc 10, bay so 3)
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
    return ("phi pool %.3f%%/chieu"%c["phi"]) if c.get("biet_phi") else "phi pool ? (GT khong khai)"

# ---------- 5. SO ANH CHUP — de LUOT SAU so duoc ----------
def _so_o(x):
    """Doc mot o trong bang. Tra None cho o trong, cho '—' va cho '?'."""
    x=(x or "").strip().replace("$","").replace(",","").replace("%","")
    if x in ("","—","?","-"): return None
    try: return float(x)
    except Exception: return None

def doc_anh_cu(path=SO_ANH):
    """🆕 v5, Bean chot 12/09: khong dung lai qua khu tu log (⛔ qua dat).
    Thay vao do: MOI luot ghi anh chup, luot sau doc anh cu ra ma so.

    Tra ve (gan_nhat, tat_ca):
      gan_nhat {dia_chi: anh}          — de VE 5 so
      tat_ca   {dia_chi: [anh, ...]}   — de cham ket qua 6/24/72 gio
    Moi 'anh' la dict {gio, vi, doi_ung, mc, gia, ma}.

    🔴 HAI THOI KY TRONG CUNG MOT BANG. Dong ghi TRUOC 13/09 khong co cot 'gia' (13 o)
       va cot 've' cua no danh so CU (3 = co nguoi vao). Dong tu 13/09 co 14 o va danh so
       MOI (3 = het tao day). Phan biet bang SO O, khong bang ngay — dem o thi khong the
       doc nham (KYLUAT.md muc 4)."""
    gan={}; het={}
    if not os.path.exists(path): return gan,het
    for dong in open(path,encoding="utf-8"):
        # 🆕 v7.1 (14/09): nhan CA dong 'DC' (ro doi chung — pool qua non).
        #   Truoc day chi nhan '| 20' nen dong DC chi duoc GHI, khong bao gio duoc CHAM
        #   ket qua 6/24/72h => 29 dong moi luot nam khong, va cau hoi "con non song hay
        #   chet" khong co lay mot con so. Day la ro doi chung LUAT.md muc 11 dang thieu.
        dc = dong.startswith("| DC 20")
        if not (dong.startswith("| 20") or dc): continue
        ph=[x.strip() for x in dong.strip().strip("|").split("|")]
        if len(ph)<13: continue
        try:
            a=ph[2].strip("`").lower()
            moc=ph[0][3:].strip() if dc else ph[0]     # bo tien to 'DC '
            g=calendar.timegm(time.strptime(moc[:16],"%Y-%m-%d %H:%M"))
            anh={"gio":g,"ma":ph[1],"vi":_so_o(ph[3]),"doi_ung":_so_o(ph[4]),
                 "mc":_so_o(ph[5]),"gia":_so_o(ph[6]) if len(ph)>=14 else None,
                 "non":dc}
            het.setdefault(a,[]).append(anh)
            # 🔴 Con non KHONG duoc lam moc cho VE 5: no chua tung qua ba ve gia,
            #   so hai anh cua no la so hai tap khac nhau (KYLUAT.md muc 4).
            if dc: continue
            if a not in gan or g>gan[a]["gio"]: gan[a]=anh
        except Exception: pass
    return gan,het

def nhip_lenh(c,cua="h1"):
    """Doc so LENH va so VI rieng biet tu feed. KHONG goi them cu nao.
    Tra ve (ty_le_lenh, ty_le_vi, lenh_tren_vi, nhan).
    🔴 Day la MO TA, khong phai cua chan. Ty le cao KHONG co nghia la gia se len —
    do 13/09 tren 11 con: hai con lech mua nhat (3.16 va 1.89) giam 95%% va 93%%."""
    t=(c.get("tx") or {}).get(cua) or {}
    m,b=t.get("buys") or 0, t.get("sells") or 0
    vm,vb=t.get("buyers") or 0, t.get("sellers") or 0
    tl  = (m/b) if b else None
    tlv = (vm/vb) if vb else None
    lpv = ((m+b)/(vm+vb)) if (vm+vb) else None
    if tl is None: nhan="—"
    elif tl>=NHIP_CAO:  nhan="NHIEU LENH NHO BAT DAY"
    elif tl<=NHIP_THAP: nhan="IT LENH, NGHIENG BAN"
    else: nhan="CAN"
    return tl,tlv,lpv,nhan

def _ma_ve(c):
    """Chuoi 5 ky tu, mot ky tu moi ve. '-' = truot · '.' = CHUA CHAY TOI.
    Phan biet hai cai do la bat buoc: con truot ve 2 thi ve 4 khong sai, no khong
    duoc do. Dem chung mot ky tu la sau nay quet do nhay se dem nham."""
    ra=""
    for i in (1,2,3,4,5):
        v=c.get("ve%d"%i)
        ra += "." if v is None else (str(i) if v else "-")
    return ra

def ghi_anh(rows,path=SO_ANH,doi_chung=()):
    """Ghi anh chup MOI con doc duoc nen — ke ca con truot cua.
    Do la cai lam cho luot sau co vat so. CAM sua tay file nay.

    doi_chung: cac pool qua loc tho nhung KHONG doc duoc nen (pool qua non). Ghi
    tien to 'DC' de khong lan vao bang chinh — day la ro doi chung, khong phai hang san."""
    moi = not os.path.exists(path)
    g=time.strftime("%Y-%m-%d %H:%M",time.gmtime())
    with open(path,"a",encoding="utf-8") as f:
        if moi:
            f.write("# SO ANH CHUP — script tu ghi moi luot. CAM sua tay.\n\n")
            f.write("> Muc dich: luot sau doc anh cu -> biet SO VI tang hay giam, DOI UNG tang hay\n")
            f.write("> giam. Khong can dung lai qua khu tu log Transfer (⛔ qua dat).\n")
            f.write("> Bean chot 12/09. Du 30 dong cung mot con -> quet do nhay duoc nguong ve 2 va 5.\n")
            f.write("> Cot 'nam ve': 5 ky tu, '-' la truot, '.' la chua chay toi ve do.\n")
            f.write("> Cot 'h tu dinh' (them 14/09): dinh doi pool cach day may gio. Day la so quyet\n")
            f.write("> duoc NEN_MIN nen la 36 hay 48 — dinh toi muon thi cham som la cham khi chua co dinh.\n\n")
            f.write("| gio UTC | ma | dia chi | so vi | doi ung | von hoa | gia | gia/dinh | h tu dinh | gio duoi | vol 1h/nen | nam ve | nhip h1 | vi h1 | lenh/vi |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for c in rows:
            r=c.get("cua") or {}
            tl,tlv,lpv,_ = nhip_lenh(c)
            f.write("| %s | %s | `%s` | %s | %s | $%s | %s | %.1f%% | %s | %d/%d | %s | %s | %s | %s | %s |\n"%(
                g,c["ma"],c["base"] or "?",
                format(int(r["so_vi"]),",") if r.get("so_vi") else "—",
                ("$"+format(int(c["dothat"]),",")) if c.get("dothat") else "—",
                format(int(c["mc"]),","),
                ("%.10g"%c["gia"]) if c.get("gia") else "—",
                c.get("xep",0)*100,
                ("%.0fh"%c["gio_tu_dinh"]) if c.get("gio_tu_dinh") is not None else "—",
                c.get("gio_duoi",0),GIO_NAM,
                ("%.1fx"%c["vol_lan"]) if c.get("vol_lan") else "—",
                _ma_ve(c),
                ("%.2f"%tl) if tl is not None else "—",
                ("%.2f"%tlv) if tlv is not None else "—",
                ("%.1f"%lpv) if lpv is not None else "—"))
        if doi_chung:
            for c in doi_chung:
                tl,tlv,lpv,_ = nhip_lenh(c)
                f.write("| DC %s | %s | `%s` | — | — | $%s | %s | %s | %s | %d nen | — | ..... | %s | %s | %s |\n"%(
                    g,c["ma"],c["base"] or "?", format(int(c["mc"]),","),
                    ("%.10g"%c["gia"]) if c.get("gia") else "—",
                    ("%.1f%%"%(c["xep"]*100)) if c.get("xep") else "—",
                    ("%.0fh"%c["gio_tu_dinh"]) if c.get("gio_tu_dinh") is not None else "—",
                    c.get("so_nen") or 0,
                    ("%.2f"%tl) if tl is not None else "—",
                    ("%.2f"%tlv) if tlv is not None else "—",
                    ("%.1f"%lpv) if lpv is not None else "—"))
    return len(rows)

def ve_nam(c,gan):
    """VE 5 — CO NGUOI VAO. Chi cham duoc khi con nay DA CO ANH CU.
    Dat khi: so vi giu TANG  va  doi ung KHONG bi rut (thuoc 2 >= THUOC2_SAN).

    🔴 CUA LA DAU, KHONG PHAI MUC (Bean chot 13/09). Toc do %/gio duoc in ra va ghi so
       de sau nay quet do nhay, nhung KHONG quyet dinh qua/truot — dat mot muc bay gio
       la bia so (KYLUAT.md muc 11).
    🔴 Khoang cach hai anh KHONG co dinh (do 4 luot that: 3,2h · 2,8h · 6,1h). Ngoai dai
       VE5_CACH_MIN..MAX thi KHONG cham — so hai anh lech gio la so hai tap (KYLUAT.md 4).
    Dat c['ve5'] = True/False/None. None = chua do duoc, KHAC hoan toan False."""
    c["ve5"]=None; c["ve5_ly"]=""
    a=(c.get("base") or "").lower()
    if a not in gan:
        c["ve5_ly"]="CHUA CO ANH CU — luot dau cua con nay, ghi lai de lan sau so"
        print("   VE 5 ⬜ co nguoi vao: %s"%c["ve5_ly"]); return
    anh=gan[a]; cach=(time.time()-anh["gio"])/3600
    r=c.get("cua") or {}
    vi_cu,vi_moi = anh["vi"], r.get("so_vi")
    du_cu,du_moi = anh["doi_ung"], c.get("dothat")
    print("   VE 5 — co nguoi vao (so voi anh chup cach %.1f gio):"%cach)
    if not (VE5_CACH_MIN<=cach<=VE5_CACH_MAX):
        c["ve5_ly"]="anh cu cach %.1f gio, ngoai dai %.0f-%.0fh -> KHONG cham"%(
            cach,VE5_CACH_MIN,VE5_CACH_MAX)
        print("      ⬜ %s"%c["ve5_ly"]); return
    if not (vi_cu and vi_moi):
        c["ve5_ly"]="thieu so vi mot trong hai dau -> KHONG cham"
        print("      ⬜ %s"%c["ve5_ly"]); return

    d_vi=(vi_moi/vi_cu-1)*100; toc=d_vi/cach
    print("      so vi   %s -> %s  (%+.1f%% · %+.2f%%/gio) %s"%(
          format(int(vi_cu),","),format(int(vi_moi),","),d_vi,toc,
          "✅ co nguoi vao" if d_vi>0 else "🔴 nguoi ta dang bo di"))
    c["ve5_toc"]=toc

    t=None
    if du_cu and du_moi:
        d_du=(du_moi/du_cu-1)*100
        # 🔴 Doi ung roi theo CAN BAC HAI cua gia — phai chia cho phan ky vong, neu khong
        #    la doc nham cai co hoc cua pool thanh 'bi rut' (KYLUAT.md muc 9).
        ky_vong=(du_cu*((c["mc"]/anh["mc"])**0.5)) if (anh["mc"] and c.get("mc")) else None
        if ky_vong:
            t=du_moi/ky_vong
            print("      doi ung $%s -> $%s (%+.1f%%) · THUOC 2 = %.2f %s"%(
                  format(int(du_cu),","),format(int(du_moi),","),d_du,t,
                  "🔴 CO NGUOI RUT" if t<THUOC2_SAN else
                  ("✅ CO NGUOI BOM" if t>THUOC2_TRAN else "khong ai dong vao")))
        else:
            print("      doi ung $%s -> $%s (%+.1f%%) · ⬜ thieu von hoa cu, khong chay duoc thuoc 2"%(
                  format(int(du_cu),","),format(int(du_moi),","),d_du))
    else:
        print("      doi ung ⬜ thieu so mot trong hai dau")
    if t is None:
        c["ve5_ly"]="khong chay duoc thuoc 2 -> KHONG cham"
        print("      ⬜ %s"%c["ve5_ly"]); return

    c["ve5"] = (d_vi>0) and (t>=THUOC2_SAN)
    c["ve5_ly"]=("so vi %+.1f%% · thuoc 2 %.2f"%(d_vi,t))
    print("      VE 5 %s  (%s)"%("✅ DAT" if c["ve5"] else "🔴 TRUOT",c["ve5_ly"]))

def cham_ket_qua(het,gia_nay,path=SO_ANH):
    """🆕 13/09. Sau moi luot, cham lai cac anh cu da du tuoi 6h/24h/72h.
    Khong co buoc nay thi ca he KHONG BAO GIO tu biet sua ve xong la tot len hay xau di —
    so chi ghi trang thai, khong ghi ket qua.
    0 cu goi them: gia lay tu chinh lenh feed cua luot nay."""
    if not os.path.exists(path): return 0
    da=set()
    for dong in open(path,encoding="utf-8"):
        if dong.startswith("| KQ "):
            ph=[x.strip() for x in dong.strip().strip("|").split("|")]
            if len(ph)>=5: da.add((ph[2].strip("`").lower(),ph[3],ph[4]))
    moi=[]; now=time.time()
    for a,ds in het.items():
        if a not in gia_nay: continue
        for anh in ds:
            if not anh.get("gia"): continue
            gio_txt=time.strftime("%Y-%m-%d %H:%M",time.gmtime(anh["gio"]))
            tuoi=(now-anh["gio"])/3600
            for moc in KQ_MOC:
                if not (moc <= tuoi <= moc*(1+KQ_LECH)): continue
                if (a,gio_txt,"%dh"%moc) in da: continue
                d=(gia_nay[a]/anh["gia"]-1)*100
                # 🆕 v7.1: o cuoi ghi ro anh nay thuoc nhom nao. Khong co o nay thi hai
                #   nhom tron lam mot va bang so "non vs du tuoi" khong lap duoc.
                moi.append("| KQ | %s | `%s` | %s | %dh | %.10g | %.10g | %+.1f%% | %s |\n"%(
                    anh["ma"],a,gio_txt,moc,anh["gia"],gia_nay[a],d,
                    "non" if anh.get("non") else "du"))
    if moi:
        with open(path,"a",encoding="utf-8") as f: f.writelines(moi)
    return len(moi)

def bang_gia(pools):
    """{dia_chi token: gia USD} lay tu TOAN BO feed, truoc loc tho.
    Moi token lay pool day nhat — cung nguon, cung mot lenh goi (KYLUAT.md muc 5)."""
    ra={}; day={}
    for p in pools.values():
        a=p["attributes"]; rel=p.get("relationships") or {}
        t=(dia_chi(rel,"base_token") or "").lower()
        g=so(a.get("base_token_price_usd")); res=so(a.get("reserve_in_usd")) or 0
        if not (t and g): continue
        if t not in day or res>day[t]: day[t]=res; ra[t]=g
    return ra

# ---------- 6. VUNG GIA VAO ----------
def vung_vao(c):
    """Cua cu quy ra DO. KHONG co so tay nao — xem LUAT.md muc 4.6."""
    P=c.get("gia_nen"); du=c.get("dothat"); dinh=c.get("dinh")
    if not (P and du and dinh): print("   VUNG VAO: ⛔ thieu gia, doi ung hoac dinh"); return
    n=lambda x:("$%.9f"%x).rstrip("0")
    tran=XEP_TOI*dinh
    san =P*(DOI_UNG_SAN/du)**2
    kh  =khu_hoi(du,c.get("phi",0.0))
    dat =P*(1+kh/200)
    print("   VUNG DUNG DUOC: %s -> %s"%(n(san),n(tran)))
    print("      tran xep %s = %.0f%% dinh · san phi %s = noi khu hoi cham %.0f%%"%(
          n(tran),XEP_TOI*100,n(san),KHU_HOI_MAX))
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
    """DANH THIEP — chi chay cho con DA QUA HET CUA. 1 cu. KHONG phai cua chan."""
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
        xh =" · ".join(x.get("url","")  for x in (info.get("socials")  or []))
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
    print("      🔴 bac KHONG doi co lenh, KHONG doi cua, KHONG doi gi het.")
    if len(cas)<=1:
        print("   dia chi cung ma tren chuoi nay: 1")
    else:
        a,mc=sorted(cas.items(),key=lambda kv:-kv[1])[0]
        print("   🔴 %d DIA CHI CUNG MA tren chuoi nay (%d pool). To nhat %s von hoa $%s"%(
              len(cas),len(rows),a,format(int(mc),",")))
        print("      /search cat o 50 -> day la SAN. /search tra VON HOA LON NHAT trong moi pool")
        print("      -> pool bui thoi so len (ca CRUMBS: $4.020.453 vs pool chinh $324.227).")
        print("      🔴 SO DIA CHI DU 42 KY TU (ca STREAM `f94c` · CRUMBS `9136` · MARIO `420c`).")

# ---------- 7. SO DA BAO ----------
def doc_da_bao(path):
    cu={}
    if path and os.path.exists(path):
        for dong in open(path,encoding="utf-8"):
            dong=dong.strip()
            if not dong or dong.startswith("#"): continue
            ph=[x.strip() for x in dong.split("|")]
            if len(ph)<2: continue
            try: cu[ph[0].lower()]=calendar.timegm(time.strptime(ph[1][:19],"%Y-%m-%dT%H:%M:%SZ"))
            except Exception:
                try: cu[ph[0].lower()]=calendar.timegm(time.strptime(ph[1][:19],"%Y-%m-%dT%H:%M:%S"))
                except Exception: pass
    return cu

# ---------- MAIN ----------
def main():
    so_da_bao = sys.argv[1] if len(sys.argv)>1 else None
    da_bao = doc_da_bao(so_da_bao)
    anh_gan, anh_het = doc_anh_cu()
    gio=time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime())

    in_nguong()
    pools,hong,loi_feed=feed()
    print("\nPHIEU · %s"%gio)
    print("feed: %d pool doc duoc · %d trang loi"%(len(pools),hong))
    for x in loi_feed: print("   loi feed: "+x)
    if hong>8:
        print("FEED HONG — hon 8 trang loi. KHONG KET LUAN."); return
    if not pools:
        print("FEED HONG — 0 pool. LOI GOI, khong phai 'khong co du lieu'."); return

    gia_nay=bang_gia(pools)
    n_kq=cham_ket_qua(anh_het,gia_nay)
    print("cham ket qua anh cu (moc %s gio): %d dong moi"%("/".join(str(x) for x in KQ_MOC),n_kq))

    tho=loc_tho(pools)
    print("qua loc tho (mc $%s-$%s · reserve>=$%s): %d"%(
        format(MC_MIN,","),format(MC_MAX,","),format(RESERVE_SO,","),len(tho)))
    if not tho:
        print("KHONG CO GI TRONG DAI"); print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0)); return

    doc=[]; non=[]; loi_nen=0
    for c in tho:
        ba_ve(c)
        if c["ly_nen"].startswith("LOI GOI"): loi_nen+=1; print("   ⛔ %s: %s"%(c["ma"],c["ly_nen"]))
        elif "qua non" in c["ly_nen"]: non.append(c)
        else: doc.append(c)
    print("doc duoc nen: %d · pool qua non (<%d nen): %d · loi goi: %d"%(
          len(doc),NEN_MIN,len(non),loi_nen))

    cands=[c for c in doc if c["ve1"] and c["ve2"] and c["ve3"]]
    print("qua VE 1+2+3 (hinh dang gia): %d"%len(cands))

    if not cands:
        print("da ghi %d dong anh chup + %d dong ro doi chung vao %s"%(
              ghi_anh(doc,doi_chung=non),len(non),SO_ANH))
        print("KHONG CO GI TRONG DANH SACH THEO DOI")
        print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0)); return

    err=doi_ung_that(cands)
    if err:
        print(err); print("KHONG KET LUAN — RPC hong, khong phai khong co ung vien."); return

    gp=goplus([(c.get("base") or "").lower() for c in cands])
    print("GoPlus: doc duoc %d/%d con"%(len(gp),len(cands)))

    nguong=time.time()-GIO_KHONG_BAO_LAI*3600; theo_doi=[]; ung_vien=[]
    for c in sorted(cands,key=lambda x:-(x["dothat"] or 0)):
        kh=khu_hoi(c["dothat"],c.get("phi",0.0)) if c["dothat"] else None
        c["ve4"]=False
        if c["dothat"] is None:
            tt="⛔ LOAI O VE 4: chua do duoc doi ung (%s)"%c["ly_do"]; c["ve4"]=None
        elif kh>KHU_HOI_MAX:
            tt="LOAI O VE 4 — PHI: khu hoi $%d = %.2f%% > cua %.2f%%  (doi ung $%s · %s)"%(
                CO_LENH,kh,KHU_HOI_MAX,format(int(c["dothat"]),","),in_phi(c))
        elif c["base"] in da_bao and da_bao[c["base"]]>=nguong:
            tt="BO QUA: da bao trong %d gio qua"%GIO_KHONG_BAO_LAI; c["ve4"]=None
        else:
            c["gp"]=gp.get((c.get("base") or "").lower())
            gp_chan,_ = doc_goplus(c["gp"])
            if gp_chan:
                tt="LOAI O VE 4 — GOPLUS: "+doc_goplus(c["gp"])[1].split("CHAN: ")[-1]
                print("\n%s  %s"%(c["ma"],c["base"])); in_ba_ve(c)
                print(doc_goplus(c["gp"])[1]); print("   %s"%tt); continue
            r=cua_nguoi_giu(c["base"]); c["cua"]=r; time.sleep(1.0)
            if qua_cua_nang(r):
                c["ve4"]=True; tt="DANH SACH THEO DOI"; theo_doi.append(c)
            elif r["loi"]:
                c["ve4"]=None; tt="⛔ LOAI O VE 4: "+doc_cua(r)
            else:
                tt="LOAI O VE 4 — NGUOI GIU: "+doc_cua(r)
        print("\n%s  %s"%(c["ma"],c["base"]))
        if canh_bao_ten(c["ma"]):
            print("   ⚠️ MA TRUNG TICKER SAN MY — canh bao, KHONG phai cua chan. Mo ra kiem.")
        in_ba_ve(c)
        print("   VE 4 %s sach nang: doi ung that %s  (GeckoTerminal bao tong pool $%s) · %s"%(
            "✅" if c["ve4"] else ("⬜" if c["ve4"] is None else "🔴"),
            ("$"+format(int(c["dothat"]),",")) if c["dothat"] else "CHUA DO DUOC",
            format(int(c["res"]),","),in_phi(c)))
        print(doc_goplus(c.get("gp"))[1])
        print("   von hoa $%s · cap %s · vol24 $%s · pool %s"%(
            format(int(c["mc"]),","),c["cap"],format(int(c["vol"]),","),c["pool"]))
        print("   %s"%tt)
        if c["ve4"] is True:
            print("   %s"%doc_cua(c["cua"]))
            print("   khu hoi $%d: %.2f%% / cua %.2f%%  (truot gia hai chieu + %s)"%(
                  CO_LENH,kh,KHU_HOI_MAX,in_phi(c)))
            ve_nam(c,anh_gan)
            if c["ve5"] is True:
                ung_vien.append(c)
                print("   ⇒ UNG VIEN — du ca nam ve")
                vung_vao(c)
                thiep(c)
                print("   ⏰ GIO IN PHIEU: %s  — vao tien muon hon thi DO LAI truoc, xu theo so moi"%gio)
                print("   DONG DAN VAO SO DA BAO: %s | %s | %s"%(
                    c["base"],time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),c["ma"]))
            else:
                print("   ⇒ CHI THEO DOI, chua co su kien vao. KHONG phai lenh vao.")
    print("\nda ghi %d dong anh chup + %d dong ro doi chung vao %s"%(
          ghi_anh(doc,doi_chung=non),len(non),SO_ANH))
    print("danh sach theo doi (qua 1-2-3-4): %d"%len(theo_doi))
    print("ung vien (du ca 5 ve): %d"%len(ung_vien))
    if not ung_vien: print("KHONG CO UNG VIEN MOI")
    print("[%d cu · %.0f giay]"%(CU[0],time.time()-T0))

main()
