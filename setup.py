import os
import subprocess
import sys
import venv
import webbrowser

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        print(f"Sucesso: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Erro: {command}\n{e}")
        return False
    return True

def check_python():
    if sys.version_info < (3, 8):
        print("Python 3.8+ necessário. Abrindo site para download...")
        webbrowser.open('https://www.python.org/downloads/')
        input("Instale o Python e pressione Enter para continuar...")
        sys.exit(1)
    print("Python OK")

def create_venv():
    if not os.path.exists('venv'):
        print("Criando ambiente virtual...")
        venv.create('venv', with_pip=True)
    print("Ambiente virtual OK")

def activate_venv():
    if sys.platform == 'win32':
        return 'venv\\Scripts\\activate'
    return 'source venv/bin/activate'

def install_dependencies():
    print("Instalando dependências...")
    deps = [
        'requests', 'twilio', 'cryptography', 'gspread', 'google-auth',
        'apscheduler', 'pillow', 'prophet', 'pandas', 'loguru'
    ]
    for _ in range(2):  # Tenta duas vezes
        if run_command(f"{activate_venv()} && pip install {' '.join(deps)}"):
            break
    print("Dependências instaladas")

def create_readme():
    readme_content = """
=== Instruções TaskForge Stellar Omega Final ===

1. Execute: python setup.py
2. Configure as credenciais quando solicitado:
   - Gmail:
     - Acesse https://myaccount.google.com/security
     - Ative "Verificação em duas etapas"
     - Em "Senhas de app", gere uma senha para "E-mail"
   - Twilio:
     - Crie conta em https://www.twilio.com/try-twilio
     - Copie Account SID e Auth Token
     - Ative WhatsApp sandbox em "Messaging > Try WhatsApp"
     - Envie "join <código>" para +14155238886
   - Google Drive:
     - Crie projeto em https://console.cloud.google.com/
     - Ative Google Drive API
     - Crie conta de serviço, baixe JSON
     - Crie pasta no Drive, compartilhe com e-mail da conta de serviço
     - Copie ID da pasta da URL
3. Execute: python omega.py

=== Problemas? ===
- Veja omega.log
- Reexecute: python setup.py
"""
    with open('README.txt', 'w') as f:
        f.write(readme_content)
    print("README.txt criado")

def main():
    print("=== Instalador TaskForge Stellar Omega Final ===")
    check_python()
    create_venv()
    install_dependencies()
    create_readme()
    print("\nInstalação concluída!")
    print("1. Leia README.txt para configurar credenciais.")
    print("2. Execute: python omega.py")

if __name__ == '__main__':
    main()