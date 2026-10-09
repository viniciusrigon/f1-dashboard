"""Módulo de carregamento e pré-processamento dos dados de Fórmula 1.

Carrega tabelas relacionais do dataset Ergast/Kaggle e realiza merges e limpezas
com cache do Streamlit (@st.cache_data) para alta performance.
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st


def _get_data_dir() -> Path:
    """Localiza o diretório 'data' contendo os arquivos CSV."""
    candidates = [
        Path(__file__).resolve().parent / "data",
        Path.cwd() / "tarefas" / "tarefa2" / "tarefa" / "data",
        Path.cwd() / "data",
    ]
    for p in candidates:
        if p.exists() and (p / "results.csv").exists():
            return p
    raise FileNotFoundError(
        f"Diretório de dados não encontrado. Procurado em: {[str(c) for c in candidates]}"
    )


def categorize_status(status_str: str) -> str:
    """Categoriza o status final da corrida para análise de confiabilidade."""
    if not isinstance(status_str, str):
        return "Outros"
    
    status_lower = status_str.strip().lower()
    
    if status_lower == "finished" or "lap" in status_lower:
        return "Completou / Classificado"
    
    collision_keywords = ["accident", "collision", "spun off", "damage"]
    if any(k in status_lower for k in collision_keywords):
        return "Acidente / Colisão"
    
    mechanical_keywords = [
        "engine", "gearbox", "brake", "suspension", "hydraulics",
        "electrical", "clutch", "transmission", "power unit", "overheating",
        "mechanical", "throttle", "steering", "oil", "water", "puncture",
        "wheel", "exhaust", "battery", "radiator", "turbo", "driveshaft", "pneumatics"
    ]
    if any(k in status_lower for k in mechanical_keywords):
        return "Falha Mecânica"
    
    return "Outros"


@st.cache_data(show_spinner="Carregando base histórica de Fórmula 1...")
def load_all_f1_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega e integra os dados de corridas, pilotos, equipes, status e circuitos.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            1) df_merged: resultados consolidados corrida a corrida.
            2) df_circuits: dados geográficos de cada circuito.
    """
    data_dir = _get_data_dir()

    # Leitura com tipos controlados
    races = pd.read_csv(
        data_dir / "races.csv",
        usecols=["raceId", "year", "round", "circuitId", "name", "date"],
    )
    races.rename(columns={"name": "race_name"}, inplace=True)

    results = pd.read_csv(
        data_dir / "results.csv",
        usecols=[
            "resultId", "raceId", "driverId", "constructorId",
            "grid", "positionText", "positionOrder", "points", "statusId", "fastestLapSpeed"
        ],
    )
    results["points"] = pd.to_numeric(results["points"], errors="coerce").fillna(0.0)
    results["grid"] = pd.to_numeric(results["grid"], errors="coerce").fillna(0).astype(int)
    results["positionOrder"] = pd.to_numeric(results["positionOrder"], errors="coerce").fillna(99).astype(int)
    results["fastestLapSpeed"] = pd.to_numeric(results["fastestLapSpeed"], errors="coerce")

    drivers = pd.read_csv(
        data_dir / "drivers.csv",
        usecols=["driverId", "driverRef", "code", "forename", "surname", "nationality"],
    )
    drivers["driver_name"] = drivers["forename"].fillna("") + " " + drivers["surname"].fillna("")
    drivers["driver_name"] = drivers["driver_name"].str.strip()
    drivers.rename(columns={"nationality": "driver_nationality"}, inplace=True)

    constructors = pd.read_csv(
        data_dir / "constructors.csv",
        usecols=["constructorId", "constructorRef", "name", "nationality"],
    )
    constructors.rename(
        columns={"name": "constructor_name", "nationality": "constructor_nationality"},
        inplace=True,
    )

    status = pd.read_csv(data_dir / "status.csv", usecols=["statusId", "status"])
    status["status_category"] = status["status"].apply(categorize_status)

    circuits = pd.read_csv(
        data_dir / "circuits.csv",
        usecols=["circuitId", "circuitRef", "name", "location", "country", "lat", "lng"],
    )
    circuits.rename(columns={"name": "circuit_name"}, inplace=True)
    circuits["lat"] = pd.to_numeric(circuits["lat"], errors="coerce")
    circuits["lng"] = pd.to_numeric(circuits["lng"], errors="coerce")

    # Merge relacional
    merged = results.merge(races, on="raceId", how="inner")
    merged = merged.merge(drivers, on="driverId", how="left")
    merged = merged.merge(constructors, on="constructorId", how="left")
    merged = merged.merge(status, on="statusId", how="left")
    merged = merged.merge(circuits[["circuitId", "circuit_name", "country", "lat", "lng"]], on="circuitId", how="left")

    # Identificador de vitória
    merged["is_win"] = (merged["positionOrder"] == 1).astype(int)

    # Filtrar apenas até o ano atual com dados disponíveis (por exemplo até 2024 para resultados consolidados)
    # Mas mantemos os anos disponíveis para seleção no slider
    return merged, circuits


@st.cache_data(show_spinner="Carregando dados de pit stops...")
def load_pit_stops_data() -> pd.DataFrame:
    """Carrega dados históricos de paradas nos boxes (disponíveis a partir de 2011).

    Returns:
        pd.DataFrame: DataFrame com tempos de pit stop em segundos e identificadores de corrida/piloto.
    """
    data_dir = _get_data_dir()
    pit_stops = pd.read_csv(
        data_dir / "pit_stops.csv",
        usecols=["raceId", "driverId", "stop", "lap", "milliseconds"],
    )
    pit_stops["milliseconds"] = pd.to_numeric(pit_stops["milliseconds"], errors="coerce")
    pit_stops["duration_sec"] = (pit_stops["milliseconds"] / 1000.0).round(3)
    return pit_stops


def filter_data(
    df: pd.DataFrame,
    year_range: tuple[int, int],
    selected_constructor_nats: list[str] | None = None,
    selected_drivers: list[str] | None = None,
) -> pd.DataFrame:
    """Filtra o DataFrame consolidado pelos parâmetros da interface.

    Args:
        df: DataFrame integrado.
        year_range: Tupla (ano_min, ano_max).
        selected_constructor_nats: Lista de nacionalidades de construtores selecionadas.
        selected_drivers: Lista de pilotos selecionados.

    Returns:
        pd.DataFrame filtrado.
    """
    filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].copy()

    if selected_constructor_nats:
        filtered = filtered[filtered["constructor_nationality"].isin(selected_constructor_nats)]

    if selected_drivers:
        filtered = filtered[filtered["driver_name"].isin(selected_drivers)]

    return filtered


@st.cache_data(show_spinner=False)
def load_circuits_geojson() -> dict:
    """Carrega as geometrias GeoJSON dos traçados dos circuitos de F1.

    Returns:
        dict: Objeto GeoJSON (FeatureCollection) com os traçados vetoriais.
    """
    data_dir = _get_data_dir()
    geojson_path = data_dir / "f1-circuits.geojson"
    if not geojson_path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)
