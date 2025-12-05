from notificacao import Notificacao


class NotificacaoSMS(Notificacao):
    def enviar_notificacao(self, cliente, mensagem):
        print(f"Enviando SMS para {cliente.nome}: {mensagem}")
