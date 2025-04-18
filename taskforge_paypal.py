import streamlit as st
import sqlite3
import time
import smtplib
import asyncio
from email.mime.text import MIMEText
from twilio.rest import Client
from fastapi import FastAPI, Request
import uvicorn
from loguru import logger

# Configurações gerais
PAYPAL_EMAIL = "djizinluiz2@gmail.com"
DB_PATH = "omega.db"
EMAIL_USER = "seu_email@gmail.com"
EMAIL_PASS = "sua_senha"
TWILIO_SID = "seu_twilio_sid"
TWILIO_TOKEN = "seu_twilio_token"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
ADMIN_PHONE = "+5531995427684"

# Configuração do logger
logger.add("taskforge.log", rotation="500 MB")

# Inicialização do FastAPI
app = FastAPI()

# Função para lidar com erros
def handle_error(e, context=""):
    logger.error(f"Erro em {context}: {str(e)}")
    return str(e)

# Função para criar o banco de dados
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, contacted INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS earnings (task TEXT, amount REAL, date TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (amount REAL, method TEXT, date TEXT)''')
            conn.commit()
    except Exception as e:
        handle_error(e, "init_db")

# Função para salvar ganhos (apenas para pagamentos reais confirmados)
def save_earning(task, amount):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO earnings (task, amount, date) VALUES (?, ?, ?)",
                      (task, amount, time.strftime('%Y-%m-%d')))
            conn.commit()
            logger.info(f"Ganhos reais salvos: {task} - R$ {amount:.2f}")
    except Exception as e:
        handle_error(e, "save_earning")

# Função para enviar e-mails
async def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        logger.info(f"E-mail enviado para {to_email}")
    except Exception as e:
        handle_error(e, "send_email")

# Função para enviar mensagens via WhatsApp
async def send_whatsapp_message(to_number, message):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=f"whatsapp:{to_number}"
        )
        logger.info(f"Mensagem WhatsApp enviada para {to_number}: {message.sid}")
    except Exception as e:
        handle_error(e, "send_whatsapp_message")

# Função para vender pacote e gerar link de pagamento real via PayPal
async def sell_package(to_email):
    package_price = 50.0
    try:
        paypal_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={PAYPAL_EMAIL}&amount={package_price}¤cy_code=BRL&item_name=Pacote+TaskForge"
        await send_email(to_email, "Pacote TaskForge", f"Prospecção + E-mail + Relatório por R$ 50! Pague aqui: {paypal_url}")
        return {"status": "pacote vendido", "payment_link": paypal_url}
    except Exception as e:
        handle_error(e, "sell_package")
        return {"status": "falhou"}

# Função para registrar retirada (manual via PayPal)
def log_withdrawal(amount, method):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO withdrawals (amount, method, date) VALUES (?, ?, ?)", (amount, method, time.strftime('%Y-%m-%d')))
            conn.commit()
            logger.info(f"Retirada registrada: R$ {amount:.2f} via {method}")
            st.success(f"Retirada de R$ {amount:.2f} registrada! Transfira manualmente via PayPal ({PAYPAL_EMAIL}).")
    except Exception as e:
        handle_error(e, "log_withdrawal")
        st.error(f"Erro ao processar retirada: {e}")

# Função para calcular saldo real
def calculate_balances():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(amount) FROM earnings")
            total_earnings = c.fetchone()[0] or 0.0
            c.execute("SELECT SUM(amount) FROM withdrawals")
            total_withdrawals = c.fetchone()[0] or 0.0
            withdrawable_balance = max(total_earnings - total_withdrawals, 0.0)  # Garante que não seja negativo
            return total_earnings, withdrawable_balance
    except Exception as e:
        handle_error(e, "calculate_balances")
        return 0.0, 0.0

# Função principal do Streamlit
def start_everything():
    st.title("TaskForge PayPal")
    init_db()

    # Mostrar saldo real
    total_earnings, withdrawable_balance = calculate_balances()
    st.subheader(f"Saldo Total (Reais): R$ {total_earnings:.2f}")
    st.subheader(f"Saldo Disponível para Retirada (Reais): R$ {withdrawable_balance:.2f}")

    # Formulário para captar clientes reais
    st.subheader("Cadastre-se para Receber uma Oferta")
    client_email = st.text_input("Digite seu e-mail para receber uma oferta exclusiva:")
    if st.button("Cadastrar"):
        if client_email:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('INSERT OR IGNORE INTO users (email, contacted) VALUES (?, ?)', (client_email, 0))
                conn.commit()
            st.success(f"E-mail {client_email} cadastrado com sucesso! Você receberá uma oferta em breve.")
        else:
            st.error("Por favor, insira um e-mail válido.")

    # Enviar oferta para clientes reais
    st.subheader("Enviar Oferta para Cliente")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT email FROM users WHERE contacted = 0 LIMIT 1')
        if row := c.fetchone():
            email = row[0]
            if st.button(f"Enviar oferta para {email}"):
                result = asyncio.run(sell_package(email))
                if result["status"] == "pacote vendido":
                    c.execute('UPDATE users SET contacted = 1 WHERE email = ?', (email,))
                    conn.commit()
                    st.success(f"Oferta enviada para {email}! Link de pagamento: {result['payment_link']}")
                else:
                    st.error("Falha ao enviar oferta.")

    # Confirmar pagamentos reais (manual)
    st.subheader("Confirmar Pagamentos Recebidos")
    paypal_amount = st.number_input("Valor recebido no PayPal (R$)", min_value=0.0, step=0.01)
    paypal_email = st.text_input("E-mail do cliente que pagou")
    if st.button("Confirmar Pagamento"):
        if paypal_amount > 0 and paypal_email:
            save_earning("Pacote TaskForge", paypal_amount)
            st.success(f"Pagamento de R$ {paypal_amount:.2f} de {paypal_email} confirmado!")
        else:
            st.error("Insira um valor e e-mail válidos.")

    # Solicitar retirada manual via PayPal
    st.subheader("Solicitar Retirada")
    withdrawal_amount = st.number_input("Valor para Retirar (R$)", min_value=0.0, max_value=withdrawable_balance, step=0.01, value=0.0)
    if st.button("Solicitar Retirada"):
        if withdrawal_amount > 0 and withdrawal_amount <= withdrawable_balance:
            log_withdrawal(withdrawal_amount, "PayPal")
        else:
            st.error("Valor inválido ou insuficiente para retirada.")

# Função para iniciar o FastAPI em uma thread separada
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import threading
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.start()
    start_everything()