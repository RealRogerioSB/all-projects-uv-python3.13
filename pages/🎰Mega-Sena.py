import locale
from datetime import date

import pandas as pd
import streamlit as st

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

minhas_apostas: list[str] = [
	"05 15 26 27 46 53",  # aposta n.° 1
	"03 12 19 20 45 47",  # aposta n.° 2
	"01 10 17 41 42 56",  # aposta n.° 3
	"02 10 13 27 53 55",  # aposta n.° 4
	"06 07 08 11 43 56",  # aposta n.° 5
	"08 10 14 25 33 34",  # aposta n.° 6
	"05 11 16 40 43 57",  # aposta n.° 7
	"04 05 08 13 17 38",  # aposta n.° 8
	"13 24 32 49 51 60",  # aposta n.° 9
	"11 16 19 43 58 60",  # aposta n.° 10
	"03 05 10 20 35 46",  # aposta n.° 11
	"02 09 10 19 31 57",  # aposta n.° 12
	"04 18 20 21 39 57",  # aposta n.° 13
	"02 11 22 36 49 60",  # aposta n.° 14
	"02 21 39 48 52 57",  # aposta n.° 15
	"14 41 45 50 54 59",  # aposta n.° 16
	"13 20 22 25 28 39",  # aposta n.° 17
	"01 16 21 34 49 54",  # aposta n.° 18
]

months: list[str] = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
					 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


@st.cache_data(show_spinner="⏳Obtendo os dados, aguarde...", ttl=1)
def load_megasena() -> pd.DataFrame:
	df: pd.DataFrame = pd.read_excel(io=st.session_state["xlsx_file"], engine="openpyxl")

	df["Concurso"] = df["Concurso"].astype(str).str.zfill(4)
	df["Data do Sorteio"] = pd.to_datetime(df["Data do Sorteio"], format="%d/%m/%Y")
	df["bolas"] = df.apply(lambda b: f"{b['Bola1']:02} {b['Bola2']:02} {b['Bola3']:02} "
									 f"{b['Bola4']:02} {b['Bola5']:02} {b['Bola6']:02} ", axis=1)

	for coluna in ["Rateio 6 acertos", "Rateio 5 acertos", "Rateio 4 acertos"]:
		df[coluna] = df[coluna].astype(str).replace(r"\D", "", regex=True).astype(float) / 100
		df[coluna] = df[coluna].apply(lambda f: f"{locale.currency(f, grouping=True)}")
		df[f"{coluna.split()[1]}x"] = df.apply(lambda f: f"{f[f'Ganhadores {coluna.split()[1]} acertos']}x de "
														 f"{f[f'Rateio {coluna.split()[1]} acertos']}", axis=1)

	df = df[["Concurso", "Data do Sorteio", "bolas", "6x", "5x", "4x"]]
	df.columns = ["id_sorteio", "dt_sorteio", "bolas", "6x", "5x", "4x"]
	df = df.sort_values(by=["id_sorteio", "dt_sorteio"], ignore_index=True)

	return df


st.file_uploader("Importar", type=["xlsx"], key="xlsx_file", label_visibility="hidden", width=250)

