import sqlite3
from datetime import date

import pandas as pd
import sqlalchemy.exc as sa
import streamlit as st
from streamlit.connections import SQLConnection
from streamlit.elements.lib.column_types import ColumnConfig

engine: SQLConnection = SQLConnection("SQLite3")

dict_lzc: dict[int, str] = {0: "UniBB", 1: "Alura"}
dict_mod: dict[int, str] = {0: "Presencial", 1: "Auto-instrucional"}


@st.cache_data
def load_table() -> pd.DataFrame:
	return engine.query("SELECT * FROM unibb", show_spinner="Obtendo os dados, aguarde...", ttl=1)


curse_duplicated: pd.DataFrame = load_table()
curse_duplicated = curse_duplicated[curse_duplicated.duplicated(subset=["nm_curso"], keep=False)] \
	.sort_values(by=["nm_curso", "dt_curso", "id_curso"], ascending=[True, True, True])


@st.dialog("Novo Curso")
def add() -> None:
	with st.container(horizontal=True):
		id_curso: int = st.number_input("Código: :red[*]", value=0, format="%d")
		dt_curso: date = st.date_input("Conclusão: :red[*]", value=date.today(), format="DD/MM/YYYY")
		cg_curso: int = st.number_input("Horas: :red[*]", value=0, format="%d")

	nm_curso: str = st.text_input("Nome: :red[*]", value=None)

	with st.container(horizontal=True):
		lzc_curso: int = st.radio("Estudo: :red[*]", options=list(dict_lzc.keys()), index=None,
								  format_func=lambda x: dict_lzc.get(x), horizontal=True)
		mod_curso: int = st.radio("Módulo: :red[*]", options=list(dict_mod.keys()), index=None,
								  format_func=lambda x: dict_mod.get(x), horizontal=True)

	cnh_curso: str = st.text_input("Conhecimento:", value=None)
	area_cnh_curso: str = st.text_input("Área:", value=None)

	if st.container(horizontal_alignment="right").button("Salvar", type="primary", icon=":material/save:"):
		if all([id_curso, nm_curso, dt_curso, cg_curso, lzc_curso is not None, mod_curso is not None]):
			with engine.engine.connect() as conn:
				new: dict[str, list[date | int | str]] = {
					"id_curso": [id_curso], "nm_curso": [nm_curso], "dt_curso": [dt_curso],
					"cg_curso": [cg_curso], "lzc_curso": [lzc_curso], "mod_curso": [mod_curso],
					"cnh_curso": [cnh_curso], "area_cnh_curso": area_cnh_curso
				}
				pd.DataFrame(new).to_sql("unibb", con=conn, if_exists="append", index=False)

			st.cache_data.clear()
			st.session_state["aviso"] = "add"
			st.rerun()
		else:
			st.warning("**Todos campos :red[*] devem ser preenchidos!**", icon=":material/warning:")


dict_opt: dict[int, str] = {1: f"**{len(load_table())} Cursos**",
							2: f"**{int(len(curse_duplicated) / 2)} Cursos Duplicados**",
							3: "**Manual**"}
st.segmented_control("Opções", options=dict_opt.keys(), format_func=lambda op: dict_opt.get(op), default=1,
					 key="abas", label_visibility="hidden")

column_config: dict[str, ColumnConfig] = {
	"id_curso": st.column_config.NumberColumn("Código", width=60, pinned=True),
	"nm_curso": st.column_config.TextColumn("Curso", width=240),
	"dt_curso": st.column_config.DateColumn("Conclusão", format="DD/MM/YYYY", width=90),
	"cg_curso": st.column_config.NumberColumn("Horas", width=50),
	"lzc_curso": st.column_config.SelectboxColumn("Estudo", options=list(dict_lzc.keys()),
												  format_func=lambda x: dict_lzc.get(x)),
	"mod_curso": st.column_config.SelectboxColumn("Módulo", options=list(dict_mod.keys()),
												  format_func=lambda x: dict_mod.get(x), width=150),
	"cnh_curso": st.column_config.TextColumn("Conhecimento", width="medium"),
	"area_cnh_curso": st.column_config.TextColumn("Área", width="medium"),
}

if st.session_state["abas"] == 1:
	st.dataframe(
		data=load_table().sort_values(["dt_curso", "id_curso"]),
		hide_index=True,
		column_config=column_config,
		row_height=25,
	)

	st.button("**Novo Curso**", on_click=add, type="primary", icon=":material/add_circle:")
elif st.session_state["abas"] == 2:
	st.dataframe(
		data=curse_duplicated,
		hide_index=True,
		width="content",
		column_config=column_config,
		row_height=25,
	)
elif st.session_state["abas"] == 3:
	st.text_area("**Script de SQL:**", key="sql", width="stretch")

	if st.button("**Executar**", type="primary", icon=":material/code:"):
		try:
			df: pd.DataFrame = engine.query(st.session_state["sql"], show_spinner="Executando o SQL, aguarde...", ttl=1)
		except (sqlite3.OperationalError, sa.OperationalError):
			st.toast("**Erro de sintaxe de SQL:** reveja e corrige o script.", icon=":material/error:")
		else:
			st.dataframe(df, width="content", hide_index=True)
			st.button("**Voltar**", type="primary", icon=":material/reply:")
else:
	st.markdown("**Escolha uma das opções acima!**")

if "aviso" in st.session_state:
	if st.session_state["aviso"] == "add":
		st.toast("**Curso salvo com sucesso!**", icon=":material/check_circle:")

	del st.session_state["aviso"]
