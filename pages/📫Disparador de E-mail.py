import mimetypes
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def validar_email(emails: str) -> bool:
	return all(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", mail) for mail in emails.split(", "))


with st.columns(2)[0], st.form("disparar_email", clear_on_submit=True, border=False):
	to_addr: str = st.text_input("**Para: :red[*]**", icon=":material/email:")
	to_addr = ", ".join([mail for mail in to_addr.lower().replace(" ", "").split(",")])

	cc_addr: str = st.text_input("**Cc:**", icon=":material/email:")
	cc_addr = ", ".join([mail for mail in cc_addr.lower().replace(" ", "").split(",")])

	subject: str = st.text_input("**Assunto: :red[*]**", icon=":material/subject:")
	body: str = st.text_area("**Corpo: :red[*]**")

	files: list[UploadedFile] = st.file_uploader("**Anexar:**", accept_multiple_files=True)

	with st.container(horizontal_alignment="center"):
		if st.form_submit_button("Enviar", type="primary", icon=":material/send:", width="content"):
			if not all([to_addr, subject, body]):
				st.toast("**Precisa preencher todos campos :red[*]...**", icon=":material/warning:")
				st.stop()

			if not validar_email(", ".join(mail for mail in [to_addr, cc_addr] if mail)):
				st.toast("**Um ou mais e-mails não são válidos...**", icon=":material/warning:")
				st.stop()

			msg: MIMEMultipart = MIMEMultipart()
			msg["From"] = st.secrets["REMETENTE"]
			msg["To"] = to_addr
			msg["Cc"] = cc_addr
			msg["Subject"] = subject
			msg.add_header("Content-Type", "text/plain")
			msg.attach(MIMEText(body, "plain"))

			if files:
				for file in files:
					mime_type, _ = mimetypes.guess_type(file.name)
					if mime_type is None:
						mime_type = "application/octet-stream"
					main_type, sub_type = mime_type.split("/")
					part: MIMEBase = MIMEBase(main_type, sub_type)
					part.set_payload(file.read())
					encoders.encode_base64(part)
					part.add_header("Content-Disposition", f"attachment; filename={file.name!r}")
					msg.attach(part)

			with smtplib.SMTP(host="smtp.gmail.com", port=587) as smtp_server:
				smtp_server.starttls()
				smtp_server.login(st.secrets["REMETENTE"], st.secrets["PASSWORD"])
				try:
					with st.spinner("**⏳Enviando e-mail, aguarde...**", show_time=True):
						smtp_server.send_message(msg)
				except smtplib.SMTPAuthenticationError:
					st.toast("**Não foi possível enviar, erro de autenticação**", icon=":material/warning:")
				except smtplib.SMTPConnectError:
					st.toast("**Não foi possível enviar, erro de conexão**", icon=":material/warning:")
				except smtplib.SMTPDataError:
					st.toast("**Não foi possível enviar, erro ao enviar dados**", icon=":material/warning:")
				except smtplib.SMTPRecipientsRefused:
					st.toast("**Não foi possível enviar, destinatário recusado**", icon=":material/warning:")
				except smtplib.SMTPSenderRefused:
					st.toast("**Não foi possível enviar, remetente recusado**", icon=":material/warning:")
				except smtplib.SMTPServerDisconnected:
					st.toast("**Não foi possível enviar, desconexão abrupta do servidor**", icon=":material/warning:")
				except smtplib.SMTPException:
					st.toast("**Não foi possível enviar, erro SMTP genérico", icon=":material/warning:")
				else:
					st.toast("**E-mail enviado con sucesso!**", icon=":material/check_circle:")
