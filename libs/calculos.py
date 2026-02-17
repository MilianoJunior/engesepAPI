import os
import pandas as pd


class Calculos:
    def __init__(self):
        self.debug = os.getenv('CALCULOS_DEBUG', '0').strip().lower() in {'1', 'true', 'yes', 'on'}
        meses_debug_raw = os.getenv('CALCULOS_DEBUG_MESES', '').strip()
        self.debug_meses = {m.strip() for m in meses_debug_raw.split(',') if m.strip()}

        self.counter_max_override = self._read_float_env('ENERGIA_COUNTER_MAX', None)
        self.rollover_prev_ratio = self._read_float_env('ENERGIA_ROLLOVER_PREV_RATIO', 0.85)
        self.rollover_curr_ratio = self._read_float_env('ENERGIA_ROLLOVER_CURR_RATIO', 0.25)
        self.rollover_drop_ratio = self._read_float_env('ENERGIA_ROLLOVER_DROP_RATIO', 0.35)
        self.rollover_rebound_ratio = self._read_float_env('ENERGIA_ROLLOVER_REBOUND_RATIO', 0.80)
        self.ignore_zero_readings = os.getenv('ENERGIA_IGNORE_ZERO_READINGS', '1').strip().lower() in {
            '1', 'true', 'yes', 'on'
        }

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
        rows_entrada = len(base)
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
        rows_sentinela = int(mask_sentinela.sum())
        base = base[~mask_sentinela]
        if base.empty:
            return []

        # Deduplica por timestamp, mantendo leitura mais recente.
        base = base.drop_duplicates(subset=['data_hora'], keep='last')

        # Regra de negócio para correção histórica da usina Aparecida.
        if usina == 'CGH-APARECIDA':
            for col in colunas_energia:
                base[col] = base[col] + 9971.39

        if self.debug:
            print(
                f"[CALC-DEBUG] usina={usina} periodo={periodo} "
                f"rows_entrada={rows_entrada} rows_pos_limpeza={len(base)} "
                f"rows_sentinela={rows_sentinela} colunas_energia={len(colunas_energia)}"
            )

        if periodo == 'M':
            saida = self._calcular_mensal(base, colunas_energia, usina)
            return self._to_resultado_json(saida, periodo)

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

    def _read_float_env(self, key: str, default: float | None) -> float | None:
        value = os.getenv(key)
        if value is None or str(value).strip() == '':
            return default
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _agrupar_por_periodo(self, df: pd.DataFrame, colunas_energia: list[str], periodo: str) -> pd.DataFrame:
        if periodo == 'H':
            chave = df['data_hora'].dt.floor('h')
            return df.groupby(chave)[colunas_energia].agg(['first', 'last'])
        if periodo == 'D':
            chave = df['data_hora'].dt.date
            return df.groupby(chave)[colunas_energia].agg(['first', 'last'])

        chave = df['data_hora'].dt.to_period('M').astype(str)
        return df.groupby(chave)[colunas_energia].agg(['first', 'last'])

    def _calcular_mensal(self, df: pd.DataFrame, colunas_energia: list[str], usina: str) -> pd.DataFrame:
        """
        Produção mensal robusta para acumuladores com rollover/reset:
        soma incrementos positivos e corrige quedas por estouro de contador.
        """
        chave_mes = df['data_hora'].dt.to_period('M').astype(str)
        meses = pd.Index(sorted(chave_mes.unique()), name='mes')
        saida = pd.DataFrame(index=meses)

        for col in colunas_energia:
            serie_raw = pd.to_numeric(df[col], errors='coerce')
            serie_norm, offset = self._normalizar_serie_contador(serie_raw)
            teto_contador = self._infer_counter_ceiling(serie_norm)

            producao_mes = {}
            for mes in meses:
                mask_mes = chave_mes == mes
                serie_mes_norm = serie_norm[mask_mes]
                serie_mes_raw = serie_raw[mask_mes]
                total_mes, meta = self._somar_incrementos_periodo(serie_mes_norm, teto_contador)
                producao_mes[mes] = round(total_mes, 3)

                if self.debug and (not self.debug_meses or mes in self.debug_meses):
                    self._log_mensal_debug(
                        usina=usina,
                        mes=mes,
                        coluna=col,
                        serie_mes_raw=serie_mes_raw,
                        teto_contador=teto_contador,
                        offset=offset,
                        total_mes=total_mes,
                        meta=meta,
                    )

            saida[f'prod_{col}'] = pd.Series(producao_mes).reindex(meses).fillna(0.0)

        return saida

    def _normalizar_serie_contador(self, serie: pd.Series) -> tuple[pd.Series, float]:
        serie_num = pd.to_numeric(serie, errors='coerce')
        if serie_num.dropna().empty:
            return serie_num, 0.0
        offset = float(serie_num.min(skipna=True))
        return serie_num - offset, offset

    def _infer_counter_ceiling(self, serie_norm: pd.Series) -> float | None:
        if self.counter_max_override is not None and self.counter_max_override > 0:
            return float(self.counter_max_override)

        max_obs = float(serie_norm.max(skipna=True)) if not serie_norm.dropna().empty else 0.0
        if max_obs <= 0:
            return None
        return max_obs

    def _somar_incrementos_periodo(self, serie_periodo: pd.Series, teto_contador: float | None) -> tuple[float, dict]:
        vals_raw = pd.to_numeric(serie_periodo, errors='coerce').dropna().to_numpy(dtype=float)
        zeros_ignorados = 0
        if self.ignore_zero_readings:
            vals = vals_raw[vals_raw != 0.0]
            zeros_ignorados = int(len(vals_raw) - len(vals))
        else:
            vals = vals_raw

        if len(vals) < 2:
            return 0.0, {
                'leituras': int(len(vals)),
                'rollovers': 0,
                'quedas_ignoradas': 0,
                'rollovers_descartados_rebound': 0,
                'zeros_ignorados': int(zeros_ignorados),
            }

        total = 0.0
        rollovers = 0
        quedas_ignoradas = 0
        rollovers_descartados_rebound = 0
        prev = vals[0]

        for idx in range(1, len(vals)):
            curr = vals[idx]
            diff = curr - prev
            if diff >= 0:
                total += diff
                prev = curr
                continue

            incremento_rollover = self._resolver_incremento_rollover(prev, curr, teto_contador)
            if incremento_rollover is not None:
                # Evita falso rollover por leitura espúria pontual:
                # queda abrupta seguida de retorno imediato para perto do valor anterior.
                next_val = vals[idx + 1] if (idx + 1) < len(vals) else None
                if next_val is not None and next_val >= (prev * self.rollover_rebound_ratio):
                    rollovers_descartados_rebound += 1
                    quedas_ignoradas += 1
                    continue

                total += incremento_rollover
                prev = curr
                rollovers += 1
                continue

            # Queda sem padrão de rollover: ignora leitura ruim e mantém referência anterior.
            quedas_ignoradas += 1

        return max(total, 0.0), {
            'leituras': int(len(vals)),
            'rollovers': int(rollovers),
            'quedas_ignoradas': int(quedas_ignoradas),
            'rollovers_descartados_rebound': int(rollovers_descartados_rebound),
            'zeros_ignorados': int(zeros_ignorados),
        }

    def _resolver_incremento_rollover(
        self,
        prev: float,
        curr: float,
        teto_contador: float | None,
    ) -> float | None:
        if teto_contador is None or teto_contador <= 0:
            return None
        if curr >= prev:
            return None

        drop = prev - curr
        if drop <= 0:
            return None

        prev_ratio = prev / teto_contador
        curr_ratio = curr / teto_contador
        drop_ratio = drop / teto_contador

        eh_rollover = (
            prev_ratio >= self.rollover_prev_ratio and
            (curr_ratio <= self.rollover_curr_ratio or drop_ratio >= self.rollover_drop_ratio)
        )
        if not eh_rollover:
            return None

        incremento = (teto_contador - prev) + curr
        if incremento < 0 or incremento > teto_contador:
            return None
        return incremento

    def _log_mensal_debug(
        self,
        usina: str,
        mes: str,
        coluna: str,
        serie_mes_raw: pd.Series,
        teto_contador: float | None,
        offset: float,
        total_mes: float,
        meta: dict,
    ):
        serie_valid = pd.to_numeric(serie_mes_raw, errors='coerce').dropna()
        first_raw = float(serie_valid.iloc[0]) if not serie_valid.empty else None
        last_raw = float(serie_valid.iloc[-1]) if not serie_valid.empty else None
        min_raw = float(serie_valid.min()) if not serie_valid.empty else None
        max_raw = float(serie_valid.max()) if not serie_valid.empty else None

        print(
            f"[CALC-M-DEBUG] usina={usina} mes={mes} coluna={coluna} "
            f"leituras={meta['leituras']} rollovers={meta['rollovers']} "
            f"quedas_ignoradas={meta['quedas_ignoradas']} "
            f"rollovers_descartados_rebound={meta['rollovers_descartados_rebound']} "
            f"zeros_ignorados={meta['zeros_ignorados']} "
            f"first_raw={first_raw} last_raw={last_raw} min_raw={min_raw} max_raw={max_raw} "
            f"offset={offset} teto={teto_contador} delta_final={round(float(total_mes), 3)} "
            f"regra=soma_incrementos_com_rollover"
        )

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
