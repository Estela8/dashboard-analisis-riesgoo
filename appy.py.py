
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
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
    # Tabs
    tab_kpis, tab_graficos, tab_analisis, tab_rv, tab_comp, tab_dd, tab_div, tab_corr, tab_doc = st.tabs(
        ["📈 KPIs", "📊 Gráficos", "📊 Análisis R/R",
         "⚖️ Riesgo vs Retorno", "📈 Comparativa Periodos", "📉 Drawdown",
         "🥧 Diversificación", "🔗 Correlaciones", "📖 Documentación"])

    # --------------------------
    # TAB KPIs
    with tab_kpis:
        st.subheader("📈 KPIs por periodo seleccionable")

        # Selección de activos y periodos
        activos_kpis = st.multiselect(
            "Selecciona activos para KPIs",
            activos,
            default=st.session_state.get('activos_seleccionados', activos[:2]),
            key="kpis_activos"
        )
        periodos_seleccionados = st.multiselect(
            "Selecciona periodos a analizar",
            list(periodos_dias.keys()),
            default=list(periodos_dias.keys()),
            key="kpis_periodos"
        )

        # Guardar selección global
        st.session_state['activos_seleccionados'] = activos_kpis
        categorias_activos = categorizar_activos(activos_kpis)


        def color_val_html(val):
            color = 'green' if val >= 0 else 'red'
            if isinstance(val, float):
                if abs(val) < 1:  # porcentaje
                    return f'<span style="color:{color}">{val:.2%}</span>'
                else:  # números grandes (Sharpe, Calmar)
                    return f'<span style="color:{color}">{val:.2f}</span>'
            return f'<span style="color:{color}">{val}</span>'


        for per in periodos_seleccionados:
            n_dias = periodos_dias[per]
            df_periodo = rentabilidades[activos_kpis].iloc[-n_dias:]
            kpis_periodo = calcular_kpis_vector(df_periodo)

            # Conclusiones automáticas con HTML coloreado
            conclusiones_auto = {}
            for cat in set(categorias_activos.values()):
                activos_cat = [a for a, c in categorias_activos.items() if c == cat and a in kpis_periodo.index]
                if activos_cat:
                    kpis_cat = kpis_periodo.loc[activos_cat]
                    mejor_sharpe = kpis_cat["Sharpe"].idxmax()
                    peor_dd = kpis_cat["Drawdown Max"].idxmin()
                    mayor_rent = kpis_cat["Rentabilidad Final"].idxmax()
                    mayor_vol = kpis_cat["Volatilidad Anualizada"].idxmax()
                    mayor_calmar = kpis_cat["Calmar"].idxmax()
                    menor_var5 = kpis_cat["VaR5"].idxmin()

                    conclusiones_auto[cat] = [
                        f"- Mejor Sharpe: <b>{mejor_sharpe}</b> ({color_val_html(kpis_cat.loc[mejor_sharpe, 'Sharpe'])})",
                        f"- Peor Drawdown: <b>{peor_dd}</b> ({color_val_html(kpis_cat.loc[peor_dd, 'Drawdown Max'])})",
                        f"- Mayor Rentabilidad: <b>{mayor_rent}</b> ({color_val_html(kpis_cat.loc[mayor_rent, 'Rentabilidad Final'])})",
                        f"- Mayor Volatilidad: <b>{mayor_vol}</b> ({color_val_html(kpis_cat.loc[mayor_vol, 'Volatilidad Anualizada'])})",
                        f"- Mayor Calmar: <b>{mayor_calmar}</b> ({color_val_html(kpis_cat.loc[mayor_calmar, 'Calmar'])})",
                        f"- Peor VaR5: <b>{menor_var5}</b> ({color_val_html(kpis_cat.loc[menor_var5, 'VaR5'])})"
                    ]
                else:
                    conclusiones_auto[cat] = ["- No hay activos en esta categoría."]

            # Mostrar conclusiones con HTML
            st.markdown(f"### Periodo: {per}")
            st.markdown("**Conclusiones Automáticas**")
            for categoria, lines in conclusiones_auto.items():
                st.markdown(f"**{categoria}**")
                for line in lines:
                    st.markdown(line, unsafe_allow_html=True)


            # Mostrar tabla coloreada
            def color_pos_neg(val):
                color = 'green' if val >= 0 else 'red'
                return f'color: {color}'


            st.dataframe(
                kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                            "Drawdown Max", "VaR5"])
                .format("{:.2f}", subset=["Sharpe", "Calmar"])
                .applymap(color_pos_neg)
            )


    # --------------------------
    # TAB GRÁFICOS CON PANEL EXPANDIBLE Y ANCHO AJUSTABLE
    with tab_graficos:
        st.subheader("📊 Gráficos Interactivos - Panel A y B")

        ancho_a = st.slider("Ancho Panel A (%)", 20, 80, 50, key="ancho_a_slider")
        col_a, col_b = st.columns([ancho_a, 100 - ancho_a])

        # Panel A
        with col_a:
            with st.expander("Panel A - Abrir / Cerrar", expanded=True):
                activos_a = st.multiselect(
                    "Activos Panel A",
                    activos,
                    default=st.session_state.get('activos_seleccionados', ["BTC", "ETH", "SOL"]),
                    key="activos_a"
                )
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
                activos_b = st.multiselect(
                    "Activos Panel B",
                    activos,
                    default=st.session_state.get('activos_seleccionados', ["VT", "SUSA", "SUSC"]),
                    key="activos_b"
                )
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

        activos_analisis = st.multiselect(
            "Selecciona activos a analizar",
            activos,
            default=st.session_state.get('activos_seleccionados', activos[:6]),
            key="analisis_activos"
        )
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
    # TAB RIESGO VS RETORNO
    with tab_rv:
        st.subheader("⚖️ Riesgo vs Retorno")
        st.markdown("### ❗ ¿Estoy recibiendo suficiente rentabilidad por el riesgo asumido?")

        activos_rv = st.session_state.get('activos_seleccionados', activos[:6])
        df_rv = rentabilidades[activos_rv]  # LOS DATOS QUE SE GRAFICAN
        kpis_rv = calcular_kpis_vector(df_rv)  # KPIs exactos de lo graficado

        fig_rv = px.scatter(
            kpis_rv,
            x="Volatilidad Anualizada",
            y="Rentabilidad Final",
            color=kpis_rv.index,
            hover_data=["Sharpe", "Calmar", "VaR5"]
        )
        st.plotly_chart(fig_rv, use_container_width=True)

        st.dataframe(
            kpis_rv.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                   "VaR5"])
            .format("{:.2f}", subset=["Sharpe", "Calmar"])
        )

    # --------------------------
    # TAB COMPARATIVA POR PERIODOS
    with tab_comp:
        st.subheader("📈 Comparativa por Periodos")
        st.markdown("### ❗ ¿Cómo se han comportado los activos en distintos horizontes de tiempo?")

        # Usar la selección global de KPIs si existe
        activos_comp = st.session_state.get('activos_seleccionados', activos[:6])

        tabs_comp = st.tabs(list(periodos_dias.keys()))
        for i, periodo in enumerate(periodos_dias.keys()):
            with tabs_comp[i]:
                df_periodo = rentabilidades[activos_comp].iloc[-periodos_dias[periodo]:].cumsum()
                fig_comp = go.Figure()
                for a in activos_comp:
                    fig_comp.add_trace(go.Scatter(x=df_periodo.index, y=df_periodo[a], mode="lines", name=a))
                fig_comp.update_layout(title=f"Rentabilidad acumulada {periodo}")
                st.plotly_chart(fig_comp, use_container_width=True)

                # KPIs sobre los datos graficados
                kpis_periodo = calcular_kpis_vector(rentabilidades[activos_comp].iloc[-periodos_dias[periodo]:])
                st.dataframe(
                    kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                                "Drawdown Max", "VaR5"])
                    .format("{:.2f}", subset=["Sharpe", "Calmar"]))

    # --------------------------
    # TAB DRAWDOWN
    with tab_dd:
        st.subheader("📉 Drawdown Histórico")
        st.markdown("### ❗ ¿Cuál ha sido la peor caída de cada activo y cuánto duró?")

        # Usar la selección global de KPIs si existe
        activos_dd = st.session_state.get('activos_seleccionados', activos[:6])

        # Graficar drawdown
        fig_dd = go.Figure()
        for a in activos_dd:
            fig_dd.add_trace(go.Scatter(
                x=rentabilidades.index,
                y=drawdown(rentabilidades[a]),
                mode="lines",
                name=a,
                stackgroup="one"
            ))
        fig_dd.update_layout(title="Drawdowns")
        st.plotly_chart(fig_dd, use_container_width=True)

        # KPIs sobre los datos graficados
        kpis_periodo = calcular_kpis_vector(rentabilidades[activos_comp].iloc[-periodos_dias[periodo]:])
        st.dataframe(
            kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                        "Drawdown Max", "VaR5"])
            .format("{:.2f}", subset=["Sharpe", "Calmar"]))

    # --------------------------
    # TAB DIVERSIFICACIÓN
    with tab_div:
        st.subheader("🥧 Diversificación de Activos")
        st.markdown("### ❗ ¿Cómo está distribuida mi cartera entre categorías de activos?")

        # Usar la selección global de KPIs si existe
        activos_div = st.session_state.get('activos_seleccionados', activos[:6])
        categorias_global = categorizar_activos(activos_div)
        counts = pd.Series(categorias_global).value_counts()

        fig_pie = px.pie(
            values=counts.values,
            names=counts.index,
            title="Distribución por Categoría"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # KPIs sobre los datos graficados
        kpis_periodo = calcular_kpis_vector(rentabilidades[activos_comp].iloc[-periodos_dias[periodo]:])
        st.dataframe(
            kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                        "Drawdown Max", "VaR5"])
            .format("{:.2f}", subset=["Sharpe", "Calmar"]))

    # --------------------------
    # TAB CORRELACIONES
    with tab_corr:
        st.subheader("🔗 Correlaciones entre Activos")
        st.markdown("### ❗ Los activos que tengo, ¿realmente me diversifican o se mueven juntos? ")

        # Usar la selección global de KPIs si existe
        activos_corr = st.session_state.get('activos_seleccionados', activos[:6])
        corr = rentabilidades[activos_corr].corr()


        fig_heat = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Correlaciones entre Activos Seleccionados"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # KPIs sobre los datos graficados
        kpis_periodo = calcular_kpis_vector(rentabilidades[activos_comp].iloc[-periodos_dias[periodo]:])
        st.dataframe(
            kpis_periodo.style.format("{:.2%}", subset=["Rentabilidad Final", "Volatilidad Anualizada",
                                                        "Drawdown Max", "VaR5"])
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














