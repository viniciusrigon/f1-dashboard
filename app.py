"""IA001 — Atividade 02: Dashboard Interativo em Streamlit
Tema: Fórmula 1 World Championship (1950–2026)
Grupo e Integrante: Vinicius Rigon

Público-alvo:
  1. Fãs e entusiastas de F1 (comparações de desempenho, eras de domínio e história).
  2. Jornalistas e analistas de dados esportivos (insights rápidos, confiabilidade e métricas).
"""

from pathlib import Path
import altair as alt
import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st
from streamlit_folium import st_folium

from data_loader import filter_data, load_all_f1_data, load_pit_stops_data, load_circuits_geojson

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(
    page_title="F1 Analytics — Dashboard Histórico",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização: Fundo branco para todo o dashboard
st.markdown(
    """
    <style>
        /* Fundo principal do dashboard e do cabeçalho */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {
            background-color: #FFFFFF !important;
        }

        /* Fundo da barra lateral */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E6E6E6;
        }

        /* Container do conteúdo principal */
        .main .block-container {
            background-color: #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Compatibilidade de largura de gráficos com base na versão do Streamlit
versao_streamlit = tuple(int(parte) for parte in st.__version__.split(".")[:2])
LARGURA = {"width": "stretch"} if versao_streamlit >= (1, 50) else {"use_container_width": True}

# ==============================================================================
# CARREGAMENTO DOS DADOS (COM CACHE)
# ==============================================================================
df_all, df_circuits = load_all_f1_data()
geojson_circuits = load_circuits_geojson()

# ==============================================================================
# CABEÇALHO PRINCIPAL
# ==============================================================================
st.title("🏎️ F1 Data Explorer — Dashboard Interativo de Fórmula 1")
st.markdown(
    """
    Este dashboard interativo permite explorar o **histórico completo da Fórmula 1** desde a temporada inaugural de 1950 até 2026,
    *Público-alvo:* **Fãs de automobilismo** e **jornalistas/analistas de dados esportivos** que buscam 
    investigar o domínio de pilotos, a hegemonia de construtores por nacionalidade e os padrões de 
    confiabilidade mecânica e desfechos de corrida.
    """
)
st.caption("Fonte dos dados: Formula 1 World Championship (1950–2026) / Ergast Dataset (Kaggle — Domínio Público CC0).")

# ==============================================================================
# BARRA LATERAL (FILTROS INTERATIVOS)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Controles & Filtros")
    st.markdown("Ajuste os parâmetros abaixo para recalcular as análises do dashboard em tempo real.")

    min_year_base = int(df_all["year"].min())
    max_year_base = max(int(df_all[df_all["is_win"] == 1]["year"].max()), 2026)  # Último ano com corridas realizadas

    # Mapeamento das décadas históricas da Fórmula 1
    DECADAS_F1 = {
        "Anos 2020 (2020–2026 — Efeito Solo & Nova Geração)": (2020, 2026),
        "Anos 2010 (2010–2019 — Era Turbo-Híbrida V6)": (2010, 2019),
        "Anos 2000 (2000–2009 — Era V10 / V8 Clássicos)": (2000, 2009),
        "Anos 1990 (1990–1999 — Era V10 & Senna/Schumacher)": (1990, 1999),
        "Anos 1980 (1980–1989 — Era Turbo Clássica)": (1980, 1989),
        "Anos 1970 (1970–1979 — Garagistas & Efeito Solo)": (1970, 1979),
        "Anos 1960 (1960–1969 — Era Motores Traseiros)": (1960, 1969),
        "Anos 1950 (1950–1959 — Década Inaugural / Fangio)": (1950, 1959),
    }

    RECORTES_RAPIDOS = {
        "Era Turbo-Híbrida (2014–2026)": (2014, 2026),
        "Últimos 10 anos (2016–2026 — Era Híbrida)": (2016, 2026),
        "Últimos 5 anos (2021–2026)": (2021, 2026),
        "Era V8 (2006–2013)": (2006, 2013),
        "Histórico Completo (1950–2026)": (min_year_base, max_year_base),
    }

    # 1. Modo de Seleção Temporal
    modo_tempo = st.radio(
        "Critério de seleção do período:",
        ["Recortes Rápidos", "Filtro por Década", "Personalizado"],
        index=0,
        horizontal=True,
        help="Alterne entre atalhos de eras históricas, navegação por décadas ou ajuste manual no slider.",
    )

    if modo_tempo == "Recortes Rápidos":
        preset = st.radio(
            "Recortes temporais rápidos:",
            list(RECORTES_RAPIDOS.keys()),
            index=0,
        )
        default_range = RECORTES_RAPIDOS[preset]

    elif modo_tempo == "Filtro por Década":
        multi_decadas = st.toggle("Selecionar múltiplas décadas", value=False)
        if multi_decadas:
            decadas_sel = st.multiselect(
                "Selecione as décadas desejadas:",
                options=list(DECADAS_F1.keys()),
                default=[list(DECADAS_F1.keys())[0]],
                help="Selecione duas ou mais décadas para compor o período contínuo.",
            )
            if decadas_sel:
                default_range = (
                    min(DECADAS_F1[d][0] for d in decadas_sel),
                    max(DECADAS_F1[d][1] for d in decadas_sel),
                )
            else:
                default_range = (2014, 2026)
        else:
            decada_sel = st.selectbox(
                "Selecione a década:",
                options=list(DECADAS_F1.keys()),
                index=0,
            )
            default_range = DECADAS_F1[decada_sel]

    else:
        default_range = (2014, 2026)

    # 2. Slider de Período (ajuste fino / confirmação visual)
    year_range = st.slider(
        "Intervalo de temporadas (anos):",
        min_value=min_year_base,
        max_value=max_year_base,
        value=default_range,
        step=1,
        help="Filtra todos os Grandes Prêmios ocorridos dentro do intervalo selecionado.",
    )

    st.divider()

    # Opções dinâmicas disponíveis no período selecionado
    df_period = df_all[(df_all["year"] >= year_range[0]) & (df_all["year"] <= year_range[1])]
    available_nats = sorted(df_period["constructor_nationality"].dropna().unique().tolist())

    # 3. Filtro de Nacionalidade dos Construtores
    st.subheader("Equipes & Construtores")
    selected_nats = st.multiselect(
        "Nacionalidade do Construtor:",
        options=available_nats,
        default=available_nats,
        help="Filtra equipes de acordo com o país sob o qual foram registradas na FIA.",
    )

    # 4. Controle de Top N
    st.subheader("Parâmetros de Exibição")
    top_n = st.slider(
        "Top N de pilotos/equipes nos rankings:",
        min_value=5,
        max_value=25,
        value=10,
        step=1,
    )

    # 5. Filtro opcional de Pilotos específicos
    df_period_nat = df_period[df_period["constructor_nationality"].isin(selected_nats)]
    available_drivers = sorted(df_period_nat["driver_name"].dropna().unique().tolist())
    
    filtrar_pilotos = st.checkbox("Filtrar pilotos específicos", value=False)
    selected_drivers = None
    if filtrar_pilotos:
        selected_drivers = st.multiselect(
            "Selecione os pilotos:",
            options=available_drivers,
            default=available_drivers[:top_n] if len(available_drivers) >= top_n else available_drivers,
        )

    st.divider()
    st.markdown("ℹ️ *Dica:* Utilize os filtros para comparar o domínio de montadoras ou isolar eras técnicas.")

# ==============================================================================
# APLICAÇÃO DOS FILTROS E VALIDAÇÃO DE DADOS VAZIOS
# ==============================================================================
filtered = filter_data(
    df_all,
    year_range=year_range,
    selected_constructor_nats=selected_nats,
    selected_drivers=selected_drivers,
)

# REQUISITO: Informar quando uma seleção não produzir dados
if filtered.empty:
    st.warning(
        "⚠️ **Nenhum dado encontrado para a combinação de filtros selecionada.**\n\n"
        "- Verifique se ao menos uma nacionalidade de construtor foi selecionada na barra lateral.\n"
        "- Caso tenha ativado o filtro de pilotos específicos, certifique-se de selecionar pilotos que competiram no período.\n"
        "- Tente ampliar o intervalo de anos no controle deslizante."
    )
    st.stop()

# ==============================================================================
# CARTÕES DE MÉTRICAS (KPIs DO RECORTE)
# ==============================================================================
n_races = filtered["raceId"].nunique()
n_drivers = filtered["driverId"].nunique()
n_constructors = filtered["constructorId"].nunique()

# Piloto com mais vitórias
wins_by_driver = filtered[filtered["is_win"] == 1].groupby("driver_name").size()
top_winner = wins_by_driver.idxmax() if not wins_by_driver.empty else "N/A"
top_wins_count = wins_by_driver.max() if not wins_by_driver.empty else 0

# Construtor com mais pontos
points_by_const = filtered.groupby("constructor_name")["points"].sum()
top_const = points_by_const.idxmax() if not points_by_const.empty else "N/A"
top_const_points = points_by_const.max() if not points_by_const.empty else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Grandes Prêmios", f"{n_races:,}")
kpi2.metric("Pilotos Ativos", f"{n_drivers:,}")
kpi3.metric("Construtores", f"{n_constructors:,}")
kpi4.metric("Líder de Vitórias", f"{top_winner}", f"{top_wins_count} vitórias" if top_wins_count > 0 else "")
kpi5.metric("Equipe Mais Pontuadora", f"{top_const}", f"{top_const_points:,.0f} pts")

st.markdown("---")

# ==============================================================================
# ESTRUTURA EM ABAS (INVESTIGAÇÃO DAS PERGUNTAS)
# ==============================================================================
tab_p1, tab_p2, tab_p3, tab_dinamica, tab_pits, tab_map, tab_about = st.tabs([
    "🏆 Pergunta 1 — Vitórias por Piloto",
    "🏎️ Pergunta 2 — Nacionalidade & Equipes",
    "🏁 Pergunta 3 — Confiabilidade & Status",
    "⚡ Dinâmica de Corrida & Ultrapassagens",
    "⏱️ Pit Stops & Velocidade",
    "🌍 Mapa de Circuitos",
    "📋 Metodologia & Dados",
])

# ------------------------------------------------------------------------------
# ABA 1: PERGUNTA 1 (PLOTLY) — VITÓRIAS POR PILOTO
# ------------------------------------------------------------------------------
with tab_p1:
    st.subheader(f"🏆 Pergunta 1: Quais pilotos tiveram o maior número de vitórias entre {year_range[0]} e {year_range[1]}?")
    st.markdown(
        """
        Esta análise investiga o domínio individual dos pilotos no recorte selecionado. O gráfico apresenta 
        o número absoluto de vitórias e a taxa de conversão (percentual de corridas vencidas sobre as disputadas).
        """
    )

    # Agregação por piloto
    driver_stats = filtered.groupby(["driverId", "driver_name"]).agg(
        total_races=("raceId", "nunique"),
        wins=("is_win", "sum"),
        total_points=("points", "sum"),
    ).reset_index()

    # Descobrir a principal equipe do piloto no período
    main_team = (
        filtered.groupby(["driver_name", "constructor_name"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .drop_duplicates("driver_name")
        .set_index("driver_name")["constructor_name"]
    )
    driver_stats["equipe_principal"] = driver_stats["driver_name"].map(main_team).fillna("Outra")
    driver_stats["taxa_vitoria_pct"] = (driver_stats["wins"] / driver_stats["total_races"] * 100).round(1)

    # Filtrar pilotos com vitórias ou ordenar por vitórias e pontos
    top_drivers = (
        driver_stats.sort_values(by=["wins", "total_points"], ascending=[False, False])
        .head(top_n)
        .copy()
    )

    if top_drivers["wins"].sum() == 0:
        st.info("ℹ️ Não foram registradas vitórias para os pilotos no recorte especificado. Exibindo por pontuação total.")
        top_drivers = driver_stats.sort_values(by="total_points", ascending=False).head(top_n)

    # Visualização com Plotly
    driver_order = top_drivers["driver_name"].tolist()

    fig_p1 = px.bar(
        top_drivers,
        x="wins",
        y="driver_name",
        orientation="h",
        color="equipe_principal",
        text="wins",
        category_orders={"driver_name": driver_order},
        labels={
            "wins": "Número de Vitórias (1º Lugar)",
            "driver_name": "Piloto",
            "equipe_principal": "Equipe Principal",
        },
        hover_data={
            "wins": True,
            "total_races": True,
            "taxa_vitoria_pct": ":.1f%",
            "total_points": ":,.0f",
        },
        title=f"Top {len(top_drivers)} Pilotos com Mais Vitórias ({year_range[0]}–{year_range[1]})",
        height=max(420, top_n * 35),
    )

    fig_p1.update_layout(
        xaxis_title="Vitórias em Grandes Prêmios (unidades)",
        yaxis_title="Piloto",
        yaxis={"categoryorder": "array", "categoryarray": driver_order[::-1]},
        legend_title="Equipe Principal",
        margin=dict(l=20, r=20, t=50, b=40),
    )
    fig_p1.update_traces(textposition="outside", texttemplate="%{text}")

    st.plotly_chart(fig_p1, **LARGURA)

    # Texto interpretativo para o público-alvo
    st.info(
        f"**💡 Interpretação para Fãs e Jornalistas:**\n\n"
        f"No período entre **{year_range[0]} e {year_range[1]}**, foram disputadas **{n_races} corridas**. "
        f"O topo do ranking evidencia a alta concentração de vitórias entre os primeiros colocados, "
        f"com destaque para **{top_winner}** ({top_wins_count} vitórias). "
        f"Jornalistas esportivos podem observar que a taxa de vitória (%) muitas vezes sintetiza períodos de hegemonia "
        f"técnica indiscutível de uma montadora (ex.: Mercedes na década de 2010 e Red Bull no início dos anos 2020)."
    )

    with st.expander("🔍 Ver tabela de dados detalhada dos pilotos"):
        tabela_p1 = top_drivers[["driver_name", "equipe_principal", "wins", "total_races", "taxa_vitoria_pct", "total_points"]].rename(
            columns={
                "driver_name": "Piloto",
                "equipe_principal": "Equipe Principal",
                "wins": "Vitórias",
                "total_races": "GPs Disputados",
                "taxa_vitoria_pct": "Aproveitamento (%)",
                "total_points": "Pontos Totais",
            }
        )
        st.dataframe(tabela_p1, hide_index=True, **LARGURA)

    # Análise Complementar: Conversão de Pole Positions em Vitórias
    st.markdown("---")
    st.markdown("#### 🎯 Eficiência dos Pole-Sitters: Conversão de Pole Position em Vitória")
    st.caption("Investigação sobre o aproveitamento da 1ª posição no grid de largada para os maiores conquistadores de pole do período.")

    df_poles = filtered[filtered["grid"] == 1].copy()
    if not df_poles.empty:
        pole_stats = (
            df_poles.groupby("driver_name")
            .agg(
                total_poles=("raceId", "nunique"),
                vitorias_da_pole=("is_win", "sum"),
            )
            .reset_index()
        )
        pole_stats["poles_sem_vitoria"] = pole_stats["total_poles"] - pole_stats["vitorias_da_pole"]
        pole_stats["taxa_conversao_pct"] = (
            pole_stats["vitorias_da_pole"] / pole_stats["total_poles"] * 100
        ).round(1)

        top_pole_drivers = (
            pole_stats.sort_values(by=["total_poles", "vitorias_da_pole"], ascending=[False, False])
            .head(top_n)
        )

        col_pole_chart, col_pole_kpi = st.columns([3, 1])
        with col_pole_chart:
            fig_pole = go.Figure()
            fig_pole.add_trace(
                go.Bar(
                    y=top_pole_drivers["driver_name"],
                    x=top_pole_drivers["vitorias_da_pole"],
                    name="Pole Convertida em Vitória (1º Lugar)",
                    orientation="h",
                    marker_color="#2ca02c",
                    text=top_pole_drivers["vitorias_da_pole"],
                    textposition="auto",
                    textangle=0,
                )
            )
            fig_pole.add_trace(
                go.Bar(
                    y=top_pole_drivers["driver_name"],
                    x=top_pole_drivers["poles_sem_vitoria"],
                    name="Pole Não Convertida (P2+ ou Abandono)",
                    orientation="h",
                    marker_color="#d62728",
                    text=top_pole_drivers["poles_sem_vitoria"],
                    textposition="auto",
                    textangle=0,
                )
            )
            fig_pole.update_layout(
                barmode="stack",
                title=f"Conversão de Pole Position em Vitória — Top {len(top_pole_drivers)} Pole-Sitters ({year_range[0]}–{year_range[1]})",
                xaxis_title="Total de Pole Positions (unidades)",
                yaxis_title="Piloto",
                yaxis={"categoryorder": "total ascending"},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=60, b=40),
                height=max(380, len(top_pole_drivers) * 35),
            )
            st.plotly_chart(fig_pole, **LARGURA)

        with col_pole_kpi:
            st.markdown("##### 📌 Aproveitamento de Pole")
            for _, row in top_pole_drivers.head(min(5, len(top_pole_drivers))).iterrows():
                st.metric(
                    label=row["driver_name"],
                    value=f"{row['taxa_conversao_pct']:.1f}%",
                    help=f"{row['vitorias_da_pole']} vitórias em {row['total_poles']} poles no período.",
                )
    else:
        st.info("Nenhuma pole position registrada no recorte selecionado.")

# ------------------------------------------------------------------------------
# ABA 2: PERGUNTA 2 (ALTAIR & PLOTLY) — NACIONALIDADE E CONSTRUTORES
# ------------------------------------------------------------------------------
with tab_p2:
    st.subheader(f"🏎️ Pergunta 2: Como a nacionalidade dos construtores impacta o acúmulo de pontos?")
    st.markdown(
        """
        Esta seção analisa a correlação entre a **nacionalidade oficial das montadoras** e a sua capacidade 
        de pontuação ao longo dos campeonatos, permitindo mapear os polos industriais do automobilismo.
        """
    )

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("#### Evolução Anual de Pontos por Nacionalidade")
        st.caption("Gramática declarativa interativa: clique em uma nacionalidade na legenda para filtrá-la.")

        # Agregação por ano e nacionalidade de construtor
        nat_year = (
            filtered.groupby(["year", "constructor_nationality"])["points"]
            .sum()
            .reset_index()
        )

        # Seleção interativa na legenda
        selecao_nat = alt.selection_point(fields=["constructor_nationality"], bind="legend")

        grafico_altair = (
            alt.Chart(nat_year)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:O", title="Temporada (Ano)"),
                y=alt.Y("points:Q", title="Total de Pontos Marcados (unidades)"),
                color=alt.Color("constructor_nationality:N", title="Nacionalidade do Construtor"),
                opacity=alt.condition(selecao_nat, alt.value(1.0), alt.value(0.15)),
                tooltip=[
                    alt.Tooltip("year:O", title="Ano"),
                    alt.Tooltip("constructor_nationality:N", title="Nacionalidade"),
                    alt.Tooltip("points:Q", title="Pontos", format=",.1f"),
                ],
            )
            .add_params(selecao_nat)
            .properties(height=420, title=f"Pontuação Anual por País da Equipe ({year_range[0]}–{year_range[1]})")
        )
        st.altair_chart(grafico_altair, **LARGURA)

    with col_chart2:
        st.markdown("#### Pontos Acumulados por Equipe")
        st.caption("Composição de pontos das principais equipes no recorte.")

        const_totals = (
            filtered.groupby(["constructor_name", "constructor_nationality"])["points"]
            .sum()
            .reset_index()
            .sort_values(by="points", ascending=False)
            .head(top_n)
        )

        const_order = const_totals["constructor_name"].tolist()

        fig_p2_bars = px.bar(
            const_totals,
            x="points",
            y="constructor_name",
            color="constructor_nationality",
            orientation="h",
            category_orders={"constructor_name": const_order},
            labels={
                "points": "Pontos Totais Acumulados",
                "constructor_name": "Equipe",
                "constructor_nationality": "País",
            },
            title=f"Top {len(const_totals)} Equipes por Pontuação",
            height=420,
        )
        fig_p2_bars.update_layout(
            yaxis={"categoryorder": "array", "categoryarray": const_order[::-1]},
            margin=dict(l=20, r=20, t=50, b=40),
        )
        st.plotly_chart(fig_p2_bars, **LARGURA)

    st.info(
        "**💡 Interpretação dos Resultados:**\n\n"
        "Historicamente, a Fórmula 1 possui uma forte tradição de equipes britânicas (McLaren, Williams, Lotus, "
        "Aston Martin) e italianas (Ferrari). Contudo, na era moderna recente (a partir de 2014), construtores "
        "com licença austríaca (**Red Bull**) e alemã (**Mercedes**) passaram a liderar amplamente o acúmulo de pontos. "
        "Essa visualização permite a jornalistas esportivos contextualizar geopoliticamente as dinastias esportivas."
    )

    # Análise Complementar: Treemap Hierárquico de Pontos
    st.markdown("---")
    st.markdown("#### 🌳 Composição Hierárquica: País ➔ Equipe ➔ Piloto")
    st.caption("Visão estrutural da distribuição de pontos: explore interativamente como cada construtor e piloto contribui para a pontuação de seu país.")

    tree_data = (
        filtered.groupby(["constructor_nationality", "constructor_name", "driver_name"])["points"]
        .sum()
        .reset_index()
    )
    tree_data = tree_data[tree_data["points"] > 0]

    if not tree_data.empty:
        fig_tree = px.treemap(
            tree_data,
            path=[px.Constant("Fórmula 1"), "constructor_nationality", "constructor_name", "driver_name"],
            values="points",
            color="points",
            color_continuous_scale="Blues",
            title=f"Distribuição Hierárquica de Pontuação ({year_range[0]}–{year_range[1]})",
            height=500,
        )
        fig_tree.update_traces(textinfo="label+value+percent parent")
        fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig_tree, **LARGURA)
    else:
        st.info("Nenhum dado de pontos disponível para compor o mapa hierárquico no recorte.")

# ------------------------------------------------------------------------------
# ABA 3: PERGUNTA 3 (SEABORN & MATPLOTLIB) — STATUS E CONFIABILIDADE
# ------------------------------------------------------------------------------
with tab_p3:
    st.subheader(f"🏁 Pergunta 3: Qual é a distribuição dos resultados finais (`status`) para os principais pilotos?")
    st.markdown(
        """
        Para analisar consistência e taxa de abandono, esta seção categoriza o desfecho de cada corrida 
        entre **Completou / Classificado**, **Falha Mecânica**, **Acidente / Colisão** e **Outros**.
        """
    )

    # Identificar os Top N pilotos por pontos no período
    top_driver_ids = (
        filtered.groupby("driverId")["points"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index.tolist()
    )
    df_top_status = filtered[filtered["driverId"].isin(top_driver_ids)].copy()

    # Tabela de contingência piloto x categoria de status
    cross_status = pd.crosstab(
        df_top_status["driver_name"],
        df_top_status["status_category"],
        normalize="index"
    ) * 100

    # Ordenar pilotos pela maior taxa de conclusão
    if "Completou / Classificado" in cross_status.columns:
        cross_status = cross_status.sort_values("Completou / Classificado", ascending=True)

    # Renderização estática precisa com Matplotlib e Seaborn
    sns.set_theme(style="whitegrid", font="sans-serif")
    fig_sns, ax = plt.subplots(figsize=(11, max(5, top_n * 0.45)))

    cores_status = {
        "Completou / Classificado": "#2ca02c",  # Verde
        "Falha Mecânica": "#d62728",            # Vermelho
        "Acidente / Colisão": "#ff7f0e",        # Laranja
        "Outros": "#7f7f7f",                    # Cinza
    }
    cols_existentes = [c for c in ["Completou / Classificado", "Falha Mecânica", "Acidente / Colisão", "Outros"] if c in cross_status.columns]
    palette = [cores_status[c] for c in cols_existentes]

    cross_status[cols_existentes].plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=palette,
        width=0.7,
    )

    ax.set_title(
        f"Distribuição Percentual de Resultados Finais de Corrida — Top {len(cross_status)} Pilotos ({year_range[0]}–{year_range[1]})",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Percentual das Corridas Disputadas (%)", fontsize=11)
    ax.set_ylabel("Piloto", fontsize=11)
    ax.set_xlim(0, 100)
    ax.legend(
        title="Status Final da Corrida",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=True,
    )

    # Adicionar anotações percentuais nas barras principais
    for p in ax.patches:
        width = p.get_width()
        if width > 12:  # Mostra rótulo apenas se a fatia for suficientemente visível
            x = p.get_x() + width / 2
            y = p.get_y() + p.get_height() / 2
            ax.text(x, y, f"{width:.0f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    plt.tight_layout()
    st.pyplot(fig_sns, **LARGURA)
    plt.close(fig_sns)

    st.info(
        "**💡 Análise Estatística:**\n\n"
        "Pilotos multicampeões da era moderna (como Hamilton, Verstappen e Alonso) sustentam taxas de conclusão de prova "
        "frequentemente superiores a **85%**. Ao comparar com décadas anteriores (ex.: anos 1980 e 1990), constata-se um "
        "declínio substancial nas falhas de motor e câmbio, comprovando a evolução tecnológica dos motores V6 turbo-híbridos."
    )

# ------------------------------------------------------------------------------
# ABA 4: DINÂMICA DE CORRIDA & ULTRAPASSAGENS
# ------------------------------------------------------------------------------
with tab_dinamica:
    st.subheader(f"⚡ Dinâmica de Corrida: Grid de Largada, Ultrapassagens e Disputas pelo Título ({year_range[0]}–{year_range[1]})")
    st.markdown(
        """
        Esta seção aprofunda o comportamento na pista: como a posição de largada (`grid`) se correlaciona com a 
        posição de chegada (`positionOrder`), quais pilotos mais ganham posições ao longo das provas e 
        como as batalhas pelo título mundial se desenrolaram corrida a corrida.
        """
    )

    col_din1, col_din2 = st.columns([3, 2])

    # 1. Grid vs. Posição Final com Linha de Paridade e Múltiplas Visões
    with col_din1:
        st.markdown("#### Correlação: Grid de Largada vs. Posição Final")

        df_grid_pos = filtered[(filtered["grid"] > 0) & (filtered["positionOrder"] <= 25)].copy()

        if not df_grid_pos.empty:
            df_grid_pos["pos_diff"] = df_grid_pos["grid"] - df_grid_pos["positionOrder"]

            # Correlação de postos (Spearman calculada via Pearson dos postos ranqueados) e Pearson
            spearman_corr = df_grid_pos["grid"].rank().corr(df_grid_pos["positionOrder"].rank())
            pearson_corr = df_grid_pos["grid"].corr(df_grid_pos["positionOrder"])

            intensidade_corr = "Forte" if spearman_corr >= 0.6 else ("Moderada" if spearman_corr >= 0.3 else "Fraca")
            st.caption(
                f"📊 **Spearman:** `{spearman_corr:.2f}` | **Pearson:** `{pearson_corr:.2f}` "
                f"({intensidade_corr} correlação positiva: largar à frente prediz fortemente a posição final)."
            )

            tab_grid_heat, tab_grid_box, tab_grid_scatter = st.tabs([
                "🔥 Mapa de Calor (Densidade)",
                "📦 Boxplot por Grid",
                "📈 Dispersão & Tendência",
            ])

            max_val = max(int(df_grid_pos["grid"].max()), int(df_grid_pos["positionOrder"].max()), 22)

            # Visão A: Mapa de Calor 2D (Densidade sem sobreposição de inteiros)
            with tab_grid_heat:
                fig_heat = px.density_heatmap(
                    df_grid_pos,
                    x="grid",
                    y="positionOrder",
                    nbinsx=24,
                    nbinsy=24,
                    color_continuous_scale="YlOrRd",
                    labels={
                        "grid": "Posição no Grid de Largada",
                        "positionOrder": "Posição Final de Chegada",
                        "count": "Total de Pilotos",
                    },
                    title="Densidade Conjunta: Grid vs. Chegada",
                    height=420,
                )
                fig_heat.add_shape(
                    type="line",
                    x0=1,
                    y0=1,
                    x1=max_val,
                    y1=max_val,
                    line=dict(color="#1f77b4", width=2, dash="dash"),
                )
                fig_heat.add_annotation(
                    x=min(max_val * 0.72, 16),
                    y=min(max_val * 0.72 + 1.5, 18),
                    text="Paridade (Chegada = Grid)",
                    showarrow=False,
                    font=dict(color="#1f77b4", size=10),
                )
                fig_heat.update_layout(
                    xaxis=dict(range=[0.5, 24.5], dtick=2, title="Posição de Largada (Grid)"),
                    yaxis=dict(range=[0.5, 24.5], dtick=2, title="Posição Oficial de Chegada"),
                    margin=dict(l=20, r=20, t=50, b=40),
                )
                st.plotly_chart(fig_heat, key="chart_grid_heat", **LARGURA)
                st.markdown(
                    """
                    **💡 Como interpretar o Mapa de Calor:**
                    - **Intensidade da Cor:** Tons quentes (laranja/vermelho) indicam combinações onde centenas de corridas se concentram.
                    - **Linha Azul Tracejada ($y = x$):** Representa a paridade neutra (chegada idêntica ao grid). Quanto mais perto da diagonal, maior o determinismo da largada.
                    - **Foco no Top 3:** O ponto mais quente da história é o P1 $\\to$ P1, mostrando que largar na ponta oferece altíssima probabilidade de vitória/pódio, enquanto o meio do grid se espalha verticalmente devido a disputas e abandonos.
                    """
                )

            # Visão B: Boxplot por Posição de Largada
            with tab_grid_box:
                df_box = df_grid_pos[df_grid_pos["grid"] <= 22].copy()
                fig_box = px.box(
                    df_box,
                    x="grid",
                    y="positionOrder",
                    labels={
                        "grid": "Posição de Largada (Grid)",
                        "positionOrder": "Posição Final de Chegada",
                    },
                    title="Distribuição da Posição Final por Grid de Largada",
                    color_discrete_sequence=["#e10600"],
                    height=420,
                )
                fig_box.add_shape(
                    type="line",
                    x0=1,
                    y0=1,
                    x1=22,
                    y1=22,
                    line=dict(color="#1f77b4", width=2, dash="dash"),
                )
                fig_box.add_annotation(
                    x=16,
                    y=17.5,
                    text="Paridade (Chegada = Grid)",
                    showarrow=False,
                    font=dict(color="#1f77b4", size=10),
                )
                fig_box.update_layout(
                    xaxis=dict(dtick=1, title="Posição de Largada (Grid)"),
                    yaxis=dict(range=[0.5, 24.5], dtick=2, title="Posição Oficial de Chegada"),
                    margin=dict(l=20, r=20, t=50, b=40),
                )
                st.plotly_chart(fig_box, key="chart_grid_box", **LARGURA)
                st.markdown(
                    """
                    **💡 Como interpretar o Boxplot:**
                    - **Linha Central (Mediana):** Revela a posição final mais típica de um piloto que largou naquela posição específica.
                    - **Caixa (25% a 75%):** Contém 50% de todos os desfechos registrados para aquele lugar no grid (intervalo interquartil).
                    - **Paridade com a Linha Azul:** Se a mediana estiver abaixo da linha tracejada, os pilotos dessa posição tendem a ganhar posições; se estiver acima, tendem a perder posições.
                    """
                )

            # Visão C: Dispersão com Regressão Linear e Jitter anti-sobreposição
            with tab_grid_scatter:
                if len(df_grid_pos) > 2000:
                    df_grid_plot = df_grid_pos.sample(n=2000, random_state=42).copy()
                else:
                    df_grid_plot = df_grid_pos.copy()

                rng = np.random.default_rng(42)
                df_grid_plot["grid_jitter"] = df_grid_plot["grid"] + rng.uniform(-0.25, 0.25, size=len(df_grid_plot))
                df_grid_plot["pos_jitter"] = df_grid_plot["positionOrder"] + rng.uniform(-0.25, 0.25, size=len(df_grid_plot))

                fig_grid = px.scatter(
                    df_grid_plot,
                    x="grid_jitter",
                    y="pos_jitter",
                    color="pos_diff",
                    color_continuous_scale="RdBu",
                    color_continuous_midpoint=0,
                    hover_data={
                        "grid": True,
                        "positionOrder": True,
                        "driver_name": True,
                        "constructor_name": True,
                        "race_name": True,
                        "year": True,
                        "pos_diff": True,
                        "grid_jitter": False,
                        "pos_jitter": False,
                    },
                    labels={
                        "grid_jitter": "Grid de Largada",
                        "pos_jitter": "Posição Final de Chegada",
                        "grid": "Grid Oficial",
                        "positionOrder": "Chegada Oficial",
                        "constructor_name": "Equipe",
                        "pos_diff": "Saldo de Posições",
                        "driver_name": "Piloto",
                        "race_name": "GP",
                        "year": "Temporada",
                    },
                    title="Dispersão: Grid vs. Chegada (Jitter Anti-Sobreposição)",
                    opacity=0.6,
                    height=420,
                )
                fig_grid.add_shape(
                    type="line",
                    x0=1,
                    y0=1,
                    x1=max_val,
                    y1=max_val,
                    line=dict(color="#333333", width=2, dash="dash"),
                )
                fig_grid.add_annotation(
                    x=min(max_val * 0.72, 16),
                    y=min(max_val * 0.72 + 1.5, 18),
                    text="Linha de Paridade (Chegada = Grid)",
                    showarrow=False,
                    font=dict(color="#333333", size=10),
                )

                # Linha de tendência linear (regressão) via numpy
                if len(df_grid_pos) >= 2:
                    m, b = np.polyfit(df_grid_pos["grid"], df_grid_pos["positionOrder"], 1)
                    x_trend = np.array([1, max_val])
                    y_trend = m * x_trend + b
                    fig_grid.add_trace(
                        go.Scatter(
                            x=x_trend,
                            y=y_trend,
                            mode="lines",
                            name=f"Regressão (m={m:.2f})",
                            line=dict(color="#e10600", width=2.5),
                        )
                    )

                fig_grid.update_layout(
                    xaxis=dict(range=[0.5, 24], title="Posição de Largada (Grid)"),
                    yaxis=dict(range=[0.5, 24], title="Posição Oficial de Chegada"),
                    margin=dict(l=20, r=20, t=50, b=40),
                    coloraxis_colorbar=dict(title="Saldo"),
                )
                st.plotly_chart(fig_grid, key="chart_grid_scatter", **LARGURA)
                st.markdown(
                    r"""
                    **💡 Como interpretar a Dispersão & Tendência:**
                    - **Linha Vermelha Contínua (Regressão Linear):** Modela a taxa média de conversão do grid para a chegada ($y = m \cdot x + b$). Inclinação próxima de 1 confirma forte dependência do grid.
                    - **Linha Tracejada Escura ($y = x$):** Pontos em **azul** (abaixo da linha) representam ganhos de posições; pontos em **vermelho** (acima da linha) indicam perdas.
                    - **Jitter (±0.25):** Aplica um ruído visual sutil para que milhares de corridas coincidentes não fiquem ocultas exatamente sob um único ponto.
                    """
                )

            with st.expander("📖 Guia Comparativo: Qual visualização escolher?"):
                st.markdown(
                    """
                    - **🔥 Mapa de Calor (Densidade):** Melhor para enxergar **concentração e frequência**. Elimina o acúmulo de pontos discretos e evidencia visualmente o determinismo do Top 3 vs. o caos do pelotão intermediário.
                    - **📦 Boxplot por Grid:** Melhor para responder **"qual é a faixa esperada de chegada de quem larga em P$X$?"**. Revela a mediana e a dispersão (25% a 75%) de cada posição individual.
                    - **📈 Dispersão & Tendência:** Melhor para inspecionar **cada corrida individualmente com reta de regressão linear**. Mostra o saldo de ultrapassagens por cores (azul = ganho, vermelho = perda) com detalhes completos no cursor (*hover*).
                    """
                )

    # 2. Ranking de Escaladores do Grid
    fig_climbers_pts = None
    fig_climbers_all = None

    with col_din2:
        st.markdown("#### Mestres da Recuperação: Posições Ganhas por Corrida")
        st.caption("Média de posições conquistadas em relação ao grid de largada.")

        tab_recup_pts, tab_recup_geral = st.tabs([
            "🏆 Zona de Pontuação (Pontuadores)",
            "🌐 Histórico Geral (Todas as Provas)",
        ])

        # A. Apenas Corridas na Zona de Pontuação (Pilotos que Pontuaram)
        with tab_recup_pts:
            df_gain_pts = filtered[(filtered["grid"] > 0) & (filtered["points"] > 0)].copy()

            if not df_gain_pts.empty:
                df_gain_pts["pos_gain"] = df_gain_pts["grid"] - df_gain_pts["positionOrder"]

                gain_stats_pts = (
                    df_gain_pts.groupby("driver_name")
                    .agg(
                        total_gps=("raceId", "nunique"),
                        media_ganho=("pos_gain", "mean"),
                        maior_recuperacao=("pos_gain", "max"),
                    )
                    .reset_index()
                )
                min_gps_pts = min(10, max(2, n_races // 5)) if n_races >= 2 else 1
                gain_stats_pts_filtered = gain_stats_pts[gain_stats_pts["total_gps"] >= min_gps_pts]
                if gain_stats_pts_filtered.empty and not gain_stats_pts.empty:
                    gain_stats_pts_filtered = gain_stats_pts

                top_climbers_pts = (
                    gain_stats_pts_filtered.sort_values(by="media_ganho", ascending=False)
                    .head(top_n)
                    .sort_values(by="media_ganho", ascending=True)
                )

                if not top_climbers_pts.empty:
                    fig_climbers_pts = px.bar(
                        top_climbers_pts,
                        x="media_ganho",
                        y="driver_name",
                        orientation="h",
                        color="media_ganho",
                        color_continuous_scale="Tealgrn",
                        labels={
                            "media_ganho": "Média de Posições Ganhas por GP Pontuado",
                            "driver_name": "Piloto",
                            "total_gps": "GPs Pontuados no Recorte",
                            "maior_recuperacao": "Maior Escalada de Posições",
                        },
                        hover_data={
                            "driver_name": True,
                            "media_ganho": ":.2f",
                            "total_gps": True,
                            "maior_recuperacao": True,
                        },
                        title=f"Top {len(top_climbers_pts)} Escaladores na Zona de Pontuação",
                        height=420,
                    )
                    fig_climbers_pts.update_layout(
                        coloraxis_showscale=False,
                        margin=dict(l=20, r=20, t=50, b=40),
                    )
                    st.plotly_chart(fig_climbers_pts, key="chart_climbers_pts", **LARGURA)
                    st.caption(
                        f"Contabiliza apenas provas onde o piloto pontuou (`points > 0`). "
                        f"Mínimo de {min_gps_pts} GP(s) pontuado(s) no recorte."
                    )
                else:
                    st.info("Sem dados suficientes de pilotos pontuadores no recorte.")
            else:
                st.info("Nenhum piloto pontuou no recorte selecionado.")

        # B. Histórico Geral (Todas as Provas com Largada Válida)
        with tab_recup_geral:
            df_gain = filtered[filtered["grid"] > 0].copy()

            if not df_gain.empty:
                df_gain["pos_gain"] = df_gain["grid"] - df_gain["positionOrder"]

                gain_stats = (
                    df_gain.groupby("driver_name")
                    .agg(
                        total_gps=("raceId", "nunique"),
                        media_ganho=("pos_gain", "mean"),
                        maior_recuperacao=("pos_gain", "max"),
                    )
                    .reset_index()
                )
                min_gps = min(10, max(3, n_races // 3)) if n_races >= 3 else 1
                gain_stats_filtered = gain_stats[gain_stats["total_gps"] >= min_gps]
                if gain_stats_filtered.empty and not gain_stats.empty:
                    gain_stats_filtered = gain_stats

                top_climbers = (
                    gain_stats_filtered.sort_values(by="media_ganho", ascending=False)
                    .head(top_n)
                    .sort_values(by="media_ganho", ascending=True)
                )

                if not top_climbers.empty:
                    fig_climbers_all = px.bar(
                        top_climbers,
                        x="media_ganho",
                        y="driver_name",
                        orientation="h",
                        color="media_ganho",
                        color_continuous_scale="Tealgrn",
                        labels={
                            "media_ganho": "Média de Posições Ganhas por GP",
                            "driver_name": "Piloto",
                            "total_gps": "Total de GPs Disputados",
                            "maior_recuperacao": "Maior Escalada de Posições",
                        },
                        hover_data={
                            "driver_name": True,
                            "media_ganho": ":.2f",
                            "total_gps": True,
                            "maior_recuperacao": True,
                        },
                        title=f"Top {len(top_climbers)} Maiores Recuperadores no Geral",
                        height=420,
                    )
                    fig_climbers_all.update_layout(
                        coloraxis_showscale=False,
                        margin=dict(l=20, r=20, t=50, b=40),
                    )
                    st.plotly_chart(fig_climbers_all, key="chart_climbers_all", **LARGURA)
                    st.caption(
                        f"Contabiliza todas as largadas válidas (`grid > 0`). "
                        f"Mínimo de {min_gps} GP(s) disputado(s) no recorte."
                    )
                else:
                    st.info("Poucos GPs disputados no recorte para calcular média de recuperação.")
            else:
                st.info("Sem dados suficientes de grid e posição para calcular recuperação geral.")

    # Contextualização e Comparativo Analítico
    st.info(
        "**💡 Diferenciação Analítica — Zona de Pontuação vs. Histórico Geral:**\n\n"
        "• **Zona de Pontuação (Pontuadores):** Contabiliza exclusivamente as provas em que o piloto terminou na zona de pontos (`points > 0`). "
        "Esse recorte evidencia as escaladas mais determinantes da categoria — pilotos que, mesmo largando atrás por punições técnicas ou "
        "incidentes no qualifying, realizaram recuperações sólidas que se converteram em pontos no campeonato.\n\n"
        "• **Histórico Geral (Todas as Provas):** Contabiliza todas as largadas válidas (`grid > 0`). Esta métrica reflete a média de ganho "
        "de posições em qualquer contexto, capturando pilotos de equipes de fundo de grid que largam nas últimas posições e ganham colocações "
        "em função de abandonos de adversários à frente, sem necessariamente pontuar."
    )

    if fig_climbers_pts is not None and fig_climbers_all is not None:
        with st.expander("📊 Ver Comparativo Lado a Lado (Pontuadores vs. Geral)"):
            st.caption("Comparação direta e simultânea dos dois rankings de recuperação para o mesmo período selecionado:")
            col_comp1, col_comp2 = st.columns(2)
            with col_comp1:
                st.plotly_chart(fig_climbers_pts, key="comp_climbers_pts", **LARGURA)
            with col_comp2:
                st.plotly_chart(fig_climbers_all, key="comp_climbers_all", **LARGURA)

    st.markdown("---")

    # 3. Evolução Rodada a Rodada da Batalha pelo Título
    st.markdown("#### 🏁 Batalha pelo Título: Corrida a Corrida (Evolução de Pontos)")
    st.caption("Acompanhe o acúmulo de pontos etapa por etapa ao longo de uma temporada específica selecionada.")

    anos_temporada = sorted(filtered["year"].unique().tolist(), reverse=True)
    if anos_temporada:
        ano_selecionado = st.selectbox(
            "Selecione o ano da temporada para dissecar a disputa pelo título:",
            options=anos_temporada,
            index=0,
            key="sel_ano_batalha",
        )

        df_ano = df_all[df_all["year"] == ano_selecionado].copy()
        top_drivers_ano = (
            df_ano.groupby("driver_name")["points"]
            .sum()
            .sort_values(ascending=False)
            .head(6)
            .index.tolist()
        )

        df_ano_top = df_ano[df_ano["driver_name"].isin(top_drivers_ano)].copy()
        df_ano_top = df_ano_top.sort_values(by=["round"])

        races_ordered = df_ano[["round", "race_name"]].drop_duplicates().sort_values("round")

        dados_acumulados = []
        for drv in top_drivers_ano:
            drv_data = df_ano_top[df_ano_top["driver_name"] == drv]
            merged_races = races_ordered.merge(
                drv_data[["round", "points"]], on="round", how="left"
            ).fillna({"points": 0})
            merged_races["pontos_acumulados"] = merged_races["points"].cumsum()
            merged_races["driver_name"] = drv
            dados_acumulados.append(merged_races)

        if dados_acumulados:
            df_acumulado = pd.concat(dados_acumulados, ignore_index=True)

            fig_titulo = px.line(
                df_acumulado,
                x="round",
                y="pontos_acumulados",
                color="driver_name",
                markers=True,
                labels={
                    "round": "Etapa do Campeonato (Round)",
                    "pontos_acumulados": "Pontos Acumulados no Campeonato",
                    "driver_name": "Piloto",
                },
                hover_data=["race_name"],
                title=f"Evolução da Pontuação Corrida a Corrida — Temporada {ano_selecionado}",
                height=480,
            )
            fig_titulo.update_layout(
                hovermode="x unified",
                legend_title="Piloto",
                margin=dict(l=20, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_titulo, **LARGURA)

# ------------------------------------------------------------------------------
# ABA 5: PIT STOPS & VELOCIDADE
# ------------------------------------------------------------------------------
with tab_pits:
    st.subheader(f"⏱️ Eficiência de Pit Stops & Evolução das Velocidades Médias")
    st.markdown(
        """
        O trabalho de box e o ritmo puro de corrida são determinantes na era moderna. Esta seção investiga a 
        **duração das paradas nos boxes por equipe** (registradas oficialmente pela FIA a partir de 2011) 
        e a **evolução das velocidades médias de volta rápida (`fastestLapSpeed`)** ao longo dos regulamentos técnicos.
        """
    )

    # 1. Pit Stops por Equipe
    st.markdown("#### 🛑 A Guerra dos Boxes: Duração do Pit Lane por Equipe (a partir de 2011)")
    st.caption("Duração total em segundos da passagem pelos boxes (parada + tráfego no pit lane).")

    anos_pit_validos = [y for y in range(year_range[0], year_range[1] + 1) if y >= 2011]

    if anos_pit_validos:
        df_pit_stops_raw = load_pit_stops_data()

        pits_filtrados = df_pit_stops_raw.merge(
            filtered[["raceId", "driverId", "constructor_name", "driver_name", "race_name", "year"]].drop_duplicates(),
            on=["raceId", "driverId"],
            how="inner",
        )

        pits_regulares = pits_filtrados[
            (pits_filtrados["duration_sec"] >= 16.0) & (pits_filtrados["duration_sec"] <= 40.0)
        ].copy()

        if not pits_regulares.empty:
            const_counts = pits_regulares["constructor_name"].value_counts()
            top_const_pits = const_counts.head(top_n).index.tolist()
            pits_plot = pits_regulares[pits_regulares["constructor_name"].isin(top_const_pits)]

            ordem_pits = (
                pits_plot.groupby("constructor_name")["duration_sec"]
                .median()
                .sort_values(ascending=True)
                .index.tolist()
            )

            col_pit_kpi1, col_pit_kpi2, col_pit_kpi3 = st.columns(3)
            melhor_parada = pits_regulares.sort_values("duration_sec").iloc[0]
            tempo_medio = pits_regulares["duration_sec"].mean()
            total_paradas = len(pits_regulares)

            col_pit_kpi1.metric("Total de Pit Stops Analisados", f"{total_paradas:,}")
            col_pit_kpi2.metric("Média Geral no Pit Lane", f"{tempo_medio:.2f} s")
            col_pit_kpi3.metric(
                "Passagem Mais Rápida",
                f"{melhor_parada['duration_sec']:.2f} s",
                f"{melhor_parada['constructor_name']} ({melhor_parada['year']})",
            )

            fig_box_pits = px.box(
                pits_plot,
                x="constructor_name",
                y="duration_sec",
                color="constructor_name",
                category_orders={"constructor_name": ordem_pits},
                labels={
                    "constructor_name": "Equipe",
                    "duration_sec": "Duração Total no Pit Lane (segundos)",
                },
                title=f"Distribuição do Tempo de Pit Stop por Equipe (Ordenado pela Mediana — {min(anos_pit_validos)}–{max(anos_pit_validos)})",
                height=450,
            )
            fig_box_pits.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_box_pits, **LARGURA)
        else:
            st.info("Nenhum dado de pit stop regular encontrado para as equipes filtradas no período.")
    else:
        st.info("ℹ️ Os dados oficiais de telemetria de pit stops foram introduzidos na F1 em 2011. Ajuste o filtro temporal para incluir temporadas a partir de 2011.")

    st.markdown("---")

    # 2. Velocidade da Volta Mais Rápida (fastestLapSpeed)
    st.markdown("#### ⚡ Evolução Histórica da Velocidade Média de Volta Mais Rápida (`fastestLapSpeed`)")
    st.caption("Evolução da velocidade média (km/h) registrada nas voltas mais rápidas a partir de 2004.")

    df_speed = filtered[filtered["fastestLapSpeed"].notna()].copy()

    if not df_speed.empty:
        circuitos_populares = (
            df_speed.groupby("circuit_name")["year"]
            .nunique()
            .sort_values(ascending=False)
            .head(8)
            .index.tolist()
        )

        col_sp1, col_sp2 = st.columns([1, 3])
        with col_sp1:
            circuito_escolhido = st.selectbox(
                "Selecione um circuito de referência:",
                options=circuitos_populares,
                index=0,
                key="sel_circuito_speed",
            )
            st.markdown(
                """
                **Contexto dos Regulamentos:**
                - *2004–2005:* Motores V10 de 3.0L (picos históricos de potência e velocidade).
                - *2006–2013:* Motores V8 de 2.4L aspirados.
                - *2014–2021:* Motores V6 turbo-híbridos de 1.6L.
                - *2022–2026:* Era do Efeito Solo e rodas aro 18.
                """
            )

        with col_sp2:
            df_speed_circ = df_speed[df_speed["circuit_name"] == circuito_escolhido].copy()

            speed_anual = (
                df_speed_circ.groupby("year")["fastestLapSpeed"]
                .max()
                .reset_index(name="max_speed")
            )

            fig_speed = px.line(
                speed_anual,
                x="year",
                y="max_speed",
                markers=True,
                labels={
                    "year": "Temporada (Ano)",
                    "max_speed": "Velocidade Média Máxima (km/h)",
                },
                title=f"Recorde Anual de Velocidade Média por Temporada — {circuito_escolhido}",
                height=420,
            )
            fig_speed.update_traces(line_color="#e10600", line_width=3)
            fig_speed.update_layout(
                yaxis_title="Velocidade da Melhor Volta (km/h)",
                xaxis_title="Ano",
                margin=dict(l=20, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_speed, **LARGURA)
    else:
        st.info("ℹ️ Dados de velocidade de volta mais rápida (`fastestLapSpeed`) estão disponíveis a partir de 2004. Amplie o período para visualizar.")

# ------------------------------------------------------------------------------
# ABA 6: BÔNUS GEOGRÁFICO (FOLIUM) — MAPA DE CIRCUITOS & TRAÇADOS
# ------------------------------------------------------------------------------
with tab_map:
    st.subheader(f"🌍 Distribuição Geográfica & Traçado dos Circuitos ({year_range[0]}–{year_range[1]})")
    st.markdown(
        """
        Explore a localização e o **traçado oficial** dos autódromos da Fórmula 1. 
        Alterne entre a **Visão Global** (volume de GPs sediados por circuito) e o **Inspetor de Traçado Detalhado** 
        (para analisar a geometria, curvas e o asfalto real da pista com imagens de satélite em alta resolução).
        """
    )

    # Mapeamento de geometrias GeoJSON por circuitId
    features_by_circuit_id = {}
    for feat in geojson_circuits.get("features", []):
        cid = feat.get("properties", {}).get("circuitId")
        if cid is not None:
            features_by_circuit_id[cid] = feat

    # Contagem de corridas por circuito no período
    circuits_in_period = (
        filtered.groupby(["circuitId", "circuit_name", "country", "lat", "lng"])["raceId"]
        .nunique()
        .reset_index(name="total_gps")
    )
    circuits_in_period = circuits_in_period.dropna(subset=["lat", "lng"]).sort_values(by="total_gps", ascending=False)

    if circuits_in_period.empty:
        st.info("Nenhum dado geográfico disponível para os filtros atuais.")
    else:
        carto_api_key = "cb1_40r5_1_45a706050a75d2e4001fa8bc"
        carto_tiles_url = f"https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key={carto_api_key}"
        carto_attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

        esri_satellite_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        esri_attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.1, 1.4, 1.1])

        with col_ctrl1:
            modo_mapa = st.radio(
                "Modo de Exibição:",
                ["🌐 Visão Geral (Todos os Circuitos)", "🏎️ Inspetor de Traçado Detalhado"],
                index=0,
                key="radio_modo_mapa",
            )

        with col_ctrl3:
            camada_mapa = st.selectbox(
                "Camada do Mapa:",
                ["🗺️ Mapa Cartográfico (Carto)", "🛰️ Imagem de Satélite (Esri)"],
                index=0,
                key="sel_camada_mapa",
            )

        chosen_tiles = esri_satellite_url if "Satélite" in camada_mapa else carto_tiles_url
        chosen_attr = esri_attr if "Satélite" in camada_mapa else carto_attr

        if modo_mapa == "🌐 Visão Geral (Todos os Circuitos)":
            with col_ctrl2:
                st.caption(
                    f"Exibindo **{len(circuits_in_period)} autódromos** ativos no período selecionado ({year_range[0]}–{year_range[1]}). "
                    f"Círculos indicam o volume de GPs e linhas vermelhas representam os traçados vetoriais cadastrados."
                )

            mapa_f1 = folium.Map(location=[25.0, 10.0], zoom_start=2, tiles=chosen_tiles, attr=chosen_attr)

            for _, row in circuits_in_period.iterrows():
                cid = row["circuitId"]
                raio = 5 + min(row["total_gps"] * 1.5, 20)
                feat = features_by_circuit_id.get(cid)

                status_tracado = f"✅ Sim ({feat['properties'].get('length_km', '-')} km)" if feat else "❌ Apenas coordenadas"
                popup_html = f"""
                <div style="font-family: sans-serif; font-size: 13px;">
                    <b style="color: #e10600; font-size: 14px;">{row['circuit_name']}</b><br/>
                    <b>País:</b> {row['country']}<br/>
                    <b>GPs no período:</b> {row['total_gps']}<br/>
                    <b>Traçado vetorial:</b> {status_tracado}<br/>
                </div>
                """
                folium.CircleMarker(
                    location=[row["lat"], row["lng"]],
                    radius=raio,
                    color="#e10600",  # Vermelho F1
                    fill=True,
                    fill_color="#e10600",
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{row['circuit_name']} ({row['total_gps']} GPs)",
                ).add_to(mapa_f1)

                # Desenha também o traçado vetorial no mapa geral quando disponível
                if feat:
                    folium.GeoJson(
                        feat,
                        style_function=lambda x: {
                            "color": "#e10600",
                            "weight": 3,
                            "opacity": 0.85,
                        },
                        tooltip=f"Traçado: {row['circuit_name']}",
                    ).add_to(mapa_f1)

            st_folium(mapa_f1, use_container_width=True, height=540, returned_objects=[])
            st.caption("🔴 Círculos maiores indicam autódromos com maior presença no calendário (ex.: Monza, Silverstone, Spa-Francorchamps, Interlagos). Dê zoom com o mouse para aproximar de qualquer traçado desenhado na pista.")

        else:
            # Modo Inspetor de Traçado Detalhado
            circuits_com_tracado = [
                row["circuit_name"] for _, row in circuits_in_period.iterrows()
                if row["circuitId"] in features_by_circuit_id
            ]
            outros_circuits = [
                row["circuit_name"] for _, row in circuits_in_period.iterrows()
                if row["circuitId"] not in features_by_circuit_id
            ]
            opcoes_circuito = circuits_com_tracado + outros_circuits

            # Seleciona Interlagos por padrão se disponível, ou o mais corrido
            default_idx = 0
            for i, opt in enumerate(opcoes_circuito):
                if "Interlagos" in opt or "José Carlos Pace" in opt:
                    default_idx = i
                    break

            with col_ctrl2:
                circuito_sel_nome = st.selectbox(
                    "Selecione o Circuito:",
                    options=opcoes_circuito,
                    index=default_idx,
                    key="sel_circuito_inspector",
                )

            row_circ = circuits_in_period[circuits_in_period["circuit_name"] == circuito_sel_nome].iloc[0]
            cid_sel = row_circ["circuitId"]
            feat_sel = features_by_circuit_id.get(cid_sel)

            # Métricas em destaque do autódromo
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Localização", f"{row_circ['country']}")
            with m_col2:
                st.metric("GPs no Período", f"{row_circ['total_gps']}")
            with m_col3:
                extensao_val = f"{feat_sel['properties'].get('length_km', '-')} km" if feat_sel and 'length_km' in feat_sel['properties'] else "N/D"
                st.metric("Extensão do Traçado", extensao_val)
            with m_col4:
                alt_val = f"{feat_sel['properties'].get('altitude', '-')} m" if feat_sel and feat_sel['properties'].get('altitude') is not None else "N/D"
                st.metric("Altitude", alt_val)

            if feat_sel:
                coords = feat_sel["geometry"]["coordinates"]
                lats = [c[1] for c in coords]
                lngs = [c[0] for c in coords]
                c_lat = (min(lats) + max(lats)) / 2
                c_lng = (min(lngs) + max(lngs)) / 2

                mapa_f1 = folium.Map(location=[c_lat, c_lng], zoom_start=14, tiles=chosen_tiles, attr=chosen_attr)
                mapa_f1.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])

                # Traçado vetorial em vermelho oficial da F1
                folium.GeoJson(
                    feat_sel,
                    style_function=lambda x: {
                        "color": "#e10600",
                        "weight": 5,
                        "opacity": 0.95,
                    },
                    tooltip=f"Traçado Oficial: {circuito_sel_nome}",
                ).add_to(mapa_f1)

                # Marcador de largada / reta principal
                start_lat, start_lng = coords[0][1], coords[0][0]
                folium.Marker(
                    location=[start_lat, start_lng],
                    popup=folium.Popup(f"<b>{circuito_sel_nome}</b><br/>Reta Principal / Largada", max_width=220),
                    tooltip="Linha de Largada / Chegada",
                    icon=folium.Icon(color="red", icon="flag"),
                ).add_to(mapa_f1)

            else:
                mapa_f1 = folium.Map(location=[row_circ["lat"], row_circ["lng"]], zoom_start=15, tiles=chosen_tiles, attr=chosen_attr)
                folium.Marker(
                    location=[row_circ["lat"], row_circ["lng"]],
                    popup=folium.Popup(f"<b>{circuito_sel_nome}</b>", max_width=220),
                    tooltip=circuito_sel_nome,
                    icon=folium.Icon(color="red", icon="flag"),
                ).add_to(mapa_f1)
                st.info("ℹ️ Traçado vetorial não cadastrado na base GeoJSON para este circuito histórico. Exibindo coordenada oficial com visualização de satélite/mapa.")

            st_folium(mapa_f1, use_container_width=True, height=540, returned_objects=[])
            st.caption("💡 Dica: alterne a camada para **'🛰️ Imagem de Satélite (Esri)'** para conferir as curvas, zebras, pit lane e arquibancadas reais do autódromo.")

# ------------------------------------------------------------------------------
# ABA 7: METODOLOGIA, DICIONÁRIO E DADOS BRUTOS
# ------------------------------------------------------------------------------
with tab_about:
    st.subheader("📋 Metodologia, Dicionário de Atributos & Dados Brutos")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            """
            ### Sobre a Base de Dados
            - **Fonte:** *Formula 1 World Championship (1950–2026)* — Kaggle / Ergast Developer Network.
            - **Licença:** CC0: Public Domain.
            - **Entidades Integradas:**
              - `races.csv`: Calendário, ano, circuito e nome oficial de cada GP.
              - `results.csv`: Desempenho individual (grid de largada, posição final, pontos, status, volta rápida).
              - `drivers.csv`: Dados cadastrais e nacionalidade dos pilotos.
              - `constructors.csv`: Equipes e suas respectivas nacionalidades oficiais.
              - `status.csv`: Classificação de encerramento da prova (conclusão, panes, acidentes).
              - `circuits.csv`: Coordenadas geográficas dos autódromos.
              - `pit_stops.csv`: Tempos e voltas de paradas nos boxes (disponível a partir de 2011).
            """
        )

    with col_m2:
        st.markdown(
            """
            ### Limitações da Análise
            1. **Mudanças no Sistema de Pontuação:** A F1 alterou seu critério de pontos diversas vezes 
               (ex.: vitória valia 9 pontos nos anos 1960, 10 pontos nos anos 1990 e 25 pontos desde 2010). 
               Por esse motivo, comparações diretas de pontos brutos entre eras distintas devem ser ponderadas.
            2. **Expansão do Calendário:** Temporadas clássicas tinham 12 a 16 corridas, enquanto temporadas 
               recentes chegam a 24 corridas, aumentando o volume acumulado de pontos e vitórias absolutas.
            3. **Disponibilidade Temporal:** Telemetria de paradas em boxes (`pit_stops.csv`) foi registrada pela 
               FIA a partir de 2011, e velocidade média de volta rápida (`fastestLapSpeed`) a partir de 2004.
            """
        )

    st.markdown("### Dicionário de Atributos Principais")
    dic_dados = pd.DataFrame([
        {"Atributo": "year", "Significado": "Ano da temporada do campeonato", "Tipo": "Numérico (Ano)"},
        {"Atributo": "round", "Significado": "Número da etapa na temporada", "Tipo": "Numérico (Ordem)"},
        {"Atributo": "driver_name", "Significado": "Nome completo do piloto", "Tipo": "Texto"},
        {"Atributo": "constructor_name", "Significado": "Nome da equipe / construtor", "Tipo": "Texto"},
        {"Atributo": "constructor_nationality", "Significado": "Nacionalidade de registro da equipe", "Tipo": "Categórico"},
        {"Atributo": "grid", "Significado": "Posição inicial no grid de largada", "Tipo": "Numérico (1 = Pole)"},
        {"Atributo": "positionOrder", "Significado": "Posição final oficial de chegada", "Tipo": "Numérico (1 = Vencedor)"},
        {"Atributo": "points", "Significado": "Pontuação atribuída na corrida", "Tipo": "Numérico (Pontos)"},
        {"Atributo": "fastestLapSpeed", "Significado": "Velocidade média da volta mais rápida (km/h)", "Tipo": "Numérico (km/h)"},
        {"Atributo": "status_category", "Significado": "Categoria do status final (Conclusão / Pane / Acidente)", "Tipo": "Categórico"},
        {"Atributo": "duration_sec", "Significado": "Tempo total no pit lane durante parada (s)", "Tipo": "Numérico (Segundos)"},
    ])
    st.table(dic_dados)

    st.markdown("### Amostra dos Dados Filtrados")
    st.dataframe(
        filtered[[
            "year", "round", "race_name", "driver_name", "constructor_name",
            "constructor_nationality", "grid", "positionOrder", "points", "fastestLapSpeed", "status_category"
        ]].head(100),
        hide_index=True,
        **LARGURA,
    )

# ==============================================================================
# RODAPÉ
# ==============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 13px;'>"
    "IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA | "
    "Dashboard Streamlit | Integrante: Vinicius Rigon"
    "</div>",
    unsafe_allow_html=True,
)
