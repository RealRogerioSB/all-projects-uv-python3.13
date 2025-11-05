from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config("Teste de Funcionamento de CSV", layout="wide")

dict_sex: dict[int, str] = {0: "Feminino", 1: "Masculino"}


@st.cache_data(ttl=1)
def load_data() -> pd.DataFrame:
	df: pd.DataFrame = pd.read_csv("data/cadastro.csv", engine="pyarrow")
	df["nascimento"] = pd.to_datetime(df["nascimento"]).dt.date
	return df


@st.dialog("Novo Cadastro")
def add() -> None:
	name: str = st.text_input("Nome:")

	with st.container(horizontal=True):
		birth: date = st.date_input("Data de Nascimento:", format="DD/MM/YYYY",
									min_value=date(1900, 1, 1), width=200)
		sex: str = st.radio("Sexo:", options=list(dict_sex.keys()), index=None,
							format_func=lambda x: dict_sex.get(x), horizontal=True)

	if st.container(horizontal_alignment="center").button("Salvar", type="primary", icon=":material/save:"):
		if all([name, birth, sex is not None]):
			incluir: pd.DataFrame = pd.DataFrame({
				"nome": [name],
				"nascimento": [pd.to_datetime(birth).date()],
				"sexo": [sex]
			})
			st.session_state["cadastro"] = pd.concat([st.session_state["cadastro"], incluir], ignore_index=True)
			st.session_state["cadastro"].to_csv("data/cadastro.csv", index=False)
			st.cache_data.clear()
			st.session_state["message"] = "add"
			st.rerun()
		else:
			st.warning("**Todos campos devem ser preenchidos!**", icon=":material/warning:")


@st.dialog("Editar Cadastro")
def edit() -> None:
	select: int = int(st.session_state["editor"]["selection"]["rows"][0])

	name: str = st.text_input("Nome:", value=st.session_state["cadastro"].iloc[select]["nome"])

	with st.container(horizontal=True):
		birth: date = st.date_input("Data de Nascimento:", format="DD/MM/YYYY", min_value=date(1900, 1, 1),
									value=st.session_state["cadastro"].iloc[select]["nascimento"], width=200)
		sex: int = st.radio("Sexo:", options=list(dict_sex.keys()), format_func=lambda x: dict_sex.get(x),
							index=int(st.session_state["cadastro"].iloc[select]["sexo"]), horizontal=True)

	if st.container(horizontal_alignment="center").button("Salvar", type="primary", icon=":material/save:"):
		if all([name, birth, sex is not None]):
			st.session_state["cadastro"].iloc[select] = [name, pd.to_datetime(birth).date(), sex]
			st.session_state["cadastro"].to_csv("data/cadastro.csv", index=False)
			st.cache_data.clear()
			st.session_state["message"] = "edit"
			st.rerun()
		else:
			st.warning("**Todos campos devem ser preenchidos!**", icon=":material/warning:")


@st.dialog("Confirmação de Exclusão")
def delete() -> None:
	st.write("Tem certeza que deseja deletar o registro selecionado?")
	st.markdown("")
	with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):
		st.button("Sim", key="sim", type="primary", icon=":material/check:")
		st.button("Não", key="não", type="primary", icon=":material/cancel:")

	if st.session_state["sim"]:
		select: int = int(st.session_state["editor"]["selection"]["rows"][0])

		st.session_state["cadastro"].drop(index=select, inplace=True)
		st.session_state["cadastro"].reset_index(drop=True, inplace=True)
		st.session_state["cadastro"].to_csv("data/cadastro.csv", index=False)
		st.cache_data.clear()
		st.session_state["message"] = "delete"
		st.rerun()

	if st.session_state["não"]:
		st.rerun()


if "cadastro" not in st.session_state:
	st.session_state["cadastro"] = load_data()

st.dataframe(
	data=st.session_state["cadastro"],
	width="content",
	height=313,
	hide_index=True,
	column_config={
		"nome": st.column_config.TextColumn("Nome", width=130),
		"nascimento": st.column_config.DateColumn("Data de Nascimento", format="DD/MM/YYYY"),
		"sexo": st.column_config.SelectboxColumn("Sexo", options=list(dict_sex.keys()),
												 format_func=lambda x: dict_sex.get(x), width=120),
	},
	on_select="rerun",
	selection_mode="single-row",
	key="editor",
)

with st.container(horizontal=True):
	st.button("**Incluir**", on_click=add, type="primary", icon=":material/add:")
	st.button("**Editar**", key="edit", type="primary", icon=":material/edit:")
	st.button("**Deletar**", key="delete", type="primary", icon=":material/delete:")

if st.session_state["edit"]:
	if st.session_state["editor"]["selection"]["rows"]:
		edit()
	else:
		st.session_state["message"] = "selection"

if st.session_state["delete"]:
	if st.session_state["editor"]["selection"]["rows"]:
		delete()
	else:
		st.session_state["message"] = "selection"

if "message" in st.session_state:
	if st.session_state["message"] == "add":
		st.toast("**Planilha incluída com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "edit":
		st.toast("**Planilha editada com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "delete":
		st.toast("**1 linha deletada com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "selection":
		st.toast("**Não houve seleção de registro...**", icon=":material/error:")

	del st.session_state["message"]
