# NHIET.py — MAY DO NHIET (LUAT.md muc 12, Bean chot 03/11). SCRIPT.md v8.0.
# Hoi: tien dang chay ve CHUOI nao, BE PHONG nao. KHONG hoi con nao.
# 🔴 CHI DE DOC: khong cua, khong nguong "nong", khong ban tin, khong tu bat tat may san.
# Chay TRUOC SAN.py trong chay.sh. Hong thi in ⛔ va thoat 0 — KHONG BAO GIO lam hong luot quet.
# Ghi: nhiet.txt (chay.sh dat len DAU phieu) + dong "| NH ..." cuoi DO-DEM.md
#      (SAN.py chi doc dong "| 20" / "| DC 20" / "| KQ " nen KHONG dung vao dong NH).
import json, sys, time, urllib.request, urllib.parse

LLAMA     = "https://api.llama.fi/overview/dexs"
CHUOI     = ["Robinhood Chain", "Solana", "BSC", "Base", "Ethereum", "Hyperliquid L1", "Arbitrum"]
BP_SAN    = 1_000_000   # be phong co khoi luong 7 ngay >= muc nay moi in. MOC LOC HIEN THI, KHONG phai nguong nong.
BP_TOI_DA = 12          # in toi da bao nhieu be phong (xep theo khoi luong 7 ngay)
GOI_LAI   = 2           # so lan goi lai khi loi (429 / timeout / 5xx)
NGHI      = 10          # giay nghi truoc khi goi lai
SO_ANH    = "DO-DEM.md"
RA        = "nhiet.txt"
Q         = "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"
UA        = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def goi(url):
    """Tra (ok, json, ly_do). Loi goi tra ok=False — KHONG tra rong de doc nham thanh 'khong co'."""
    ly = ""
    for lan in range(GOI_LAI + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return True, json.loads(r.read()), ""
        except Exception as e:
            ly = "%s %s" % (type(e).__name__, getattr(e, "code", "") or str(e)[:80])
            if lan < GOI_LAI:
                time.sleep(NGHI)
    return False, None, ly


def do(x):
    if x is None:
        return "—"
    x = float(x)
    if x >= 1e9:
        return "$%.2f ty" % (x / 1e9)
    if x >= 1e6:
        return "$%.1f tr" % (x / 1e6)
    return "$%.0fk" % (x / 1e3)


def pt(x):
    return "—" if x is None else "%+.0f%%" % float(x)


def main():
    gio = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    ra = ["NHIET · %s UTC — tien chay ve dau (CHI DE DOC, khong phai lenh mua · LUAT.md muc 12)" % gio,
          "nguong dang chay: chuoi=%d · be phong >= %s/7 ngay · toi da %d dong · goi lai %d lan" % (
              len(CHUOI), do(BP_SAN), BP_TOI_DA, GOI_LAI)]
    so = []
    loi = 0

    ra.append("CHUOI (khoi luong san phi tap trung) | 24 gio | 7 ngay | 7 ngay so 7 ngay truoc | 30 ngay so 30 ngay truoc")
    hang = []
    for c in CHUOI:
        ok, j, ly = goi(LLAMA + "/" + urllib.parse.quote(c) + Q)
        if not ok:
            loi += 1
            ra.append("  ⛔ %-15s loi goi: %s" % (c, ly))
            so.append("| NH %s | chuoi | %s | ⛔ | | | |\n" % (gio, c))
            continue
        hang.append((j.get("change_7dover7d") if j.get("change_7dover7d") is not None else -1e9, c, j))
        time.sleep(1)
    for _, c, j in sorted(hang, key=lambda h: -h[0]):
        ra.append("  %-15s %10s %11s %8s %8s" % (c, do(j.get("total24h")), do(j.get("total7d")),
                                                pt(j.get("change_7dover7d")), pt(j.get("change_30dover30d"))))
        so.append("| NH %s | chuoi | %s | %.0f | %.0f | %s | %s |\n" % (
            gio, c, j.get("total24h") or 0, j.get("total7d") or 0,
            j.get("change_7dover7d"), j.get("change_30dover30d")))

    ok, j, ly = goi(LLAMA + Q)
    ra.append("BE PHONG (nhom Launchpad, 7 ngay >= %s) | chuoi | 7 ngay | 7/7 | 30/30" % do(BP_SAN))
    if not ok:
        loi += 1
        ra.append("  ⛔ loi goi danh sach be phong: %s" % ly)
        so.append("| NH %s | bephong | ⛔ | | | | |\n" % gio)
    else:
        bp = [p for p in (j.get("protocols") or [])
              if p.get("category") == "Launchpad" and (p.get("total7d") or 0) >= BP_SAN]
        bp.sort(key=lambda p: -(p.get("total7d") or 0))
        if not bp:
            ra.append("  (0 be phong tren muc loc — goi THANH CONG, day la so that)")
        for p in bp[:BP_TOI_DA]:
            ch = ",".join((p.get("chains") or [])[:2])
            ra.append("  %-22s %-16s %10s %8s %8s" % ((p.get("displayName") or p.get("name"))[:22], ch[:16],
                                                    do(p.get("total7d")), pt(p.get("change_7dover7d")),
                                                    pt(p.get("change_30dover30d"))))
            so.append("| NH %s | bephong | %s | %s | %.0f | %s | %s |\n" % (
                gio, p.get("name"), ch, p.get("total7d") or 0,
                p.get("change_7dover7d"), p.get("change_30dover30d")))
    ra.append("🔴 Be phong tang manh co the chi do MOT token (LUAT.md 12 luat 3) — dem so token truoc khi doc la 'nong'.")
    ra.append("🔴 Bang noi O DAU, khong noi VI SAO. Chua cham viec treo #26 thi khong dung de quyet gi.")
    if loi:
        ra.append("⛔ %d cu goi hong sau %d lan goi lai — o ⛔ la LOI GOI, khong phai 'khong co du lieu'." % (loi, GOI_LAI))
    ra.append("")

    with open(RA, "w", encoding="utf-8") as f:
        f.write("\n".join(ra) + "\n")
    try:
        with open(SO_ANH, "a", encoding="utf-8") as f:
            f.writelines(so)
    except Exception as e:
        print("⛔ khong ghi duoc %s: %s" % (SO_ANH, e))
    print("\n".join(ra))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # tuyet doi khong lam hong luot quet
        msg = "NHIET · ⛔ may do nhiet hong: %s %s\n\n" % (type(e).__name__, str(e)[:120])
        open(RA, "w", encoding="utf-8").write(msg)
        print(msg)
    sys.exit(0)
