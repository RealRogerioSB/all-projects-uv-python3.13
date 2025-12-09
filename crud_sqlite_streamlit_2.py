from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import text
from streamlit.connections import SQLConnection

st.set_page_config("Teste de Funcionamento de SQLite", layout="wide", initial_sidebar_state="auto")

engine: SQLConnection = SQLConnection("SQLite3")


@st.cache_data(ttl=1)
def load_data() -> pd.DataFrame:
	df: pd.DataFrame = engine.query("SELECT idx, nome, nascimento, sexo FROM simples")
	df["nascimento"] = pd.to_datetime(df["nascimento"])
	return df


@st.dialog("Editar Cadastro")
def edit(_idx: int) -> None:
	_row: pd.Series = st.session_state["simples"][st.session_state["simples"]["idx"].eq(_idx)].iloc[0]

	dict_sex: dict[int, str] = {0: "Feminino", 1: "Masculino"}

	name: str = st.text_input("Nome:", value=_row["nome"])

	with st.container(horizontal=True):
		birth: date = st.date_input("Data de Nascimento:", format="DD/MM/YYYY",
									min_value=date(1900, 1, 1), value=_row["nascimento"])
		sex: int = st.radio("Sexo:", options=list(dict_sex.keys()), index=int(_row["sexo"]),
							format_func=lambda x: dict_sex.get(x), horizontal=True)

	with st.container(horizontal=True, horizontal_alignment="right"):
		if st.button("Salvar", type="primary", icon=":material/save:"):
			if all([name, birth, sex is not None]):
				with engine.engine.connect() as conx:
					conx.execute(
						text("""
							UPDATE simples
							SET nome       = :name,
								nascimento = :birth,
								sexo       = :sex
							WHERE idx      = :idx
						"""),
						dict(name=name, birth=birth, sex=sex, idx=_idx)
					)
					conx.commit()
				st.cache_data.clear()
				st.session_state["simples"] = load_data()
				st.session_state["message"] = "edit"
				st.rerun()
			else:
				st.warning("**Todos campos devem ser preenchidos!**", icon=":material/warning:")


@st.dialog("Confirmação")
def delete(_idx: int) -> None:
	st.markdown("Confirma a exclusão do registro?")

	with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):
		st.button("Sim", key="sim", type="primary", icon=":material/check:")
		st.button("Não", key="não", type="primary", icon=":material/cancel:")

	if st.session_state["sim"]:
		with engine.engine.connect() as conx:
			conx.execute(text("DELETE FROM simples WHERE idx = :idx"), dict(idx=_idx))
			conx.commit()
		st.cache_data.clear()
		st.session_state["simples"] = load_data()
		st.session_state["message"] = "delete"
		st.rerun()

	if st.session_state["não"]:
		st.rerun()


if "simples" not in st.session_state:
	st.session_state["simples"] = load_data()

for row in st.session_state["simples"].itertuples(index=False, name=None):
	with st.container(horizontal=True):
		col1, col2, col3 = st.columns(3)
		col1.write(f"**{row[1]}**")
		col2.write(f"**{row[2].strftime('%d/%m/%Y')}**")
		col3.write(f"**{'Feminino' if row[3] == 0 else 'Masculino'}**")

		st.button("**:material/edit:**", key=f"edit_{row[0]}", type="primary", on_click=edit, args=(row[0],))
		st.button("**:material/delete:**", key=f"delete_{row[0]}", type="primary", on_click=delete, args=(row[0],))

if "message" in st.session_state:
	if st.session_state["message"] == "edit":
		st.toast("**Planilha editada com sucesso!**", icon=":material/check_circle:")

	if st.session_state["message"] == "delete":
		st.toast("**1 linha excluída com sucesso!**", icon=":material/check_circle:")

	del st.session_state["message"]
