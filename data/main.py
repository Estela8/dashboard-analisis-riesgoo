import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go

    # --------------------------
    # Configuración de página
    st.set_page_config(page_title="📊 Dashboard Rentabilidad y Riesgo", layout="wide")
    st.title("📊 Dashboard: Rentabilidad y Riesgo")

    # --------------------------
    # Datos y parámetros
    periodos_dias = {"3M": 63, "6M": 126, "1A": 252}
    tipo_rentabilidad = "acumuladas"
    rf = 0.02  # tasa libre de riesgo anual


    @st.cache_data
    def cargar_rentabilidades(tipo):
        return pd.read_csv(f"rentabilidades_{tipo}.csv", index_col=0, parse_dates=True)


    rentabilidades = cargar_rentabilidades(tipo_rentabilidad)
    activos = rentabilidades.columns.tolist()
    metricas_completas = ["Rentabilidad", "Drawdown", "Sharpe", "Calmar", "VaR5"]


    # --------------------------
    # Funciones
    def drawdown(df):
        return (df - df.cummax()) / df.cummax()


    def calcular_kpis_vector(df_panel):
        ret_final = df_panel.iloc[-1]
        vol_anual = df_panel.std() * np.sqrt(252)
        sharpe = (ret_final - rf) / vol_anual
        max_dd = drawdown(df_panel).min()
        calmar = ret_final / abs(max_dd)
        var5 = df_panel.quantile(0.05)
        kpi_df = pd.DataFrame({
            "Rentabilidad Final": ret_final,
            "Volatilidad Anualizada": vol_anual,
            "Sharpe": sharpe,
            "Calmar": calmar,
            "Drawdown Max": max_dd,
            "VaR5": var5
        })
        return kpi_df


    def generar_grafico_panel(df_panel, activos_panel, metricas_panel, benchmark=None, panel_name="Panel"):
        fig = go.Figure()
        for a in activos_panel:
            for met in metricas_panel:
                if met == "Rentabilidad":
                    fig.add_trace(go.Scatter(x=df_panel.index, y=df_panel[a], mode='lines', name=f"{a} Rentabilidad"))
                elif met == "Drawdown":
                    fig.add_trace(go.Scatter(x=df_panel.index, y=drawdown(df_panel[a]), mode='lines',
                                             name=f"{a} Drawdown", line=dict(dash='dot')))
                elif met in ["Sharpe", "Calmar", "VaR5"]:
                    val = (df_panel[a] - df_panel[a].min()) / (df_panel[a].max() - df_panel[a].min())
                    fig.add_trace(go.Scatter(x=df_panel.index, y=val, mode='lines', name=f"{a} {met} (norm)"))
        if benchmark and benchmark in df_panel.columns:
            fig.add_trace(go.Scatter(x=df_panel.index, y=df_panel[benchmark], mode='lines',
                                     name=f"Benchmark ({benchmark})", line=dict(color='black', width=3, dash='dash')))
        fig.update_layout(title=f"{panel_name} - Métricas Seleccionadas",
                          xaxis_title="Fecha", yaxis_title="Valor",
                          legend=dict(orientation="h", y=-0.3))
        return fig


    def categorizar_activos(activos):
        criptos_ref = ["BTC", "ETH", "SOL", "ADA", "DOT"]
        categorias = {}
        for a in activos:
            if any(c in a for c in criptos_ref):
                categorias[a] = "Criptos"
            else:
                categorias[a] = "ETF/Bonos"
        return categorias


    def generar_conclusiones_automatizadas(kpis, categorias):
        conclusiones = {}
        for cat in set(categorias.values()):
            activos_cat = [a for a, c in categorias.items() if c == cat and a in kpis.index]
            if activos_cat:
                kpis_cat = kpis.loc[activos_cat]
                mejor_sharpe = kpis_cat["Sharpe"].idxmax()
                peor_dd = kpis_cat["Drawdown Max"].idxmin()
                mayor_rent = kpis_cat["Rentabilidad Final"].idxmax()
                conclusiones[cat] = [
                    f"- Mejor Sharpe: **{mejor_sharpe}** ({kpis_cat.loc[mejor_sharpe, 'Sharpe']:.2f})",
                    f"- Peor Drawdown: **{peor_dd}** ({kpis_cat.loc[peor_dd, 'Drawdown Max']:.2%})",
                    f"- Mayor rentabilidad: **{mayor_rent}** ({kpis_cat.loc[mayor_rent, 'Rentabilidad Final']:.2%})"
                ]
            else:
                conclusiones[cat] = ["- No hay activos en esta categoría."]
        return conclusiones


    # --------------------------
    # Tabs
    tab_kpis, tab_graficos, tab_analisis, tab_doc = st.tabs(
        ["📈 KPIs", "📊 Gráficos", "📊 Análisis R/R", "📖 Documentación"])

    # --------------------------
    # TAB KPIs
    with tab_kpis:
        st.subheader("📈 KPIs por periodo seleccionable")
        activos_kpis = st.multiselect("Selecciona activos para KPIs", activos, default=activos[:6], key="kpis_activos")
        periodos_seleccionados = st.multiselect("Selecciona periodos a analizar", list(periodos_dias.keys()),
                                                default=list(periodos_dias.keys()), key="kpis_periodos")
        categorias_activos = categorizar_activos(activos_kpis)

        for per in periodos_seleccionados:
            n_dias = periodos_dias[per]
            df_periodo = rentabilidades[activos_kpis].iloc[-n_dias:]
            kpis_periodo = calcular_kpis_vector(df_periodo)
            conclusiones_auto = generar_conclusiones_automatizadas(kpis_periodo, categorias_activos)

            st.markdown(f"### Periodo: {per}")
            st.markdown("**Conclusiones Automáticas**")
            for categoria, lines in conclusiones_auto.items():
                st.markdown(f"**{categoria}**")
                for line in lines:
                    st.markdown(line)

            st.dataframe(kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                                     "Drawdown Max", "VaR5"])
                         .format("{:.2f}", subset=["Sharpe", "Calmar"]))

    # --------------------------
    # TAB GRÁFICOS CON PANEL EXPANDIBLE Y ANCHO AJUSTABLE
    with tab_graficos:
        st.subheader("📊 Gráficos Interactivos - Panel A y B")

        # Slider para ajustar ancho de los paneles
        ancho_a = st.slider("Ancho Panel A (%)", 20, 80, 50, key="ancho_a_slider")
        col_a, col_b = st.columns([ancho_a, 100 - ancho_a])

        # Panel A
        with col_a:
            with st.expander("Panel A - Abrir / Cerrar", expanded=True):
                activos_a = st.multiselect("Activos Panel A", activos, default=["BTC", "ETH", "SOL"], key="activos_a")
                periodo_a = st.selectbox("Periodo Panel A", list(periodos_dias.keys()), key="periodo_a")
                benchmark_a = st.selectbox("Benchmark Panel A", activos_a, key="benchmark_a")
                metricas_a = st.multiselect("Métricas Panel A", metricas_completas, default=metricas_completas,
                                            key="metricas_a")
                n_a = periodos_dias[periodo_a]
                df_a = rentabilidades[activos_a].iloc[-n_a:]
                fig_a = generar_grafico_panel(df_a, activos_a, metricas_a, benchmark_a, "Panel A")
                st.plotly_chart(fig_a, use_container_width=True)

        # Panel B
        with col_b:
            with st.expander("Panel B - Abrir / Cerrar", expanded=True):
                activos_b = st.multiselect("Activos Panel B", activos, default=["VT", "SUSA", "SUSC"], key="activos_b")
                periodo_b = st.selectbox("Periodo Panel B", list(periodos_dias.keys()), key="periodo_b")
                benchmark_b = st.selectbox("Benchmark Panel B", activos_b, key="benchmark_b")
                metricas_b = st.multiselect("Métricas Panel B", metricas_completas, default=metricas_completas,
                                            key="metricas_b")
                n_b = periodos_dias[periodo_b]
                df_b = rentabilidades[activos_b].iloc[-n_b:]
                fig_b = generar_grafico_panel(df_b, activos_b, metricas_b, benchmark_b, "Panel B")
                st.plotly_chart(fig_b, use_container_width=True)

    # --------------------------
    # TAB ANALISIS RIESGO / RENTABILIDAD
    with tab_analisis:
        st.subheader("📊 Análisis Rentabilidad / Riesgo por Periodo")
        activos_analisis = st.multiselect("Selecciona activos a analizar", activos, default=activos[:6],
                                          key="analisis_activos")
        periodos_analisis = st.multiselect("Selecciona periodos a analizar", list(periodos_dias.keys()),
                                           default=list(periodos_dias.keys()), key="analisis_periodos")
        metricas_analisis = st.multiselect("Métricas a analizar", metricas_completas,
                                           default=["Rentabilidad", "Drawdown"], key="analisis_metricas")

        for per in periodos_analisis:
            n = periodos_dias[per]
            df_periodo = rentabilidades[activos_analisis].iloc[-n:]
            st.markdown(f"### Periodo: {per}")
            fig = generar_grafico_panel(df_periodo, activos_analisis, metricas_analisis, panel_name=f"Análisis {per}")
            st.plotly_chart(fig, use_container_width=True)
            kpis_periodo = calcular_kpis_vector(df_periodo)
            st.dataframe(kpis_periodo.style.format("{:.2%}",
                                                   subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                           "Drawdown Max",
                                                           "VaR5"])
                         .format("{:.2f}", subset=["Sharpe", "Calmar"]))

    # --------------------------
    # TAB DOCUMENTACIÓN
    with tab_doc:
        st.subheader("📖 Documentación")
        st.markdown("""
           ### Propósito
           Dashboard profesional para analizar **rentabilidad y riesgo** de activos financieros.

           ### Métricas principales
           - Rentabilidad Final, Volatilidad Anualizada, Sharpe, Calmar, Drawdown Max, VaR5

           ### Uso de Paneles
           - Panel A y B comparan activos y métricas.
           - Selección de benchmark y métricas completas.
           - Tab de Análisis permite evaluar distintos periodos.
           - KPIs muestran automáticamente por periodos y con conclusiones categorizadas.
           - Gráficos están enmarcados para mejorar visibilidad y organización.
           """)














