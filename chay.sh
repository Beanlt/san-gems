#!/bin/bash
# SAN GEMS — chay tu dong tren may Bean. Goi boi launchd moi 3 gio.
# Chay THANG tren macOS, KHONG qua proxy nao -> 4 cong deu thong.
# Bang lich: LUAT.md muc 10.1. NGUOC + NO LAI moi luot. DAY PHANG moi ngay 1 lan.
cd "$(dirname "$0")" || exit 1
mkdir -p phieu

PY="$(command -v python3)"
if [ -z "$PY" ]; then
  echo "$(date -u +%FT%TZ) ⛔ KHONG CO python3 — cai Command Line Tools: xcode-select --install" >> chay.log
  exit 1
fi

G="$(date -u +%Y-%m-%d_%H%M)"
NGAY="$(date -u +%Y-%m-%d)"

dan_so() {
  # Script in san dong de dan vao so da bao. Tu dan, khong cho Bean lam tay.
  grep "DONG DAN VAO SO DA BAO:" "$1" 2>/dev/null \
    | sed 's/.*DONG DAN VAO SO DA BAO: //' >> DA-BAO.md
}

# ---- moi luot: NGUOC + NO LAI ----
for loi in nguoc nolai; do
  F="phieu/${G}_${loi}.txt"
  "$PY" SAN.py "$loi" DA-BAO.md > "$F" 2>&1
  dan_so "$F"
done

# ---- moi ngay mot lan: DAY PHANG (luot dau sau 00:00 UTC) ----
if [ ! -f ".dayphang_${NGAY}" ]; then
  F="phieu/${G}_dayphang.txt"
  "$PY" SAN.py dayphang-feed      > "$F" 2>&1
  "$PY" SAN.py dayphang-nen 0 17  >> "$F" 2>&1
  "$PY" SAN.py dayphang-nen 17 34 >> "$F" 2>&1
  "$PY" SAN.py dayphang DA-BAO.md >> "$F" 2>&1
  dan_so "$F"
  touch ".dayphang_${NGAY}"
  find . -maxdepth 1 -name ".dayphang_*" -mtime +2 -delete 2>/dev/null
fi

# ---- gop phieu luot nay vao MOI-NHAT.md de Bean va Claude doc mot cho ----
{
  echo "# PHIEU MOI NHAT — $(date -u +%FT%TZ)"
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
} > MOI-NHAT.md

# ---- don phieu cu hon 7 ngay ----
find phieu -name "*.txt" -mtime +7 -delete 2>/dev/null

echo "$(date -u +%FT%TZ) xong — $(ls phieu/${G}_*.txt 2>/dev/null | wc -l | tr -d ' ') phieu" >> chay.log
