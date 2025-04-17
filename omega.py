import asyncio
import sqlite3
import os
import smtplib
import ssl
import requests
import json
import zipfile
from email.mime.text import MIMEText
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from twilio.rest import Client
from cryptography.fernet import Fernet
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from prophet import Prophet
import pandas as pd
import re
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Configuração de logging
logger.remove()
logger.add('omega.log', rotation='10 MB', retention='7 days', compression='zip', format='{time} {level} {message}')
logger.info('TaskForge Stellar Omega Final iniciado')

# Configurações
DB_PATH = 'omega.db'
TEST_IMG = 'test.png'
ENCRYPT_KEY = Fernet.generate_key()
cipher = Fernet(ENCRYPT_KEY)
scheduler = AsyncIOScheduler()
CREDENTIALS_FILE = 'credentials.json'

# Configuração de credenciais
def save_credentials():
    creds = {
        'email_user': input('Digite seu e-mail Gmail (ex.: seu_email@gmail.com): '),
        'email_pass': input('Digite sua senha de app do Gmail (veja README.txt): '),
        'twilio_sid': input('Digite seu Twilio Account SID (veja README.txt): '),
        'twilio_token': input('Digite seu Twilio Auth Token (veja README.txt): '),
        'whatsapp': input('Digite seu número WhatsApp (ex.: +5511999999999): '),
        'google_creds': input('Cole o conteúdo do arquivo JSON do Google Drive (veja README.txt): '),
        'drive_folder': input('Digite o ID da pasta do Google Drive (veja README.txt): ')
    }
    for key, value in creds.items():
        if not value.strip():
            print(f"Erro: {key} não pode ser vazio. Tente novamente.")
            return save_credentials()
    with open(CREDENTIALS_FILE, 'wb') as f:
        f.write(cipher.encrypt(json.dumps(creds).encode()))
    logger.info('Credenciais salvas')
    return creds

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        return save_credentials()
    try:
        with open(CREDENTIALS_FILE, 'rb') as f:
            return json.loads(cipher.decrypt(f.read()).decode())
    except:
        print("Erro ao carregar credenciais. Reconfigurando...")
        return save_credentials()

def download_test_image():
    if not os.path.exists(TEST_IMG):
        try:
            url = 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c'
            with open(TEST_IMG, 'wb') as f:
                f.write(requests.get(url).content)
            logger.info('Imagem test.png baixada')
        except:
            logger.warning('Falha ao baixar test.png')

