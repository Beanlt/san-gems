#!/bin/bash
# SAN GEMS — chay tu dong. Goi boi GitHub Actions hoac launchd tren may Bean.
# Chay THANG, KHONG qua proxy nao -> 4 cong deu thong.
# Bang lich: LUAT.md muc 10.1. NGUOC + NO LAI moi luot. DAY PHANG moi ngay 1 lan.
#
# Cach goi:
#   bash chay.sh nhanh      -> chi NGUOC + NO LAI            (lo 3 gio)
#   bash chay.sh dayphang   -> chi DAY PHANG                 (moi ngay 1 lan)
#   bash chay.sh            -> ca ba                         (launchd tren may Bean)
#
# 🔴 VA 11/09 (luot chay that dau tien tren GitHub, run #1):
#   - Lo DAY PHANG khong con go cung "0 17" va "17 34". Luot do ra 42 ung vien, hai lo
#     go cung chi doc 34 -> 8 con BIEN MAT khong mot dong bao. Nay tu dem roi lap du lo.
#   - Tach duoc lo nhanh khoi lo DAY PHANG de lo 3 gio khong bi keo cham theo.

set -u
cd "$(dirname "$0")" || exit 1
mkdir -p phieu

CHE_DO="${1:-tatca}"

PY="$(command -v python3)"
if [ -z "$PY" ]; then
  echo "$(date -u +%FT%TZ) ⛔ KHONG CO python3 — cai Command Line Tools: xcode-select --install" >> chay.log
  exit 1
fi

G="$(date -u +%Y-%m-%d_%H%M)"
NGAY="$(date -u +%Y-%m-%d)"
LO_NEN=17          # so con moi lo doc nen. Giu nguyen con so cu.

dan_so() {
  # Script in san dong de dan vao so da bao. Tu dan, khong cho Bean lam tay.
  [ -f "$1" ] || return 0
  grep "DONG DAN VAO SO DA BAO:" "$1" 2>/dev/null \
    | sed 's/.*DONG DAN VAO SO DA BAO: //' >> DA-BAO.md
}

chay_nhanh() {
  for loi in nguoc nolai; do
    F="phieu/${G}_${loi}.txt"
    "$PY" SAN.py "$loi" DA-BAO.md > "$F" 2>&1
    dan_so "$F"
  done
}

chay_dayphang() {
  # Moi ngay mot lan. File moc duoc commit vao repo nen nhip ngay song qua cac luot.
  if [ -f ".dayphang_${NGAY}" ]; then
    echo "$(date -u +%FT%TZ) DAY PHANG: da chay hom nay, bo qua" >> chay.log
    return 0
  fi
  F="phieu/${G}_dayphang.txt"
  "$PY" SAN.py dayphang-feed > "$F" 2>&1

  # 🔴 Dem SO THAT ung vien roi lap du lo — thay cho hai lo go cung truoc day.
  N="$("$PY" - <<'EOF' 2>/dev/null || echo 0
import json
try:
    print(len(json.load(open("dp_cands.json"))))
except Exception:
    print(0)
EOF
)"
  echo "so ung vien qua loc tho: $N — chia lo $LO_NEN con moi lo" >> "$F"
  if [ "$N" -gt 0 ] 2>/dev/null; then
    i=0
    while [ "$i" -lt "$N" ]; do
      j=$(( i + LO_NEN ))
      "$PY" SAN.py dayphang-nen "$i" "$j" >> "$F" 2>&1
      i=$j
    done
  else
    echo "⛔ khong doc duoc dp_cands.json — feed hong hoac 0 ung vien. KHONG ket luan." >> "$F"
  fi

  "$PY" SAN.py dayphang DA-BAO.md >> "$F" 2>&1
  dan_so "$F"
  touch ".dayphang_${NGAY}"
  find . -maxdepth 1 -name ".dayphang_*" -mtime +2 -delete 2>/dev/null
}

case "$CHE_DO" in
  nhanh)    chay_nhanh ;;
  dayphang) chay_dayphang ;;
  *)        chay_nhanh; chay_dayphang ;;
esac

# ---- gop phieu luot nay de Bean va Claude doc mot cho ----
# Tach ten file theo che do: hai workflow chay rieng nen khong duoc de chung de len nhau.
case "$CHE_DO" in
  dayphang) RA="MOI-NHAT-DAYPHANG.md" ;;
  *)        RA="MOI-NHAT.md" ;;
esac
# 🔴 CHI ghi de khi luot NAY that su co phieu. Bat duoc luc thu 11/09: luot DAY PHANG
#    chay lai trong cung ngay se bo qua quet (dung) nhung van ghi de file thanh RONG,
#    xoa mat phieu cua luot dau. Doc file rong roi tuong "khong co ung vien" la sai kieu
#    nang nhat (KYLUAT.md: lo i goi KHAC khong co du lieu).
CO_PHIEU_MOI=0
for f in phieu/${G}_*.txt; do [ -f "$f" ] && CO_PHIEU_MOI=1 && break; done

if [ "$CO_PHIEU_MOI" = "1" ]; then
{
  echo "# PHIEU MOI NHAT ($CHE_DO) — $(date -u +%FT%TZ)"
  echo
  echo "> May tu ghi, CAM sua tay. Phieu cu nam trong thu muc phieu/ (giu 7 ngay)."
  echo
  for f in phieu/${G}_*.txt; do
    [ -f "$f" ] || continue
    echo "## $(basename "$f")"
    echo '```'
    cat "$f"
    echo '```'
    echo
  done
} > "$RA"
else
  echo "$(date -u +%FT%TZ) luot nay khong sinh phieu moi -> GIU NGUYEN $RA" >> chay.log
fi

find phieu -name "*.txt" -mtime +7 -delete 2>/dev/null

echo "$(date -u +%FT%TZ) xong ($CHE_DO) — $(ls phieu/${G}_*.txt 2>/dev/null | wc -l | tr -d ' ') phieu" >> chay.log
