import sys
from math import ceil


class DigitoVerificador:
	def __init__(self, _value: str) -> None:
		self._value: str = _value.upper()
		self._pesos: list[int] = []
		self.digito: int = 0

	@staticmethod
	def calcula_ascii(_caracter: str) -> int:
		return ord(_caracter) - 48

	def calcula_soma(self) -> int:
		_tamanho_range: int = len(self._value)
		_num_range: int = ceil(_tamanho_range / 8)

		for i in range(_num_range):
			self._pesos.extend(range(2, 10))

		self._pesos = self._pesos[:_tamanho_range]
		self._pesos.reverse()
		sum_of_products: int = sum(a * b for a, b in zip(map(self.calcula_ascii, self._value), self._pesos))
		return sum_of_products

	def calcula(self) -> int:
		mod_sum: int = self.calcula_soma() % 11
		return 0 if mod_sum < 2 else 11 - mod_sum


if __name__ == "__main__":
	value: str = sys.argv[1]
	dv: DigitoVerificador = DigitoVerificador(value)
	print(dv.calcula())
