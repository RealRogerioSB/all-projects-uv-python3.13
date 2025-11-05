import locale
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.connections import SQLConnection

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

engine: SQLConnection = st.connection("SQLite3", type=SQLConnection)

months: list[str] = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


@st.cache_data(show_spinner="⏳Obtendo os dados, aguarde...", ttl=1)
def last_period() -> int:
	return engine.query("SELECT MAX(período) AS MAIOR FROM mirrors").loc[0, "MAIOR"]


@st.cache_data(show_spinner="⏳Obtendo os dados, aguarde...", ttl=1)
def load_extract_monthly(_period: int) -> pd.DataFrame:
	load: pd.DataFrame = engine.query(
		sql="""
			SELECT l.lançamento, m.período, m.acerto, m.valor
			FROM mirrors m INNER JOIN lances l ON l.id_lançamento = m.id_lançamento
			WHERE m.período = :value
			ORDER BY m.acerto DESC, m.valor DESC
		""",
		params=dict(value=_period)
	)
	load["período"] = pd.to_datetime(load["período"], format="%Y%m").dt.strftime("%b / %Y")
	return load


@st.cache_data(show_spinner="⏳Obtendo os dados, aguarde...", ttl=1)
def load_extract_annual(_year: int) -> pd.DataFrame:
	load: pd.DataFrame = engine.query(
		sql="""
			SELECT l.lançamento, m.período, m.acerto, m.valor
			FROM mirrors m INNER JOIN main.lances l ON l.id_lançamento = m.id_lançamento
			WHERE CAST(período / 100 AS INTEGER) = :value
		""",
		params=dict(value=_year)
	)
	load["mês"] = pd.to_datetime(load["período"], format="%Y%m").dt.strftime("%b")
	load = load.pivot(columns="mês", index=["lançamento", "acerto"], values="valor").reset_index().fillna(value=0)
	reindex_columns: list[str] = ["lançamento", "acerto"] + [coluna for coluna in months[1:] if coluna in load.columns]
	load = load[reindex_columns]
	load["média"] = load[load.columns[2:]].mean(axis=1)
	load["total"] = load[load.columns[2:-1]].sum(axis=1)
	load = load.sort_values(["acerto", "total"], ascending=[False, False])
	return load


@st.cache_data(show_spinner="⏳Obtendo os dados, aguarde...", ttl=1)
def load_total_annual() -> pd.DataFrame:
	load: pd.DataFrame = engine.query("SELECT período, valor FROM mirrors")
	load = load.groupby(["período"])["valor"].sum().reset_index()
	load["ano"] = pd.to_datetime(load["período"], format="%Y%m").dt.year
	load["mês"] = pd.to_datetime(load["período"], format="%Y%m").dt.strftime("%b")
	load = load.pivot(columns="mês", index="ano", values="valor").fillna(0)
	load = load[[coluna for coluna in months[1:] if coluna in load.columns]]
	load["média"] = load.mean(axis=1)
	load["total"] = load[load.columns[:-1]].sum(axis=1)
	return load


@st.dialog(title=f"Salário de {date.today():%B de %Y}", width="medium")
def new_data() -> None:
	load: pd.DataFrame = engine.query("SELECT id_lançamento, lançamento FROM lances ORDER BY lançamento")
	get: dict[int, str] = dict(zip(load["id_lançamento"], load["lançamento"]))

	st.data_editor(
		data=pd.DataFrame(columns=["id_lançamento", "período", "acerto", "valor"]),
		hide_index=True,
		column_config={
			"id_lançamento": st.column_config.SelectboxColumn(
				label="Lançamento",
				width=300,
				required=True,
				options=list(get.keys()),
				format_func=lambda x: get.get(x),
			),
			"período": st.column_config.NumberColumn(
				label="Período",
				width=50,
				required=True,
				default=date.today().year * 100 + date.today().month,
				min_value=200507,
				max_value=203512,
			),
			"acerto": st.column_config.CheckboxColumn(
				label="Acerto",
				width=30,
				required=True,
				default=False
			),
			"valor": st.column_config.NumberColumn(
				label="Valor",
				width=80,
				required=True,
				default=0.0,
				format="dollar"
			),
		},
		key="editor",
		num_rows="dynamic",
	)

	with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):
		st.button("**Salvar**", key="save", type="primary", icon=":material/save:")
		st.button("**Cancelar**", key="cancel", type="primary", icon=":material/cancel:")

	if st.session_state["save"]:
		if st.session_state["editor"]["added_rows"]:
			with engine.engine.connect() as conn:
				pd.DataFrame(st.session_state["editor"]["added_rows"]) \
					.to_sql("mirrors", con=conn, if_exists="append", index=False)

			st.session_state["toast_msg"] = "save"
			st.cache_data.clear()
			st.rerun()

	if st.session_state["cancel"]:
		st.session_state["toast_msg"] = "cancel"
		st.rerun()


