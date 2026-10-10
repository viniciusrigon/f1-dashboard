# 🏎️ F1 Data Explorer — Dashboard Interativo de Fórmula 1 (1950–2026)

Aplicação interativa em **Streamlit** desenvolvida para a **Atividade 02** da disciplina:  
**IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA**  
**Autor / Integrante:** Vinicius Rigon  
**🌐 Acesse o Dashboard Online (Streamlit Community Cloud):** [https://viniciusrigon-f1-dashboard-app-4aubol.streamlit.app/](https://viniciusrigon-f1-dashboard-app-4aubol.streamlit.app/)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://viniciusrigon-f1-dashboard-app-4aubol.streamlit.app/)

---

## 1. Visão Geral e Público-Alvo

O **F1 Data Explorer** consolida e expande a investigação exploratória iniciada na Atividade 01, transformando a análise estática em uma plataforma interativa de inteligência de dados sobre os mais de 70 anos de história do Campeonato Mundial de Fórmula 1 (1950–2026).

A interface foi estruturada com foco em dois públicos-alvo centrais:

1. **Fãs e Entusiastas de Automobilismo:**
   - Comparação visual entre dinastias esportivas (ex.: o domínio da Mercedes na década de 2010 vs. a supremacia da Red Bull nos anos 2020).
   - Verificação de pilotos recordistas em vitórias, aproveitamento de largadas na ponta e escaladas históricas de pelotão.
   - Exploração geoespacial dos circuitos e inspeção de traçados em imagens de satélite.

2. **Jornalistas Esportivos e Analistas de Dados:**
   - Filtros ágeis para recortes temporais personalizados, décadas específicas ou períodos pré-configurados.
   - Métricas normalizadas, coeficientes estatísticos em tempo real (correlações de Spearman e Pearson) e taxas percentuais de confiabilidade mecânica.
   - Contextualização das limitações históricas de regras técnicas e sistemas de pontuação.

---

## 2. Destaques da Interface & Métricas em Tempo Real (KPIs)

No topo da aplicação, cinco cartões de métricas (**KPIs**) reagem instantaneamente a qualquer alteração nos filtros:

- **Grandes Prêmios:** total de etapas disputadas dentro do recorte selecionado.
- **Pilotos Ativos:** contagem de pilotos distintos que competiram no período.
- **Construtores:** número de equipes participantes.
- **Líder de Vitórias:** piloto mais vitorioso do intervalo e seu número absoluto de triunfos.
- **Equipe Mais Pontuadora:** escuderia com maior pontuação acumulada e o montante de pontos conquistados.

A interface possui estilização customizada em fundo claro, garantindo máxima legibilidade para gráficos analíticos e compatibilidade dinâmica com diferentes versões do Streamlit (`width: stretch` ou `use_container_width`).

---

## 3. Controles Interativos & Filtros da Barra Lateral (`st.sidebar`)

A barra lateral oferece controles integrados que recalculam todas as agregações sob demanda:

- **Critério de Seleção Temporal (3 Modos):**
  - **Recortes Rápidos:** atalhos para períodos consagrados:
    - *Era Turbo-Híbrida (2014–2026)*
    - *Últimos 10 anos (2016–2026)*
    - *Últimos 5 anos (2021–2026)*
    - *Era V8 (2006–2013)*
    - *Histórico Completo (1950–2026)*
  - **Filtro por Década:** navegação histórica estruturada com chave seletora (*toggle*) para escolha de **uma única década** ou **múltiplas décadas contínuas** (dos *Anos 1950* aos *Anos 2020*).
  - **Personalizado:** ajuste livre das temporadas inicial e final.
- **Slider de Intervalo de Temporadas:** controle fino de anos (1950 a 2026).
- **Nacionalidade do Construtor:** seleção múltipla com opções alimentadas dinamicamente pelas equipes ativas no período selecionado.
- **Controle de Top N:** ajuste deslizante (5 a 25) para definir o tamanho de rankings em gráficos de barras e tabelas.
- **Filtro Opcional de Pilotos Específicos:** ativação via caixa de seleção com lista contextualizada para isolar pilotos de interesse.
- **Resiliência a Filtros Vazios:** caso a combinação de parâmetros resulte em zero registros, a aplicação emite uma mensagem clara e amigável (`st.warning`) com dicas de ajuste sem interrupção abrupta do aplicativo.

---

## 4. Estrutura Analítica das Abas do Dashboard

O dashboard organiza as investigações em **7 abas temáticas**:

| Aba | Pergunta / Análise Investigada | Bibliotecas | Visualizações & Recursos Implementados |
|---|---|---|---|
| **🏆 Pergunta 1** | **Quais pilotos tiveram o maior número de vitórias?** | **Plotly** | • Gráfico de barras horizontais ordenado com cor por equipe principal, taxa de conversão (%) e total de GPs.<br>• Tabela de dados interativa expansível.<br>• **Eficiência dos Pole-Sitters:** gráfico de barras empilhadas de conversão de pole position em vitória e indicadores de aproveitamento (%) dos maiores pole-sitters. |
| **🏎️ Pergunta 2** | **Como a nacionalidade dos construtores impacta o acúmulo de pontos?** | **Altair** + **Plotly** | • Série temporal interativa em Altair com gramática declarativa e `selection_point` na legenda para realce interativo por país.<br>• Gráfico de barras Plotly com Top N equipes por pontos acumulados.<br>• **Treemap Hierárquico Interativo:** composição multinível (*Fórmula 1 ➔ País do Construtor ➔ Equipe ➔ Piloto*). |
| **🏁 Pergunta 3** | **Qual é a distribuição dos resultados finais (`status`) para os principais pilotos?** | **Seaborn** + **Matplotlib** | • Gráfico de barras horizontais empilhadas 100% categorizando os desfechos (*Completou / Classificado*, *Falha Mecânica*, *Acidente / Colisão* e *Outros*).<br>• Rótulos percentuais diretos em cada barra para análise de confiabilidade mecânica. |
| **⚡ Dinâmica de Corrida** | **Como o grid se relaciona com a chegada, quem mais ultrapassa e como se desenrolam as disputas de título?** | **Plotly** + **NumPy** | • **Correlação Grid vs. Chegada:** coeficientes de Spearman e Pearson em tempo real com 3 visões em abas:<br>&nbsp;&nbsp;1. *Mapa de Calor (Densidade 2D)* com linha de paridade $y=x$;<br>&nbsp;&nbsp;2. *Boxplot por Grid* com mediana e intervalo interquartil;<br>&nbsp;&nbsp;3. *Dispersão & Tendência* com jitter anti-sobreposição, cores por saldo de posições e reta de regressão linear calculada com `numpy.polyfit`.<br>• **Mestres da Recuperação:** rankings com abas para *Zona de Pontuação* (`points > 0`) vs. *Histórico Geral* (`grid > 0`), com comparativo lado a lado.<br>• **Batalha pelo Título GP a GP:** gráfico de linha temporal cumulativo com a evolução corrida a corrida dos líderes do campeonato no ano escolhido. |
| **⏱️ Pit Stops & Velocidade** | **Qual a eficiência dos pit stops por equipe e como evoluíram as velocidades de volta rápida?** | **Plotly** | • **Guerra dos Boxes (a partir de 2011):** KPIs de paradas e boxplot da duração total no pit lane ordenado pela mediana de cada construtor.<br>• **Evolução da Volta Mais Rápida (`fastestLapSpeed`, a partir de 2004):** seletor de autódromos clássicos e série histórica de velocidade média máxima com notas sobre as eras de motores (V10, V8, V6 Turbo-Híbrido e Efeito Solo). |
| **🌍 Mapa de Circuitos** | **Onde estão os autódromos e quais são os seus traçados geométricos oficiais?** | **Folium** + **streamlit-folium** | • **Visão Geral Global:** mapa-múndi com marcadores circulares dimensionados pelo total de GPs sediados e linhas vetoriais de traçados.<br>• **Inspetor de Traçado Detalhado:** seleção de autódromo com centralização automática (`fit_bounds`), desenho vetorial da pista em vermelho oficial F1 a partir de GeoJSON, marcador na linha de largada e métricas de país, GPs, extensão (km) e altitude.<br>• **Camadas de Visualização:** alternância entre *Mapa Cartográfico (Carto Voyager)* e *Imagem de Satélite em Alta Resolução (Esri World Imagery)*. |
| **📋 Metodologia & Dados** | **Quais são os fundamentos metodológicos, atributos e dados brutos da base?** | **Pandas** + **Streamlit** | • Detalhamento das entidades integradas e limitações da análise (mudanças de pontuação, expansão de calendários e recortes de telemetria).<br>• Dicionário completo de variáveis e atributos.<br>• Tabela com amostra interativa dos dados filtrados. |

---

## 5. Instruções de Acesso, Instalação e Execução

### 🌐 Acesso Online (Sem Instalação Local)
A aplicação está publicada e disponível gratuitamente no **Streamlit Community Cloud**:  
👉 **[https://viniciusrigon-f1-dashboard-app-4aubol.streamlit.app/](https://viniciusrigon-f1-dashboard-app-4aubol.streamlit.app/)**

### 💻 Execução Local — Pré-requisitos
- Python 3.10 ou superior instalado.

### Opção A: Execução direta com `uv` (Recomendada)

Se você utiliza o gerenciador de pacotes [`uv`](https://docs.astral.sh/uv/):

```bash
# Na raiz do repositório F1-Dashboard
uv run streamlit run app.py
```

### Opção B: Execução em ambiente virtual padrão (`venv` + `pip`)

```bash
# 1. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 2. Instale as dependências listadas
pip install -r requirements.txt

# 3. Inicie o dashboard Streamlit
streamlit run app.py
```

Após a inicialização, acesse a aplicação no navegador em:  
👉 **`http://localhost:8501`**

---

## 6. Estrutura do Repositório

```text
F1-Dashboard/
├── app.py                                   # Aplicação principal Streamlit (layout, abas, filtros e gráficos)
├── data_loader.py                           # Módulo com cache (@st.cache_data) para ETL, fusões e GeoJSON
├── requirements.txt                         # Dependências do projeto Python
├── README.md                                # Documentação técnica do dashboard
├── LICENSE                                  # Licença do projeto (Apache 2.0)
├── atividade02_dashboard_ViniciusRigon.ipynb # Caderno Jupyter de apoio e exploração prévia
├── .streamlit/                              # Configurações do Streamlit
└── data/                                    # Conjunto de dados histórico da Fórmula 1 (1950–2026)
    ├── results.csv                          # Desempenho individual corrida a corrida
    ├── races.csv                            # Grandes Prêmios, temporadas, etapas e datas
    ├── drivers.csv                          # Dados biográficos e nacionalidade dos pilotos
    ├── constructors.csv                     # Equipes e nacionalidades oficiais de registro
    ├── status.csv                           # Códigos e motivos de encerramento de corrida
    ├── circuits.csv                         # Coordenadas geográficas dos autódromos
    ├── pit_stops.csv                        # Telemetria de paradas nos boxes (desde 2011)
    └── f1-circuits.geojson                  # Coordenadas vetoriais dos traçados de pista
```

---

## 7. Tecnologias e Bibliotecas Utilizadas

| Biblioteca | Finalidade Principal no Projeto |
|---|---|
| **Streamlit** (`streamlit`) | Framework web para montagem do dashboard interativo, métricas, abas e controles de barra lateral. |
| **Pandas** (`pandas`) | Manipulação de DataFrames, fusão relacional (*merges*), agregações estatísticas e tabelas de contingência. |
| **NumPy** (`numpy`) | Cálculos numéricos, regressão linear polinomial (`np.polyfit`) e geração de ruído visual (*jitter*). |
| **Plotly** (`plotly`) | Gráficos interativos com tooltips enriquecidos, barras horizontais, dispersões, boxplots e treemaps hierárquicos. |
| **Altair** (`altair`) | Visualização declarativa da evolução temporal de pontos por nacionalidade com seleção dinâmica na legenda. |
| **Matplotlib** & **Seaborn** (`matplotlib`, `seaborn`) | Renderização de gráficos estáticos precisos de distribuição percentual empilhada de status de corrida. |
| **Folium** & **Streamlit-Folium** (`folium`, `streamlit-folium`) | Mapas interativos mundiais com camadas de satélite (Esri), marcadores proporcionais e desenho vetorial de circuitos via GeoJSON. |
| **PyArrow** (`pyarrow`) | Otimização de performance de serialização e leitura de dados tabulares pelo Streamlit. |

---

## 8. Fonte dos Dados e Licença

- **Base de Dados:** *Formula 1 World Championship (1950–2026)*, baseada no acervo do *Ergast Developer Network* disponibilizado no Kaggle por Atharv Ranjan.
- **Licença dos Dados:** [CC0: Public Domain](https://creativecommons.org/publicdomain/zero/1.0/) (domínio público para uso livre e educacional).
- **Licença do Projeto:** [Apache License 2.0](LICENSE).
