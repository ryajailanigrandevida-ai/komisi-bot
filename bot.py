import os, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

BOT_TOKEN    = os.environ.get(‘BOT_TOKEN’)
SHEET_ID     = os.environ.get(‘SHEET_ID’)
ALLOWED_USER = int(os.environ.get(‘MY_TELEGRAM_ID’, ‘0’))

CREDS_DICT = {
“type”: “service_account”,
“project_id”: “komisi-bot”,
“private_key_id”: “64eb657238def2bcd78f468e441584c6a0517488”,
“private_key”: “—–BEGIN PRIVATE KEY—–\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDGv6hXLE/jjUrE\nClqTTBQG+EcCyr9d3duzQGd3IJwPGYN3+1B2QzMZ2D10CHiD/J9+WZlWJKYOXPU2\nPI4kL4bwToToeKuknSexv3/otfM/6yhDs22U32o1Hd5kJEDOe01uK4OudHmxaD8W\ntL5Dto9Q5YzjI6Nb2rhOTlJxu+B8cFFZa1iKJvBw254lINIhTZWrMxfkCTtNkNTZ\nFsTdebEKH9uE5n45cuzXCXIQRuwbFLjwAAViYD4SC5Uxi2LLTehwTExBsdjEbQ5K\naFo47aG9EHy8/CMizgKb2x5i1jaItuQgWF2RIQE22whDFMffKtI1of6JoK5+NlL7\nkX5BQDynAgMBAAECggEATXIKhWmBeeCpVSnZsJMRLMQbW6Wom0mj3j4G8z80QJgH\nCD5YVLUL2RLPo4LXf0r11XTRkOU4BdnIPYmsM8KHWOWn2bSH4d3RRWyjSYl5D5ux\nNWxaE4xZZPhOHASacjtO6VKwfc7qSqyeBNmKWHVvdCz20N2mvtjEP9M6QhJdP++O\nB/3qCECpjTRS3rRcpprxGUipDDEaw1kMZXUB5hGOgfMG+HNlenBFA2JnAGNbGw9N\nhDl1v9O+O0gaPx3mKN5dnny5jurIK3Z+SK5S1qaPOFW1H7Q7cByEXta6VqrmDn60\npFxi/zvQhxUvHyLH+7wiFhQiHgasRiXG+KeGI+fgcQKBgQD07ESWKsB7ajuSmqjf\nRNnchFutSqRUgnTKgmB7x8Ej90AgtXw1ceAd4faKUlpn3rRekTrHDaX8QGnBhFUx\nlRc9SHpO+nDs8IXb3UwxI46sXJq5WzPWNP5X02menmiqztv50dPlbNyUauI8thRU\nRANx2lQRGjfQLaby8LcCPuumcQKBgQDPvMgHGpH6+B76rziQvKYCTEzih0nV/ivL\n4ZUBdEb2hq+0CfWde6fYY4jMmQPkyEs8VitywY7vjYMyYXCzyvtDf7tA3zdY0kcL\nI3gZiSjeJCDhov+CRU9t4Xftkkh6Yn09fTdXqUJEYQ2/zc0KNWYzmatiOUZKft9j\nqrvcmHoQlwKBgQDa4tShB/Ah290Ftma5ssSpiTiNdKnMRRKvcTldJjZ8OBn9oXQy\nJ2VOD4XQNK1LKwMziMNo5c+z0rUxF100BLRSNpXoQ3Xsq0BWMD5JpCd77v7wLIv1\nIkM0pmI8OgH8tQZvC5E99r5jfepWq7sbW/VgKOj8p9u9ly8e6vYDccwUYQKBgQC3\nQQyfn6PJZhpGAE6A97nmaxKj/r52xPozp7L/jmiPTu8ufl6qZwwAyoVCH3Wc28fq\n2QUI/ZCu6AIlbmmyYUxYFhTEvGShuRWs0MRAmotvsyVChrypWaUhBHX8IEBJnhpn\nJM+uSATKN2eenNjUuZiHynaydl34l4VO8a05g1SizwKBgDSidOHXnzhoHDQc1qpc\nlUBDVjVdPGBMiS6150Vgi7JNgBFZaMGrDdK4H+3yO206mQjfSL2iazerrByL/PvH\n5Ib6C3TvhseEad+Czg59FJSnzdyeRE8NFg/mCGK980bQdNlkwDoety658noJhceR\nXWhEHVbxIoCIvpnvmyMN5/L7\n—–END PRIVATE KEY—–\n”,
“client_email”: “komisi-bot@komisi-bot.iam.gserviceaccount.com”,
“client_id”: “112571321627461279166”,
“auth_uri”: “https://accounts.google.com/o/oauth2/auth”,
“token_uri”: “https://oauth2.googleapis.com/token”,
“auth_provider_x509_cert_url”: “https://www.googleapis.com/oauth2/v1/certs”,
“client_x509_cert_url”: “https://www.googleapis.com/robot/v1/metadata/x509/komisi-bot%40komisi-bot.iam.gserviceaccount.com”,
“universe_domain”: “googleapis.com”
}