# Inicializa banco de dados
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT, status TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, contacted INTEGER, data BLOB)''')
        c.execute('''CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY, device TEXT, state TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY, data TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS trends (id INTEGER PRIMARY KEY, trend TEXT, score REAL, timestamp TEXT)''')
        conn.commit()
    logger.info('Banco de dados inicializado')

# IoT Simulado
async def manage_iot(device='casa/luz'):
    try:
        weather = await search_online('previsão tempo hoje')
        state = 'OFF' if 'sol' in weather.lower() else 'ON'
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO devices (device, state, timestamp) VALUES (?, ?, ?)', 
                      (device, state, datetime.now().isoformat()))
            conn.commit()
        logger.info(f'IoT: {device} configurado para {state}')
        return state
    except Exception as e:
        logger.error(f'Erro IoT: {e}')
        return 'Erro'

# E-mail
async def send_email(to_email, subject, body):
    creds = load_credentials()
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = creds['email_user']
    msg['To'] = to_email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(creds['email_user'], creds['email_pass'])
            server.send_message(msg)
        logger.info(f'E-mail enviado para {to_email}')
    except Exception as e:
        logger.error(f'Erro e-mail: {e}')

# WhatsApp
async def send_whatsapp(to_number, body):
    creds = load_credentials()
    client = Client(creds['twilio_sid'], creds['twilio_token'])
    try:
        client.messages.create(body=body, from_='whatsapp:+14155238886', to=f'whatsapp:{to_number}')
        logger.info(f'WhatsApp enviado para {to_number}')
    except Exception as e:
        logger.error(f'Erro WhatsApp: {e}')

# Busca online
async def search_online(query):
    try:
        response = requests.get(f'https://api.duckduckgo.com/?q={query}&format=json')
        data = response.json()
        result = data.get('Abstract', '') or data.get('RelatedTopics', [{}])[0].get('Text', '')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO trends (trend, score, timestamp) VALUES (?, ?, ?)', 
                      (query, 1.0, datetime.now().isoformat()))
            conn.commit()
        return result
    except Exception as e:
        logger.error(f'Erro busca: {e}')
        return ''

# Análise de imagem (simplificada)
async def analyze_image(image_path=TEST_IMG):
    try:
        img = Image.open(image_path)
        colors = img.getcolors(maxcolors=1000) or [(0, (255, 255, 255))]
        dominant_color = max(colors, key=lambda x: x[0])[1]
        result = f'Cor dominante: RGB{dominant_color}'
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO knowledge (data, timestamp) VALUES (?, ?)', 
                      (result, datetime.now().isoformat()))
            conn.commit()
        return result
    except Exception as e:
        logger.error(f'Erro imagem: {e}')
        return 'Erro na análise'

# Prospecção
async def prospect_clients():
    try:
        response = requests.get('https://www.reddit.com/r/automation/.json', headers={'User-Agent': 'Mozilla/5.0'})
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', response.text)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            for email in emails:
                encrypted_email = cipher.encrypt(email.encode()).decode()
                c.execute('INSERT OR IGNORE INTO users (email, contacted, data) VALUES (?, ?, ?)', 
                          (encrypted_email, 0, encrypted_email))
            c.execute('SELECT email FROM users WHERE contacted = 0 LIMIT 1')
            if row := c.fetchone():
                decrypted_email = cipher.decrypt(row[0].encode()).decode()
                await send_email(decrypted_email, 'Oferta TaskForge', 'Automatize por R$ 40!')
                c.execute('UPDATE users SET contacted = 1 WHERE email = ?', (row[0],))
                conn.commit()
        logger.info(f'Prospecção concluída: {len(emails)} e-mails encontrados')
    except Exception as e:
        logger.error(f'Erro prospecção: {e}')

# Marketplace
async def run_marketplace():
    creds = load_credentials()
    tasks = ['E-mail: R$ 20', 'WhatsApp: R$ 40']
    for task in tasks:
        await send_whatsapp(creds['whatsapp'], f'Tarefa: {task}')
    logger.info('Marketplace atualizado')

# Backup
async def backup_db():
    creds = load_credentials()
    backup_file = f'backup_{datetime.now().strftime("%Y%m%d")}.zip'
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_PATH)
        creds_json = json.loads(creds['google_creds'])
        credentials = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': os.path.basename(backup_file), 'parents': [creds['drive_folder']]}
        media = MediaFileUpload(backup_file, mimetype='application/zip')
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(backup_file)
        logger.info('Backup enviado ao Google Drive')
    except Exception as e:
        logger.error(f'Erro backup: {e}')

# Previsão de demanda
async def predict_demand():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT timestamp, COUNT(*) as count FROM users GROUP BY date(timestamp)')
            df = pd.DataFrame(c.fetchall(), columns=['ds', 'y'])
            if len(df) < 2:
                return 'Oferta padrão: R$ 40 (poucos dados)'
            df['ds'] = pd.to_datetime(df['ds'])
            model = Prophet()
            model.fit(df)
            future = model.make_future_dataframe(periods=1)
            forecast = model.predict(future)
            return f'Oferta projetada: {forecast["yhat"].iloc[-1]:.2f}'
    except Exception as e:
        logger.error(f'Erro previsão: {e}')
        return 'Oferta padrão: R$ 40'

# Loop principal
async def main_loop():
    download_test_image()
    init_db()
    while True:
        try:
            await manage_iot()
            await prospect_clients()
            await analyze_image()
            creds = load_credentials()
            await send_email('cliente@exemplo.com', 'TaskForge', await predict_demand())
            await run_marketplace()
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f'Erro loop: {e}')
            await asyncio.sleep(60)

# Agendamento
scheduler.add_job(backup_db, 'interval', hours=24)
scheduler.start()

if __name__ == '__main__':
    asyncio.run(main_loop())