get_year, get_month = divmod(last_period(), 100)

tab1, tab2, tab3, tab4 = st.tabs(["**Extrato Mensal**", "**Extrato Anual**", "**Total Anual**", "**Gráfico**"])

with tab1:
	col1, col2 = st.columns([1.5, 2.5], gap="medium")

	with col1, st.container(horizontal_alignment="center", vertical_alignment="center"):
		st.select_slider("**Mês**", options=months[1:], value=months[get_month], key="slider_months")
		st.slider("**Ano:**", min_value=2005, max_value=date.today().year, value=get_year, key="select_year")
		st.button("**Incluir Salário**", on_click=new_data, type="primary", icon=":material/add_circle:")

	with col2, st.container(horizontal_alignment="right"):
		df1: pd.DataFrame = load_extract_monthly(
			st.session_state["select_year"] * 100 + months.index(st.session_state["slider_months"])
		)

		st.markdown(f"**Total: {locale.currency(df1['valor'].sum(), grouping=True)}**")

		st.dataframe(
			data=df1,
			hide_index=True,
			column_config={
				"lançamento": st.column_config.TextColumn(width=300),
				"período": st.column_config.TextColumn(width=100),
				"acerto": st.column_config.CheckboxColumn("Acerto"),
				"valor": st.column_config.NumberColumn(format="dollar"),
			},
		)

with tab2:
	st.slider("**Ano:**", min_value=2005, max_value=date.today().year, value=get_year, key="slider_years")

	df2: pd.DataFrame = load_extract_annual(st.session_state["slider_years"])

	cols: list[str] = ["jan", "fev", "mar", "abr", "mai", "jun", "jul",
					   "ago", "set", "out", "nov", "dez", "média", "total"]

	st.dataframe(
		data=df2,
		width="content",
		hide_index=True,
		column_config={
			"lançamento": st.column_config.TextColumn(pinned=True),
			"acerto": st.column_config.CheckboxColumn(pinned=True),
			**{col: st.column_config.NumberColumn(format="dollar") for col in cols},
		},
	)

with tab3:
	df3: pd.DataFrame = load_total_annual()

	with st.container():
		st.data_editor(
			data=df3,
			height=497,
			width="content",
			column_config={key: st.column_config.NumberColumn(format="dollar") for key in df3.columns},
			row_height=27,
		)

with tab4:
	st.slider("**Ano:**", min_value=2005, max_value=date.today().year, value=get_year, key="slider_graphic")

	df4: pd.DataFrame = load_total_annual()
	df4 = df4[df4.columns[:-2]] \
		.loc[st.session_state["slider_graphic"]] \
		.reset_index() \
		.rename(columns={st.session_state["slider_graphic"]: "salário"})

	fig = px.bar(
		data_frame=df4,
		x="mês",
		y="salário",
		title=f"Espelho {st.session_state["slider_graphic"]}",
		text=df4["salário"].apply(lambda x: locale.currency(x, grouping=True)),
		color="salário",
		color_continuous_scale="Viridis",
	).update_layout(
		xaxis_title="",
		yaxis_title="",
		xaxis=dict(showline=True, linewidth=1, linecolor="gray", showgrid=True),
		yaxis=dict(showticklabels=False),
		showlegend=False,
		coloraxis_showscale=True,
		template="presentation",
		margin=dict(l=0, r=0, t=30, b=0),
		font=dict(size=13, color="white"),
	).update_traces(
		textposition="outside",
		textfont=dict(size=9, color="black"),
		hovertemplate="%{text}<extra></extra>",
	)

	st.plotly_chart(fig)

if "toast_msg" in st.session_state:
	if st.session_state["toast_msg"] == "save":
		st.toast("**Dados salvos com sucesso!**", icon=":material/add_circle:")

	if st.session_state["toast_msg"] == "cancel":
		st.toast("**Inclusão cancelada...**", icon=":material/cancel:")

	del st.session_state["toast_msg"]