def get_sheet():
creds = Credentials.from_service_account_info(
CREDS_DICT,
scopes=[‘https://www.googleapis.com/auth/spreadsheets’]
)
gc = gspread.authorize(creds)
return gc.open_by_key(SHEET_ID).worksheet(‘Transaksi Komisi’)

def find_next_empty_row(sheet):
“”“Cari baris kosong pertama setelah baris 5 (header di baris 5, data mulai baris 6)”””
all_values = sheet.get_all_values()
for i, row in enumerate(all_values):
if i < 5:  # skip header rows (0-4 = rows 1-5)
continue
if not row[1] and not row[2]:  # kolom B dan C kosong
return i + 1  # return nomor baris (1-indexed)
return len(all_values) + 1

def parse_input(text):
parts = [x.strip() for x in text.split(’|’)]
data = {
‘tanggal’: datetime.now().strftime(’%d/%m/%Y’),
‘properti’: parts[0] if len(parts) > 0 else ‘’,
‘komisi’:   parts[1] if len(parts) > 1 else ‘0’,
‘agents’:   [],
‘status’:   ‘Lunas’,
‘ket’:      ‘’
}
for p in parts[2:]:
if ‘:’ in p:
k, v = p.split(’:’, 1)
k = k.strip(); v = v.strip()
if k.lower() == ‘status’:
data[‘status’] = v
elif k.lower() in [‘ket’, ‘keterangan’]:
data[‘ket’] = v
else:
data[‘agents’].append((k, v))
return data

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ALLOWED_USER: return
await update.message.reply_text(
‘🏠 Komisi Bot aktif!\n\n’
‘Perintah:\n’
‘/input  — Input transaksi baru\n’
‘/cek    — 5 transaksi terakhir\n’
‘/total  — Total komisi\n’
‘/bantuan — Cara penggunaan’
)

async def bantuan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ALLOWED_USER: return
msg = (
‘📖 CARA INPUT:\n\n’
‘/input Nama Properti | Komisi | Nama:Rp | Status:Lunas\n\n’
‘📌 Contoh:\n’
‘/input Ciragil I No5 | 165000000 | Riza:115500000 | Status:Lunas\n\n’
‘/input Savyavasa 3BR | 236474000 | ND:165531800 | BS:20691475 | SB:20691475 | Status:Lunas’
)
await update.message.reply_text(msg)

async def input_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ALLOWED_USER:
await update.message.reply_text(‘⛔ Akses ditolak.’); return
raw = update.message.text.replace(’/input’, ‘’, 1).strip()
if not raw:
await update.message.reply_text(‘⚠️ Format salah. Ketik /bantuan’); return
try:
d = parse_input(raw)
sheet = get_sheet()
komisi_int = int(str(d[‘komisi’]).replace(’,’,’’).replace(’.’,’’).strip())

```
    # Siapkan data row: Tanggal, Properti, Komisi, A1nama, A1rp, A2nama, A2rp, A3nama, A3rp, A4nama, A4rp, ..., Status, Ket
    agents_padded = (d['agents'] + [(None,None)]*4)[:4]
    row_data = [d['tanggal'], d['properti'], komisi_int]
    for nama, rp in agents_padded:
        row_data.append(nama or '')
        row_data.append(rp or '')
    row_data.extend([d['status'], d['ket']])

    # Tulis ke baris kosong pertama
    next_row = find_next_empty_row(sheet)
    for col_idx, val in enumerate(row_data, start=1):
        sheet.update_cell(next_row, col_idx, val)

    agents_txt = '\n'.join([f'  • {n}: Rp {int(str(r).replace(",","").replace(".","").strip()):,}' for n,r in d['agents'] if n])
    reply = (
        f'✅ Tersimpan di baris {next_row}!\n\n'
        f'🏠 {d["properti"]}\n'
        f'💰 Komisi: Rp {komisi_int:,}\n'
        f'👤 Agent:\n{agents_txt}\n'
        f'📋 Status: {d["status"]}'
    )
    await update.message.reply_text(reply)
except Exception as e:
    await update.message.reply_text(f'❌ Error: {str(e)}')
```

async def cek(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ALLOWED_USER: return
try:
sheet = get_sheet()
all_rows = sheet.get_all_values()
# Ambil baris data (mulai row 6 = index 5)
data_rows = [r for r in all_rows[5:] if r[1]]
if not data_rows:
await update.message.reply_text(‘Belum ada data.’); return
last5 = data_rows[-5:]
msg = ‘📋 5 Transaksi Terakhir:\n\n’
for r in reversed(last5):
try:
komisi = int(str(r[2]).replace(’,’,’’).replace(’.’,’’))
status = r[29] if len(r) > 29 else ‘’
msg += f’🏠 {r[1]}\n💰 Rp {komisi:,}  |  {status}\n\n’
except:
msg += f’🏠 {r[1]}\n\n’
await update.message.reply_text(msg)
except Exception as e:
await update.message.reply_text(f’❌ Error: {str(e)}’)

async def total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ALLOWED_USER: return
try:
sheet = get_sheet()
all_rows = sheet.get_all_values()
data_rows = [r for r in all_rows[5:] if r[1]]
total_komisi = 0
for r in data_rows:
try:
total_komisi += int(str(r[2]).replace(’,’,’’).replace(’.’,’’))
except: pass
msg = (
f’📊 TOTAL KOMISI 2026\n\n’
f’Jumlah Transaksi: {len(data_rows)}\n’
f’Total Komisi: Rp {total_komisi:,}’
)
await update.message.reply_text(msg)
except Exception as e:
await update.message.reply_text(f’❌ Error: {str(e)}’)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler(‘start’,   start))
app.add_handler(CommandHandler(‘bantuan’, bantuan))
app.add_handler(CommandHandler(‘input’,   input_data))
app.add_handler(CommandHandler(‘cek’,     cek))
app.add_handler(CommandHandler(‘total’,   total))
print(‘Bot berjalan…’)
app.run_polling()
