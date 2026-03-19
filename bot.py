import os, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

BOT_TOKEN    = os.environ.get('BOT_TOKEN')
SHEET_ID     = os.environ.get('SHEET_ID')
ALLOWED_USER = int(os.environ.get('MY_TELEGRAM_ID', '0'))
CREDS_JSON   = os.environ.get('GOOGLE_CREDS_JSON')

def get_sheet():
    creds_dict = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet('Transaksi Komisi')

def parse_input(text):
    parts = [x.strip() for x in text.split('|')]
    data = {
        'tanggal': datetime.now().strftime('%d/%m/%Y'),
        'properti': parts[0] if len(parts) > 0 else '',
        'komisi':   parts[1] if len(parts) > 1 else '0',
        'agents':   [],
        'status':   'Proses',
        'ket':      ''
    }
    for p in parts[2:]:
        if ':' in p:
            k, v = p.split(':', 1)
            k = k.strip(); v = v.strip()
            if k.lower() == 'status':
                data['status'] = v
            elif k.lower() in ['ket', 'keterangan']:
                data['ket'] = v
            else:
                data['agents'].append((k, v))
    return data

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    await update.message.reply_text(
        '🏠 Komisi Bot aktif!\n\n'
        'Perintah:\n'
        '/input  — Input transaksi baru\n'
        '/cek    — 5 transaksi terakhir\n'
        '/total  — Total komisi\n'
        '/bantuan — Cara penggunaan'
    )

async def bantuan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    msg = (
        '📖 CARA INPUT:\n\n'
        '/input Nama Properti | Komisi | Nama:Rp | Status:Lunas\n\n'
        '📌 Contoh:\n'
        '/input Ciragil I No5 | 165000000 | Riza:115500000 | Status:Lunas\n\n'
        '/input Savyavasa 3BR | 236474000 | ND:165531800 | BS:20691475 | SB:20691475 | Status:Lunas'
    )
    await update.message.reply_text(msg)

async def input_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        await update.message.reply_text('⛔ Akses ditolak.'); return
    raw = update.message.text.replace('/input', '', 1).strip()
    if not raw:
        await update.message.reply_text('⚠️ Format salah. Ketik /bantuan'); return
    try:
        d = parse_input(raw)
        sheet = get_sheet()
        komisi_int = int(str(d['komisi']).replace(',','').replace('.',''))

        # Cari baris kosong berikutnya di B6:B55
        all_vals_b = sheet.get('B6:B55')
        next_row = 6
        for i, v in enumerate(all_vals_b):
            if v and v[0]:
                next_row = 6 + i + 1

        # Nomor urut
        next_no = next_row - 5

        # Struktur kolom: A=No, B=Tanggal, C=Properti, D=Bulan(formula),
        # E=Komisi, F=Ag1Nama, G=Ag1Rp, H=Ag1%(formula),
        # I=Ag2Nama, J=Ag2Rp, K=Ag2%(formula),
        # L=Ag3Nama, M=Ag3Rp, N=Ag3%(formula),
        # O=Ag4Nama, P=Ag4Rp, Q=Ag4%(formula)
        # R=Status, S=Ket

        agents = (d['agents'] + [(None, None)] * 4)[:4]

        def rp(v):
            if not v: return ''
            try: return int(str(v).replace(',','').replace('.',''))
            except: return ''

        row = [
            next_no,           # A - No
            d['tanggal'],      # B - Tanggal
            d['properti'],     # C - Properti
            '',                # D - Bulan (formula, kosongkan)
            komisi_int,        # E - Komisi
            agents[0][0] or '',# F - Agent1 Nama
            rp(agents[0][1]),  # G - Agent1 Rp
            '',                # H - Agent1 % (formula)
            agents[1][0] or '',# I - Agent2 Nama
            rp(agents[1][1]),  # J - Agent2 Rp
            '',                # K - Agent2 % (formula)
            agents[2][0] or '',# L - Agent3 Nama
            rp(agents[2][1]),  # M - Agent3 Rp
            '',                # N - Agent3 % (formula)
            agents[3][0] or '',# O - Agent4 Nama
            rp(agents[3][1]),  # P - Agent4 Rp
            '',                # Q - Agent4 % (formula)
            d['status'],       # R - Status
            d['ket'],          # S - Keterangan
        ]

        sheet.insert_row(row, next_row, value_input_option='USER_ENTERED')

        agents_txt = '\n'.join([f'  • {n}: Rp {rp(r):,}' for n,r in d['agents'] if n])
        reply = (
            f'✅ Tersimpan!\n\n'
            f'🏠 {d["properti"]}\n'
            f'💰 Komisi: Rp {komisi_int:,}\n'
            f'👤 Agent:\n{agents_txt}\n'
            f'📋 Status: {d["status"]}'
        )
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

async def cek(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    try:
        sheet = get_sheet()
        rows = sheet.get('B6:E55')
        if not rows:
            await update.message.reply_text('Belum ada data.'); return
        filled = [r for r in rows if r and len(r) > 1 and r[1]]
        last5 = filled[-5:]
        msg = '📋 5 Transaksi Terakhir:\n\n'
        for r in reversed(last5):
            try:
                komisi = int(str(r[3]).replace(',','').replace('.',''))
                msg += f'🏠 {r[1]}\n💰 Rp {komisi:,}\n\n'
            except:
                msg += f'🏠 {r[1]}\n\n'
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

async def total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    try:
        sheet = get_sheet()
        rows = sheet.get('E6:E55')
        total_komisi = 0
        count = 0
        for r in rows:
            if r and r[0]:
                try:
                    total_komisi += int(str(r[0]).replace(',','').replace('.',''))
                    count += 1
                except:
                    pass
        msg = (
            f'📊 TOTAL KOMISI 2026\n\n'
            f'Jumlah Transaksi: {count}\n'
            f'Total Komisi: Rp {total_komisi:,}'
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler('start',   start))
app.add_handler(CommandHandler('bantuan', bantuan))
app.add_handler(CommandHandler('input',   input_data))
app.add_handler(CommandHandler('cek',     cek))
app.add_handler(CommandHandler('total',   total))
print('Bot berjalan...')
app.run_polling()
