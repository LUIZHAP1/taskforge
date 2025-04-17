
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
