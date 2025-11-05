from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import text
from streamlit.connections import SQLConnection

st.set_page_config("Teste de Funcionamento de SQLite", layout="wide", initial_sidebar_state="auto")

engine: SQLConnection = st.connection(name="SQLite3", type=SQLConnection)

dict_sex: dict[int, str] = {0: "Feminino", 1: "Masculino"}


@st.cache_data(ttl=1)
def load_data() -> pd.DataFrame:
	df: pd.DataFrame = engine.query("SELECT idx, nome, nascimento, sexo FROM simples")
	df["nascimento"] = pd.to_datetime(df["nascimento"])
	return df


def create_or_update(_name: str, _birth: date, _sex: int, _idx: int | None = None) -> None:
	with engine.engine.begin() as conx:
		conx.execute(
			text("""
				INSERT INTO simples (idx, nome, nascimento, sexo)
				VALUES (:idx, :nome, :nascimento, :sexo)
				ON CONFLICT(idx) DO UPDATE SET
					nome = excluded.nome,
					nascimento = excluded.nascimento,
					sexo = excluded.sexo
			"""), dict(idx=_idx, nome=_name, nascimento=_birth, sexo=_sex),
		)
		st.cache_data.clear()


def delete_by_idx(_idx: int) -> None:
	with engine.engine.begin() as conx:
		conx.execute(text("DELETE FROM simples WHERE idx = :idx"), dict(idx=_idx))
		st.cache_data.clear()


@st.dialog("Novo Cadastro")
def add() -> None:
	name: str = st.text_input("Nome:")

	with st.container(horizontal=True):
		birth: date = st.date_input("Data de Nascimento:", format="DD/MM/YYYY",
									min_value=date(1900, 1, 1))
		sex: int = st.radio("Sexo:",options=list(dict_sex.keys()), index=None,
							format_func=lambda x: dict_sex.get(x), horizontal=True)

	with st.container(horizontal=True, horizontal_alignment="right"):
		if st.button("Salvar", type="primary", icon=":material/save:"):
			if all([name, birth, sex is not None]):
				create_or_update(name, birth, sex)
				st.session_state["simples"] = load_data()
				st.session_state["message"] = "new"
				st.rerun()
			else:
				st.warning("**Todos campos devem ser preenchidos!**", icon=":material/warning:")


@st.dialog("Editar Cadastro")
def edit() -> None:
	select: int = int(st.session_state["editor"]["selection"]["rows"][0])
	row: pd.Series = st.session_state["simples"].iloc[select]
	selected_idx: int = int(row["idx"])

	name: str = st.text_input("Nome:", value=row["nome"])

	with st.container(horizontal=True):
		birth: date = st.date_input("Data de Nascimento:", format="DD/MM/YYYY",
									min_value=date(1900, 1, 1), value=row["nascimento"])
		sex: int = st.radio("Sexo:", options=list(dict_sex.keys()), index=int(row["sexo"]),
							format_func=lambda x: dict_sex.get(x), horizontal=True)

	with st.container(horizontal=True, horizontal_alignment="right"):
		if st.button("Salvar", type="primary", icon=":material/save:"):
			if all([name, birth, sex is not None]):
				create_or_update(name, birth, sex, selected_idx)
				st.session_state["simples"] = load_data()
				st.session_state["message"] = "edit"
				st.rerun()
			else:
				st.warning("**Todos campos devem ser preenchidos!**", icon=":material/warning:")


@st.dialog("Confirmação")
def confirm_for_delete() -> None:
	st.markdown("Confirma a exclusão do registro?")

	with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):
		st.button("Sim", key="sim", type="primary", icon=":material/check:")
		st.button("Não", key="não", type="primary", icon=":material/cancel:")

	if st.session_state["sim"]:
		select: int = int(st.session_state["editor"]["selection"]["rows"][0])
		selected_idx: int = int(st.session_state["simples"].iloc[select]["idx"])

		delete_by_idx(selected_idx)

		st.session_state["simples"] = load_data()
		st.session_state["message"] = "delete"
		st.rerun()

	if st.session_state["não"]:
		st.rerun()


if "simples" not in st.session_state:
	st.session_state["simples"] = load_data()

st.dataframe(
	data=st.session_state["simples"],
	width="content",
	height=313,
	hide_index=True,
	column_order=["nome", "nascimento", "sexo"],
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

with st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="center"):
	st.button("Incluir", help="Incluir cadastro", on_click=add, type="primary", icon=":material/add:")
	st.button("Editar", key="edit", help="Editar cadastro", type="primary", icon=":material/edit:")
	st.button("Excluir", key="delete", help="Deletar cadastro", type="primary", icon=":material/delete:")

if st.session_state["edit"]:
	if st.session_state["editor"]["selection"]["rows"]:
		edit()
	else:
		st.session_state["message"] = "selection"

if st.session_state["delete"]:
	if st.session_state["editor"]["selection"]["rows"]:
		confirm_for_delete()
	else:
		st.session_state["message"] = "selection"

if "message" in st.session_state:
	if st.session_state["message"] == "new":
		st.toast("**Planilha incluída com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "edit":
		st.toast("**Planilha editada com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "delete":
		st.toast("**1 linha excluída com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "selection":
		st.toast("**Não houve seleção de registro...**", icon=":material/error:")

	del st.session_state["message"]
