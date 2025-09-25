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