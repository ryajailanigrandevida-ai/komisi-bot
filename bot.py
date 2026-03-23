import os, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

BOT_TOKEN    = os.environ.get('BOT_TOKEN')
SHEET_ID     = os.environ.get('SHEET_ID', '1T3hnFxZX8QH7ItnWN6Eg0MpzmubR9TUKBXCHOOQhNJ4')
ALLOWED_USER = int(os.environ.get('MY_TELEGRAM_ID', '0'))

PRIVATE_KEY = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC+SOj7l4RK0v4A\n"
    "yC9typ/0wIIOvvnFJYAvfXHBx71GJ4F+W4BUY++d2nm7Mm//kD+sYQ/6PgBZreGL\n"
    "6l89MNtvKw6wcADRxLJf9wLb/ZSrv+qnp6TMuYVtVH5S1fbt4VzOEK6vYT80jbII\n"
    "k8l6ZuwxP4oP0cV6txUNru3uumXW2jAYmortf62EunENgrnpzIiSK5t6TLWPXJ8Z\n"
    "bV/tj/yMBuWo2qYbvcDL87q5yruwUtn6+FrBC4ImxEahLWs6pHw+o7UepSqQqE/J\n"
    "rHwPWLGdjxRKxX0JGD3IXRrGFxNjIBljc8xBLR7xXU0q9rqM0kc3EWk3fFi9MXHB\n"
    "QYG7Ie3VAgMBAAECggEAIkkf1alU2GiRBNINHbK7RI3lQUPu3DNoF+Z590kGlRvs\n"
    "LLjO9CW3mJEziuPJI1q55lTs3JGMXZxDfgLiWzOw7iRrdqYPt7xByaHHvZzAy3t+\n"
    "i+vceVjaLjthsYpE/lKzdpux5f7XNSBs2jfKv0fJOgxxU21gMD7Jx9fjnjauv9nr\n"
    "uy92mQ7dKjj+Pc8pK6Oz/tW2Cn13tH6cHhthVKzZfmWIhClM2U702ElRQyrrkmH+\n"
    "JXmjzwwdVzMaCvV+QYvwsbCqQ0fLItppiI2yuY1OITs33pNFlptRW7cs8DtJfKux\n"
    "ZC674jtQO+vxdC13OU7Bd1wP4AVDa8McjfYLn78zlwKBgQDt3QxBr/qG9Qro2mJ9\n"
    "YQJD5DGFvtcYs3vk0OtL+YZutf0fe6LD1cTpF8HjlwM+TxTU09Q/GBWCN874YtDK\n"
    "nz2F7EWRZRHMnJqio4/oGMCzBdG8eDi2Egd3j9FTZRQfwYcL7By1AYwcoGlSA5Vp\n"
    "+BORcC26ZPdv0gF2ufJQrpPenwKBgQDMyye/aejIqpYU0OChPS+xI+ssFxCrcGVZ\n"
    "LUz3CvAF5AVPYXVjSNO8Msxbx+2eU2jTRP+B2icmLgOC26IuRQGFAFCMMtkypVAr\n"
    "Urj881+q8T7zV+g0wzXu8dldnlZeb2rPLyrG4laxcoUEreQec9uf0vmYeB0Ocexu\n"
    "jlNqzqSDCwKBgGl4zuqBodEd7wx5aZq23U5FbUAk8zPcwl8f1HYH2vhUcjz3kaDM\n"
    "tVe2VR8Z4zJJ1q7YjxC7GS54mKnDB1oRajJsJhzmeBIGjvr3E+SStT+soOe1V1BE\n"
    "hlMZznPwKhA6vCspM0F/wiUfbBQVyrcGbYbb+yrfgmhu8n82zJ/CCYd5AoGAKiUY\n"
    "zfSOulUYw7nksGn2GZ9Js24fuRhNUxfWgfSXRq8RRK/Kx57iLBXMJoszZGTH6sqF\n"
    "RoTNj7bidBic/Kao1GUnLmL8fca1g+TnOu8e3f/9s3iAyfLuc3kEAZcnMRH+yhpr\n"
    "1DgaHTRzGW5rxrSTGwYA5Za6bBGX1XymwBE8m9cCgYAgPkl30l+7G2n/8cx1D2Ii\n"
    "TLpQPhtcYoeXTgHWl5OB9jU7qxhA/KU8pLDoEDDiJNti4bOmaF9qG1Dt1pN0aAuv\n"
    "PL22hKq/YF5flo8ewntOAMMSqhUbCy/cCG2rFqW3R3eQ0wEt4m4MB/OLXfe5tYJN\n"
    "VbwPsIXMnRsH8BINVtmrXA==\n"
    "-----END PRIVATE KEY-----\n"
)

