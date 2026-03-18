import os, json, re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ── KONFIGURASI ──
BOT_TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
ALLOWED_USER = int(os.environ.get('MY_TELEGRAM_ID', '0'))
CREDS_JSON = os.environ.get('GOOGLE_CREDS_JSON')

# ── KONEKSI GOOGLE SHEETS ──
def get_sheet():
    creds_dict = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).sheet1

# ── PARSE PESAN ──
def parse_input(text):
    parts = [x.strip() for x in text.split('|')]
    data = {
        'tanggal': datetime.now().strftime('%d/%m/%Y'),
        'properti': parts[0] if len(parts) > 0 else '',
        'komisi': parts[1] if len(parts) > 1 else '',
        'agents': [], 'status': 'Proses', 'ket': ''
    }
    for p in parts[2:]:
        if ':' in p:
            k, v = p.split(':', 1)
            if k.strip().lower() == 'status': data['status'] = v.strip()
            elif k.strip().lower() == 'ket': data['ket'] = v.strip()
            else: data['agents'].append((k.strip(), v.strip()))
    return data

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    await update.message.reply_text(
        '🏠 Komisi Bot aktif!\n\nPerintah tersedia:\n'
        '/input - Input transaksi baru\n'
        '/cek - Lihat 5 transaksi terakhir\n'
        '/total - Total komisi keseluruhan\n'
        '/bantuan - Cara penggunaan'
    )

async def bantuan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    msg = ('📖 CARA INPUT:\n\n'
           '/input Nama Properti | Komisi | Nama:Rp | Status:Lunas\n\n'
           '📌 Contoh:\n'
           '/input Ciragil I No5 | 165000000 | Riza:115500000 | Status:Lunas')
    await update.message.reply_text(msg)

async def input_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        await update.message.reply_text('⛔ Akses ditolak.'); return
    raw = update.message.text.replace('/input', '').strip()
    if not raw:
        await update.message.reply_text('⚠️ Format salah. Ketik /bantuan'); return
    try:
        d = parse_input(raw)
        sheet = get_sheet()
        row = [d['tanggal'], d['properti'], d['komisi']]
        for nama, rp in (d['agents'] + [(None,None)]*4)[:4]:
            row.extend([nama or '', rp or ''])
        row.extend([d['status'], d['ket']])
        sheet.append_row(row)
        agents_txt = '\n'.join([f' • {n}: Rp {int(r):,}' for n,r in d['agents'] if n])
        reply = (f'✅ Tersimpan!\n\n'
                 f'🏠 {d["properti"]}\n'
                 f'💰 Komisi: Rp {int(d["komisi"]):,}\n'
                 f'👤 Agent:\n{agents_txt}\n'
                 f'📋 Status: {d["status"]}')
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

async def cek(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    try:
        sheet = get_sheet()
        rows = sheet.get_all_values()[1:]
        if not rows: await update.message.reply_text('Belum ada data.'); return
        last5 = rows[-5:]
        msg = '📋 5 Transaksi Terakhir:\n\n'
        for r in reversed(last5):
            msg += f'🏠 {r[1]}\n💰 Rp {int(r[2]):,} | {r[11]}\n\n'
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

async def total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER: return
    try:
        sheet = get_sheet()
        rows = sheet.get_all_values()[1:]
        total_komisi = sum(int(r[2]) for r in rows if r[2].isdigit())
        msg = (f'📊 TOTAL KOMISI 2026\n\n'
               f'Jumlah Transaksi: {len(rows)}\n'
               f'Total Komisi: Rp {total_komisi:,}')
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('bantuan', bantuan))
app.add_handler(CommandHandler('input', input_data))
app.add_handler(CommandHandler('cek', cek))
app.add_handler(CommandHandler('total', total))
print('Bot berjalan...')
app.run_polling()
