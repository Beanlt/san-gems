# chay.sh — MOT loi duy nhat (SCRIPT.md v5, Bean chot 12/09)
# Chay bang: bash chay.sh
# 🔴 File nay KHONG dung git. Phan commit/push do workflow san.yml lo.
#    Truoc 12/09 ca hai cung push -> dung do la nguon sinh conflict.
set -u

python3 SAN.py DA-BAO.md 2>&1 | tee phieu.txt

mkdir -p phieu
cp phieu.txt "phieu/$(date -u +%Y-%m-%d_%H%M).txt"
cp phieu.txt MOI-NHAT.md
find phieu -type f -mtime +7 -delete
