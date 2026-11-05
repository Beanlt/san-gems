# chay.sh — MOT loi duy nhat (SCRIPT.md v5, Bean chot 12/09) + MAY DO NHIET (SCRIPT.md v8.0, Bean chot 03/11)
# Chay bang: bash chay.sh
# 🔴 File nay KHONG dung git. Phan commit/push do workflow san.yml lo.
#    Truoc 12/09 ca hai cung push -> dung do la nguon sinh conflict.
set -u

# 03/11: bang nhiet chay TRUOC, tu bat loi, luon thoat 0 -> hong cung khong lam hong luot quet.
python3 NHIET.py > /dev/null 2>&1 || echo "NHIET · ⛔ khong chay duoc NHIET.py" > nhiet.txt
[ -s nhiet.txt ] || echo "NHIET · ⛔ khong co nhiet.txt" > nhiet.txt

python3 SAN.py DA-BAO.md 2>&1 | tee phieu.txt

mkdir -p phieu
cat nhiet.txt phieu.txt > MOI-NHAT.md
cp MOI-NHAT.md "phieu/$(date -u +%Y-%m-%d_%H%M).txt"
find phieu -type f -mtime +7 -delete
