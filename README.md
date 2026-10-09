# F1 Data Explorer — Dashboard Interativo de Fórmula 1

Aplicação em **Streamlit** desenvolvida para a **Atividade 02** da disciplina:  
**IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA**  
**Grupo / Integrante:** Vinicius Rigon

---

## 1. Visão Geral e Público-Alvo

Este dashboard dá continuidade à proposta formulada na **Atividade 01**, transformando a análise exploratória inicial em uma ferramenta interativa e dinâmica voltada a dois perfis centrais:

1. **Fãs e Entusiastas de Automobilismo:** desejam comparar períodos e dinastias esportivas (ex.: era turbo-híbrida de domínio Mercedes vs. Red Bull), verificar os pilotos mais vitoriosos e entender o aproveitamento de vitórias por corrida.
2. **Jornalistas Esportivos e Analistas de Dados:** necessitam de consultas e filtros rápidos, visualizações com rótulos e unidades claras para reportagens e checagem de consistência/confiabilidade mecânica dos competidores.

---

## 2. Perguntas da Atividade 01 Investigadas no Dashboard

| Nº | Pergunta / Análise Investigada | Biblioteca | Tipo de Gráfico |
|---|---|---|---|
| **1** | **Quais pilotos tiveram o maior número de vitórias no período selecionado?** | **Plotly** | Gráfico de barras horizontais ordenado com hover tooltip detalhado e gráfico de barras empilhadas de **conversão de pole positions em vitórias**. |
| **2** | **Como a nacionalidade dos construtores impacta o acúmulo de pontos ao longo das temporadas?** | **Altair** + **Plotly** | Série temporal interativa com seleção de legenda em Altair, composição por equipe em barras Plotly e **Treemap hierárquico (País ➔ Equipe ➔ Piloto)**. |
| **3** | **Qual é a distribuição dos resultados finais (`status_name`) das corridas para os principais pilotos?** | **Seaborn** + **Matplotlib** | Gráfico de barras horizontais empilhadas normalizadas (100%) mostrando percentual de *Completou / Classificado*, *Falha Mecânica*, *Acidente / Colisão* e *Outros*. |
| **4** | **Dinâmica de Corrida: Grid vs. Posição Final, Escaladores do Grid e Batalha pelo Título GP a GP** | **Plotly** | Scatter plot interativo com linha de paridade ($y=x$), ranking dos maiores recuperadores de posição (**com abas e comparativo lado a lado: zona de pontuação vs. histórico geral**) e linha temporal de pontos acumulados rodada a rodada. |
| **5** | **Pit Stops & Velocidade: Duração dos boxes por equipe e recordes de volta rápida** | **Plotly** | Boxplot ordenado por mediana de tempo no pit lane por construtor e linha temporal de velocidades médias máximas (`fastestLapSpeed`) por circuito. |
| **Bônus** | **Onde estão localizados os Grandes Prêmios e autódromos mundiais no período?** | **Folium** | Mapa interativo mundial com círculos proporcionais ao número de GPs realizados em cada autódromo. |

---

## 3. Controles Interativos

A barra lateral (`st.sidebar`) disponibiliza controles reativos que recalculam todas as visualizações em tempo real:
- **Recortes Temporais Rápidos:** botões pré-configurados para *Era Turbo-Híbrida (2014–2026)*, *Últimos 10 anos (2016–2026)*, *Últimos 5 anos (2021–2026)*, *Era V8 (2006–2013)* e *Histórico Completo (1950–2026)*.
- **Slider de Anos:** controle fino para selecionar qualquer intervalo de temporadas entre 1950 e 2026.
- **Filtro de Nacionalidade dos Construtores:** seleção múltipla de países de registro das equipes (British, German, Italian, Austrian, French, etc.).
- **Filtro Opcional de Pilotos:** permite isolar competidores específicos.
- **Slider de Top N:** ajuste dinâmico da quantidade de pilotos e equipes exibidos nos rankings (5 a 25).
- **Tratamento de Filtros Vazios:** caso a combinação de filtros não produza registros, a aplicação exibe um alerta claro (`st.warning`) com orientações de ajuste, sem travar o sistema.

---

## 4. Instruções de Instalação e Execução

### Opção A: Execução direta com `uv` (Recomendada)

Se você já utiliza o `uv` no ambiente do projeto:

```bash
# A partir da raiz do projeto
uv run streamlit run app.py

```

### Opção B: Execução em ambiente virtual padrão (`venv` + `pip`)

```bash
# 1. Navegue até a pasta da tarefa
cd tarefa

# 2. Crie e ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o dashboard Streamlit
streamlit run app.py
```

A aplicação será iniciada localmente e poderá ser acessada no navegador pelo endereço:  
`http://localhost:8501`

---

## 5. Estrutura de Arquivos

```text
tarefa/
├── app.py              # Aplicação principal em Streamlit (interface, KPIs e abas visuais)
├── data_loader.py      # Módulo de carregamento, categorização e cache dos dados (@st.cache_data)
├── requirements.txt    # Lista de dependências Python para o dashboard
├── README.md           # Guia de instalação, execução e documentação técnica
└── data/               # Conjunto de dados CSVs da F1 (1950–2026)
    ├── results.csv
    ├── races.csv
    ├── drivers.csv
    ├── constructors.csv
    ├── status.csv
    ├── circuits.csv
    ├── pit_stops.csv
    └── f1-circuits.geojson
```

---

## 6. Fonte dos Dados e Licença

- **Base de Dados:** Formula 1 World Championship (1950–2026), baseada no acervo do *Ergast Developer Network* disponibilizado no Kaggle por Atharv Ranjan.
- **Licença:** CC0: Public Domain (dados públicos para uso livre e acadêmico).
