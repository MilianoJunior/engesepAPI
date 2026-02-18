-- Tabela de cache de produção mensal histórica por usina/UG
-- Populada automaticamente pela API na primeira requisição de cada mês fechado.
-- Nunca modificar manualmente sem entender o impacto nos cálculos de rollover.

CREATE TABLE IF NOT EXISTS producao_historica (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    usina         VARCHAR(64)     NOT NULL,
    mes           CHAR(7)         NOT NULL,        -- formato: YYYY-MM
    coluna        VARCHAR(128)    NOT NULL,         -- ex: UG-01 Energia Acumulada
    producao_mwh  DECIMAL(12, 3)  NOT NULL,
    calculado_em  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_usina_mes_coluna (usina, mes, coluna)
);
