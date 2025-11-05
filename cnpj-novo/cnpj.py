import re
import sys

from dv import DigitoVerificador


class CNPJ:
	def __init__(self, _input_cnpj: str) -> None:
		try:
			_cnpj_valido = self.__valida_formato(_input_cnpj)
			if _cnpj_valido:
				self.cnpj = self.__remove_pontuacao(_input_cnpj)
			else:
				raise Exception("CNPJ não está no padrão aa.aaa.aaa/aaaa-dd (Para validação) "
								"ou aa.aaa.aaa/aaaa (Para geração do DV)")
		except Exception as e1:
			print(e1)
			sys.exit()

	def __remove_digitos_cnpj(self) -> None:
		if len(self.cnpj) == 14:
			self.cnpj_sem_dv = self.cnpj[0:-2]
		elif len(self.cnpj) == 12:
			self.cnpj_sem_dv = self.cnpj
		else:
			raise Exception("CNPJ com tamanho inválido!")

	@staticmethod
	def __remove_pontuacao(_input: str) -> str:
		return "".join(x for x in _input if x not in "./-")

	def valida(self) -> bool:
		self.__remove_digitos_cnpj()
		_dv: str = self.gera_dv()
		return "%s%s" % (self.cnpj_sem_dv, _dv) == self.cnpj

	def gera_dv(self) -> str:
		self.__remove_digitos_cnpj()
		dv1: DigitoVerificador = DigitoVerificador(self.cnpj_sem_dv)
		dv1char: str = "{}".format(dv1.calcula())
		dv2: DigitoVerificador = DigitoVerificador(self.cnpj_sem_dv + dv1char)
		dv2char: str = "{}".format(dv2.calcula())
		return "%s%s" % (dv1char, dv2char)

	@staticmethod
	def __valida_formato(_cnpj: str):
		return re.match(r"(^([A-Z]|\d){2}\.([A-Z]|\d){3}\.([A-Z]|\d){3}\/([A-Z]|\d){4}(\-\d{2})?$)", _cnpj)


if __name__ == "__main__":
	try:
		if len(sys.argv) < 2:
			raise Exception("Formato inválido do CNPJ.")
		_exec: str = sys.argv[1].upper()
		_input: str = sys.argv[2]

		cnpj: CNPJ = CNPJ(_input)

		if _exec == '-V':
			print(cnpj.valida())
		elif _exec == '-DV':
			print(cnpj.gera_dv())
		else:
			raise Exception("Opção inválida passada, as válidas são: -v para validar, -dv para gerar digito validador.")
		sys.exit()
	except Exception as e2:
		print(e2)
		sys.exit()