if st.session_state["xlsx_file"] and st.session_state["xlsx_file"].name == "Mega-Sena.xlsx":
	megasena: pd.DataFrame = load_megasena()

	tab1, tab2, tab3, tab4 = st.tabs(["**Minhas apostas**", "**Apostas Sorteadas**",
									  "**Sua aposta da Mega-Sena**", "**Mega-Sena da Virada**"])

	with tab1:
		col1, col2 = st.columns([1.3, 2.8])

		with col1:
			minhas: list[str] = [f"Aposta {x:02} -> {" ".join(aposta.split())}" for x, aposta in
								 enumerate(minhas_apostas, 1)]

			st.data_editor(
				data=minhas,
				width="content",
				hide_index=True,
				column_config={"value": st.column_config.TextColumn(label="Minhas Apostas")},
				key="de_apostas",
				row_height=25,
			)

		with col2:
			for r in range(6, 3, -1):
				st.write(f"**Acerto de {r} bolas**")

				mega_copy: dict[str, list[int | str]] = {"Concurso": [], "Data do Sorteio": [],
														 "Bolas Acertadas": [], "Sua aposta n.°": []}

				for row in megasena[["id_sorteio", "dt_sorteio", "bolas"]].copy().itertuples(index=False, name=None):
					for aposta in minhas_apostas:
						acertos: set[int] = set(map(int, aposta.split()))

						match: set[int] = set(map(int, row[2].split())) & acertos

						if len(match) == r:
							mega_copy["Concurso"].append(str(row[0]).zfill(4))
							mega_copy["Data do Sorteio"].append(row[1].strftime("%x (%a)"))
							mega_copy["Bolas Acertadas"].append(" ".join(f"{n:02}" for n in sorted(match)))
							mega_copy["Sua aposta n.°"].append(minhas_apostas.index(aposta) + 1)

				st.columns([2.5, 0.5])[0].dataframe(
					data=mega_copy,
					width="content",
					hide_index=True,
					column_config={"Bolas Acertadas": st.column_config.ListColumn("Bolas Acertadas")},
					row_height=25,
				)

	with tab2:
		col1, col2 = st.columns([1, 4])

		with col1:
			st.select_slider("**Mês:**", options=months[1:], value=months[date.today().month], key="mês")
			st.slider("**Ano:**", min_value=1996, max_value=date.today().year, value=date.today().year, key="ano")

		with col2:
			all_mega: pd.DataFrame = megasena[megasena["dt_sorteio"].dt.year.eq(st.session_state["ano"]) &
											  megasena["dt_sorteio"].dt.month.eq(
												  months.index(st.session_state["mês"]))].copy()
			all_mega["dt_sorteio"] = all_mega["dt_sorteio"].dt.strftime("%x (%a)")

			st.data_editor(
				data=all_mega,
				width="content",
				hide_index=True,
				column_config={
					"id_sorteio": st.column_config.TextColumn("Concurso", pinned=True),
					"dt_sorteio": st.column_config.TextColumn("Data do Sorteio", pinned=True),
					"bolas": st.column_config.ListColumn("Bolas Sorteadas"),
					"6x": st.column_config.TextColumn("6x"),
					"5x": st.column_config.TextColumn("5x"),
					"4x": st.column_config.TextColumn("4x"),
				},
				key="de_all_mega",
				row_height=25,
			)

	with tab3:
		st.columns(5)[0].text_input("Sua aposta:", key="sua_aposta", placeholder="01 02 03 04 05 06")

		st.button("**Acertei?**", key="btn_acertas", type="primary", icon=":material/person_play:")

		mega_copy2: dict[str, list[int | str]] = {"Concurso": [], "Data de Sorteio": [],
												  "Bolas Sorteadas": [], "Seus Acertos": []}

		if st.session_state["btn_acertas"]:
			if st.session_state["sua_aposta"]:
				sua_aposta: set[int] = set(map(int, st.session_state["sua_aposta"].split()))

				with st.spinner("Obtendo os acertos de apostas, aguarde...", show_time=True):
					for row in megasena.copy().itertuples(index=False, name=None):
						match: set[int] = set(map(int, row[2].split())) & sua_aposta

						if len(match) >= 4:
							mega_copy2["Concurso"].append(row[0])
							mega_copy2["Data de Sorteio"].append(row[1].strftime("%x (%a)"))
							mega_copy2["Bolas Sorteadas"].append(row[2])
							mega_copy2["Seus Acertos"].append(len(match))

				st.columns([2.5, 1, 1])[0].data_editor(
					data=mega_copy2,
					width="content",
					hide_index=True,
					column_config={"Bolas Sorteadas": st.column_config.ListColumn("Bolas Sorteadas")},
					row_height=25,
				)
				st.button("**Limpar**", type="primary", icon=":material/mop:")
			else:
				st.toast("**Preencha suas bolas!**", icon=":material/warning:")

	with tab4:
		mega_da_virada: pd.DataFrame = megasena.copy()
		mega_da_virada["ano"] = mega_da_virada["dt_sorteio"].dt.year
		mega_da_virada = mega_da_virada[mega_da_virada["dt_sorteio"]. \
			isin(mega_da_virada[mega_da_virada["ano"] != pd.Timestamp.now().year]. \
				groupby(["ano"])["dt_sorteio"].transform("max"))].reset_index(drop=True). \
					drop(["ano"], axis=1)
		mega_da_virada["dt_sorteio"] = mega_da_virada["dt_sorteio"].dt.strftime("%x (%a)")

		st.data_editor(
			data=mega_da_virada,
			width="content",
			hide_index=True,
			column_config={
				"id_sorteio": st.column_config.TextColumn("Concurso", pinned=True),
				"dt_sorteio": st.column_config.TextColumn("Data do Sorteio", pinned=True),
				"bolas": st.column_config.ListColumn("Bolas Sorteadas"),
				"6x": st.column_config.TextColumn("6x"),
				"5x": st.column_config.TextColumn("5x"),
				"4x": st.column_config.TextColumn("4x"),
			},
			key="de_mega_da_virada",
			row_height=25,
		)
