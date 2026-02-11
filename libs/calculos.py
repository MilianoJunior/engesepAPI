import pandas as pd

class Calculos:
    def __init__(self):
        pass

    def calcular_energia_acumulada(self, df: pd.DataFrame, periodo: str, usina: str) -> list[dict]:
        """
        Calcula produção por período a partir de colunas acumuladas padronizadas:
        - UG-01 Energia Acumulada
        - UG-02 Energia Acumulada
        """
        if df is None or df.empty:
            return []

        periodo = (periodo or 'D').upper()[0]
        if periodo not in {'H', 'D', 'M'}:
            raise ValueError(f'Período inválido: {periodo}')

        base = df.copy()
        if 'data_hora' not in base.columns:
            return []

        base['data_hora'] = pd.to_datetime(base['data_hora'], errors='coerce')
        base = base[base['data_hora'].notna()].sort_values('data_hora')
        if base.empty:
            return []

        colunas_energia = [
            c for c in base.columns
            if c != 'data_hora' and 'energia acumulada' in c.lower()
        ]
        if not colunas_energia:
            colunas_energia = [c for c in base.columns if c != 'data_hora']

        for col in colunas_energia:
            base[col] = pd.to_numeric(base[col], errors='coerce')

        base = base.dropna(subset=colunas_energia, how='all')
        if base.empty:
            return []

        # Remove sentinela de erro de leitura.
        mask_sentinela = (base[colunas_energia] == 103.00).any(axis=1)
        base = base[~mask_sentinela]
        if base.empty:
            return []

        # Deduplica por timestamp, mantendo leitura mais recente.
        base = base.drop_duplicates(subset=['data_hora'], keep='last')

        # Regra de negócio para correção histórica da usina Aparecida.
        if usina == 'CGH-APARECIDA':
            for col in colunas_energia:
                base[col] = base[col] + 9971.39

        agrupado = self._agrupar_por_periodo(base, colunas_energia, periodo)
        if agrupado.empty:
            return []

        saida = pd.DataFrame(index=agrupado.index)
        for col in colunas_energia:
            delta = agrupado[(col, 'last')] - agrupado[(col, 'first')]
            # Reset/ruído intempestivo não deve gerar produção negativa.
            delta = delta.clip(lower=0).fillna(0)
            saida[f'prod_{col}'] = delta.round(3)

        return self._to_resultado_json(saida, periodo)

    def _agrupar_por_periodo(self, df: pd.DataFrame, colunas_energia: list[str], periodo: str) -> pd.DataFrame:
        if periodo == 'H':
            chave = df['data_hora'].dt.floor('h')
            return df.groupby(chave)[colunas_energia].agg(['first', 'last'])
        if periodo == 'D':
            chave = df['data_hora'].dt.date
            return df.groupby(chave)[colunas_energia].agg(['first', 'last'])

        chave = df['data_hora'].dt.to_period('M').astype(str)
        return df.groupby(chave)[colunas_energia].agg(['first', 'last'])

    def _to_resultado_json(self, df: pd.DataFrame, periodo: str) -> list[dict]:
        if df.empty:
            return []

        resultado = []
        for idx, row in df.iterrows():
            if periodo == 'M':
                data_out = str(idx)
            elif hasattr(idx, 'isoformat'):
                data_out = idx.isoformat()
            else:
                data_out = str(idx)

            item = {'data': data_out}
            for col, val in row.items():
                item[col] = float(val)
            resultado.append(item)

        return resultado
