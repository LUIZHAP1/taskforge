
=== Instru��es TaskForge Stellar Omega Final ===

1. Execute: python setup.py
2. Configure as credenciais quando solicitado:
   - Gmail:
     - Acesse https://myaccount.google.com/security
     - Ative "Verifica��o em duas etapas"
     - Em "Senhas de app", gere uma senha para "E-mail"
   - Twilio:
     - Crie conta em https://www.twilio.com/try-twilio
     - Copie Account SID e Auth Token
     - Ative WhatsApp sandbox em "Messaging > Try WhatsApp"
     - Envie "join <c�digo>" para +14155238886
   - Google Drive:
     - Crie projeto em https://console.cloud.google.com/
     - Ative Google Drive API
     - Crie conta de servi�o, baixe JSON
     - Crie pasta no Drive, compartilhe com e-mail da conta de servi�o
     - Copie ID da pasta da URL
3. Execute: python omega.py

=== Problemas? ===
- Veja omega.log
- Reexecute: python setup.py
