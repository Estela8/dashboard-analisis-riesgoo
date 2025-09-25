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
    criptos_ref = ["BTC", "ETH", "SOL"]
    categorias = {}
    for a in activos:
        if any(c in a for c in criptos_ref):
            categorias[a] = "Criptos"
        else:
            categorias[a] = "ETF/Bonos"
    return categorias