CREDS_DICT = {
    "type": "service_account",
    "project_id": "komisi-bot",
    "private_key_id": "8ca8a00db5813cff73dd6bc7793b3e3ec3dc13b4",
    "private_key": PRIVATE_KEY,
    "client_email": "komisi-bot@komisi-bot.iam.gserviceaccount.com",
    "client_id": "112571321627461279166",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/komisi-bot%40komisi-bot.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

def get_sheet():
    creds = Credentials.from_service_account_info(
        CREDS_DICT,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)
    try:
        ws = spreadsheet.get_worksheet_by_id(2041071178)
    except:
        ws = spreadsheet.worksheet("Transaksi Komisi")
    return ws

def find_next_empty_row(sheet):
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values):
        if i < 5:
            continue
        if not any(row[j] for j in [1, 2, 4] if j < len(row)):
            return i + 1
    return len(all_values) + 1

def parse_input(text):
    parts = [x.strip() for x in text.split("|")]
    data = {
        "tanggal": datetime.now().strftime("%d/%m/%Y"),
        "properti": parts[0] if len(parts) > 0 else "",
        "komisi": parts[1] if len(parts) > 1 else "0",
        "agents": [],
        "status": "Lunas",
        "ket": ""
    }
    for p in parts[2:]:
        if ":" in p:
            k, v = p.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k.lower() == "status":
                data["status"] = v
            elif k.lower() in ["ket", "keterangan"]:
                data["ket"] = v
            else:
                data["agents"].append((k, v))
    return data

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        return
    await update.message.reply_text(
        "Komisi Bot aktif!\n\n"
        "Perintah:\n"
        "/input  - Input transaksi baru\n"
        "/cek    - 5 transaksi terakhir\n"
        "/total  - Total komisi\n"
        "/bantuan - Cara penggunaan"
    )

async def bantuan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        return
    msg = (
        "CARA INPUT:\n\n"
        "/input Nama Properti | Komisi | Nama:Rp | Status:Lunas\n\n"
        "Contoh 1 agent:\n"
        "/input Ciragil I No5 | 165000000 | YG:115500000 | Status:Lunas\n\n"
        "Contoh banyak agent:\n"
        "/input Savyavasa 3BR | 236474000 | ND:165531800 | BS:20691475 | SB:20691475 | Status:Lunas"
    )
    await update.message.reply_text(msg)

async def input_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        await update.message.reply_text("Akses ditolak.")
        return
    raw = update.message.text.replace("/input", "", 1).strip()
    if not raw:
        await update.message.reply_text("Format salah. Ketik /bantuan")
        return
    try:
        d = parse_input(raw)
        sheet = get_sheet()
        komisi_int = int(str(d["komisi"]).replace(",", "").replace(".", "").strip())
        next_row = find_next_empty_row(sheet)
        sheet.update_cell(next_row, 2, d["tanggal"])
        sheet.update_cell(next_row, 3, d["properti"])
        sheet.update_cell(next_row, 5, komisi_int)
        agent_cols = [(6, 7), (9, 10), (12, 13), (15, 16)]
        for i, (nama, rp) in enumerate(d["agents"][:4]):
            nc, rc = agent_cols[i]
            sheet.update_cell(next_row, nc, nama)
            sheet.update_cell(next_row, rc, int(str(rp).replace(",", "").replace(".", "").strip()))
        sheet.update_cell(next_row, 30, d["status"])
        if d["ket"]:
            sheet.update_cell(next_row, 31, d["ket"])
        agents_txt = "\n".join([
            "  - " + n + ": Rp " + f"{int(str(r).replace(',','').replace('.','').strip()):,}"
            for n, r in d["agents"] if n
        ])
        reply = (
            "Tersimpan di baris " + str(next_row) + "!\n\n"
            + d["properti"] + "\n"
            "Komisi: Rp " + f"{komisi_int:,}" + "\n"
            "Agent:\n" + agents_txt + "\n"
            "Status: " + d["status"]
        )
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

async def cek(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        return
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        data_rows = [r for r in all_rows[5:] if len(r) > 2 and r[2]]
        if not data_rows:
            await update.message.reply_text("Belum ada data.")
            return
        last5 = data_rows[-5:]
        msg = "5 Transaksi Terakhir:\n\n"
        for r in reversed(last5):
            try:
                komisi = int(str(r[4]).replace(",", "").replace(".", ""))
                status = r[29] if len(r) > 29 else ""
                msg += r[2] + "\nRp " + f"{komisi:,}" + "  |  " + status + "\n\n"
            except:
                msg += r[2] + "\n\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

async def total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        return
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        data_rows = [r for r in all_rows[5:] if len(r) > 2 and r[2]]
        total_komisi = 0
        for r in data_rows:
            try:
                total_komisi += int(str(r[4]).replace(",", "").replace(".", ""))
            except:
                pass
        msg = (
            "TOTAL KOMISI 2026\n\n"
            "Jumlah Transaksi: " + str(len(data_rows)) + "\n"
            "Total Komisi: Rp " + f"{total_komisi:,}"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("bantuan", bantuan))
app.add_handler(CommandHandler("input", input_data))
app.add_handler(CommandHandler("cek", cek))
app.add_handler(CommandHandler("total", total))
print("Bot berjalan...")
app.run_polling()
