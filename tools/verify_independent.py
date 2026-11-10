"""Auditor independente em SQLite para dimensionamento de pilares ABNT NBR 6118:2023.

Este script é 100% autônomo: NÃO importa o pacote `pilares_concreto_nbr6118`.
Utiliza apenas a biblioteca padrão do Python (`sqlite3`, `json`, `sys`, `math`, `os`).
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
from typing import Any, Dict


def criar_banco_auditoria() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE parametros_normativos (
        chave TEXT PRIMARY KEY,
        valor REAL,
        descricao TEXT
    );
    """)

    cur.executescript("""
    INSERT INTO parametros_normativos (chave, valor, descricao) VALUES
        ('gamma_c', 1.40, 'Coeficiente de minoração do concreto'),
        ('gamma_s', 1.15, 'Coeficiente de minoração do aço'),
        ('gamma_f', 1.40, 'Coeficiente de majoração das ações'),
        ('b_min_cm', 14.0, 'Dimensão mínima transversal de pilares em cm'),
        ('ac_min_cm2', 360.0, 'Área mínima da seção transversal do pilar em cm²'),
        ('lambda_max', 200.0, 'Esbeltez máxima admissível para pilares'),
        ('rho_min_ac', 0.004, 'Taxa geométrica mínima absoluta de armadura (0,4% Ac)'),
        ('rho_min_nsd', 0.0015, 'Taxa mínima em função da força normal (0,15% Nsd/fyd)'),
        ('rho_max', 0.08, 'Taxa máxima absoluta de armadura em emendas (8% Ac)');
    """)

    cur.execute("""
    CREATE TABLE pilares_auditados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacao TEXT,
        b_cm REAL,
        h_cm REAL,
        ac_cm2 REAL,
        l_cm REAL,
        le_cm REAL,
        gamman REAL,
        lambda_val REAL,
        lambda1 REAL,
        nk_kn REAL,
        nsd_kn REAL,
        e1_cm REAL,
        ea_cm REAL,
        e2_cm REAL,
        etot_cm REAL,
        msd_tot_knm REAL,
        as_min_cm2 REAL,
        as_adotada_cm2 REAL,
        qtd_barras INTEGER,
        bitola_l_mm REAL,
        bitola_t_mm REAL,
        esp_estribos_cm REAL,
        status_dimensoes TEXT,
        status_esbeltez TEXT,
        status_taxa_armadura TEXT,
        status_geral TEXT
    );
    """)

    conn.commit()
    return conn


def fracao_para_float(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict) and "num" in v and "den" in v:
        return float(v["num"]) / float(v["den"])
    if isinstance(v, str):
        if "/" in v:
            p = v.split("/")
            return float(p[0]) / float(p[1])
        return float(v)
    raise ValueError(f"Não foi possível converter {v} em número.")


def auditar_arquivo_projeto(caminho_json: str, conn: sqlite3.Connection) -> bool:
    if not os.path.exists(caminho_json):
        print(f"[ERRO] Arquivo não encontrado: {caminho_json}")
        return False

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    identificacao = dados.get("identificacao", "Pilar Sem Nome")
    geo = dados.get("geometria", {})
    b = fracao_para_float(geo["largura_b_cm"])
    h = fracao_para_float(geo["comprimento_h_cm"])
    l = fracao_para_float(geo["altura_livre_l_cm"])
    alpha = fracao_para_float(geo.get("coeficiente_flambagem_alpha", 1.0))

    esf = dados.get("esforcos", {})
    nk = fracao_para_float(esf["forca_normal_nk_kn"])
    mk_topo = abs(fracao_para_float(esf.get("momento_topo_mk_topo_knm", 0.0)))
    mk_base = abs(fracao_para_float(esf.get("momento_base_mk_base_knm", 0.0)))
    eixo = esf.get("eixo_flexao", "h")

    mat = dados.get("materiais", {})
    fck = fracao_para_float(mat.get("classe_concreto_fck", 25))

    # 1. Geometria e Coeficiente gamma_n
    ac = b * h
    menor_dim = min(b, h)
    if menor_dim >= 19.0:
        gamman = 1.00
    else:
        gamman = 1.95 - 0.05 * menor_dim

    status_dim = "CONFORME" if (menor_dim >= 14.0 and ac >= 360.0) else "REPROVADO"

    # 2. Esbeltez e Raio de Giração
    le = l * alpha
    dim_flexao = h if eixo == "h" else b
    i_giracao = dim_flexao / math.sqrt(12.0)
    lambda_val = le / i_giracao
    status_esbeltez = "CONFORME" if lambda_val <= 200.0 else "REPROVADO"

    # 3. Esforços de Cálculo e Excentricidades
    gamma_f = 1.40
    gamma_c = 1.40
    gamma_s = 1.15
    nsd = nk * gamma_f * gamman

    m1k_max = max(mk_topo, mk_base)
    m1k_min = min(mk_topo, mk_base)
    m1d_max_kNcm = m1k_max * 100.0 * gamma_f * gamman
    m1d_min_kNcm = m1k_min * 100.0 * gamma_f * gamman

    e1 = (m1d_max_kNcm / nsd) if nsd > 0 else 0.0
    if m1d_max_kNcm > 0:
        alpha_b = max(0.40, 0.60 + 0.40 * (m1d_min_kNcm / m1d_max_kNcm))
    else:
        alpha_b = 1.00

    e1_equiv = max(alpha_b * e1, 0.40 * e1)
    ea = max(le / 400.0, dim_flexao / 30.0, 1.50)
    e1_tot = e1_equiv + ea

    lambda1 = max(35.0, min(90.0, (25.0 + 12.5 * (e1 / dim_flexao)) / alpha_b))

    fcd_kN_cm2 = (fck / 10.0) / gamma_c
    nu = nsd / (ac * fcd_kN_cm2)

    if lambda_val <= lambda1:
        e2 = 0.0
    else:
        um_sobre_r = min(0.005 / (dim_flexao * (nu + 0.5)), 0.005 / dim_flexao)
        e2 = ((le ** 2) / 10.0) * um_sobre_r

    etot = e1_tot + e2
    msd_tot_kNm = (nsd * etot) / 100.0

    # 4. Armadura Mínima e Adotada
    fyd_kN_cm2 = 50.0 / gamma_s
    as_min_1 = 0.0015 * (nsd / fyd_kN_cm2)
    as_min_2 = 0.004 * ac
    as_min = max(as_min_1, as_min_2)
    as_max = 0.08 * ac

    # Estimativa de armadura adotada
    mu = (nsd * etot) / ((b if eixo == "h" else h) * (dim_flexao ** 2) * fcd_kN_cm2)
    braço_aco = 0.80
    mu_c = (nu * (1.0 - nu)) / 2.0 if nu <= 0.80 else max(0.0, 0.16 * (1.0 - (nu - 0.80)))
    delta_mu = mu - mu_c
    omega = max(0.0, delta_mu / (braço_aco / 2.0)) if delta_mu > 0 else (nu - 1.0 if nu > 1.0 else 0.0)
    as_calc = omega * (ac * fcd_kN_cm2) / fyd_kN_cm2
    as_adotada = max(as_calc, as_min)

    status_taxa = "CONFORME" if as_adotada <= as_max else "REPROVADO"

    # 5. Detalhamento de barras
    qtd_barras = 4
    area_barra_125 = 1.227
    while qtd_barras * area_barra_125 < as_adotada:
        qtd_barras += 2
    bitola_l_mm = 12.5
    bitola_t_mm = 5.0
    esp_estribos_cm = min(20.0, menor_dim, 12.0 * (bitola_l_mm / 10.0))

    status_geral = "APROVADO" if all(
        s == "CONFORME" for s in (status_dim, status_esbeltez, status_taxa)
    ) else "REPROVADO"

    cur = conn.cursor()
    cur.execute("""
    INSERT INTO pilares_auditados (
        identificacao, b_cm, h_cm, ac_cm2, l_cm, le_cm, gamman,
        lambda_val, lambda1, nk_kn, nsd_kn, e1_cm, ea_cm, e2_cm,
        etot_cm, msd_tot_knm, as_min_cm2, as_adotada_cm2,
        qtd_barras, bitola_l_mm, bitola_t_mm, esp_estribos_cm,
        status_dimensoes, status_esbeltez, status_taxa_armadura, status_geral
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        identificacao, b, h, ac, l, le, gamman,
        lambda_val, lambda1, nk, nsd, e1, ea, e2,
        etot, msd_tot_kNm, as_min, as_adotada,
        qtd_barras, bitola_l_mm, bitola_t_mm, esp_estribos_cm,
        status_dim, status_esbeltez, status_taxa, status_geral,
    ))
    conn.commit()

    print(f"\n================================================================================")
    print(f"AUDITORIA INDEPENDENTE SQLITE: {identificacao}")
    print(f"================================================================================")
    print(f" Seção: {b:.1f} x {h:.1f} cm (Ac = {ac:.1f} cm²) | gamma_n = {gamman:.2f} -> [{status_dim}]")
    print(f" Comprimento le: {le:.1f} cm | Raio i = {i_giracao:.2f} cm | lambda = {lambda_val:.1f} (Limite: 200) -> [{status_esbeltez}]")
    print(f" Carga Nk: {nk:.1f} kN -> Nsd = {nsd:.1f} kN")
    print(f" Excentricidades: e1 = {e1:.2f} cm | ea = {ea:.2f} cm | e2 = {e2:.2f} cm -> etot = {etot:.2f} cm")
    print(f" Momento Total Msd: {msd_tot_kNm:.2f} kN·m | Esbeltez Limite lambda_1 = {lambda1:.1f}")
    print(f" Armadura: As,min = {as_min:.2f} cm² | As,adot = {as_adotada:.2f} cm² <= As,max = {as_max:.2f} cm² -> [{status_taxa}]")
    print(f" Detalhamento: {qtd_barras} Φ {bitola_l_mm:.1f} mm | Estribos: Φ {bitola_t_mm:.1f} mm c/ {esp_estribos_cm:.1f} cm")
    print(f" STATUS GERAL DA AUDITORIA: [{status_geral}]")
    print(f"================================================================================")

    return status_geral == "APROVADO"


def main() -> int:
    conn = criar_banco_auditoria()
    exemplos = [
        "examples/pilar_intermediario_esbeltez_moderada.json",
        "examples/pilar_canto_alta_carga_fita.json",
    ]

    sucessos = 0
    for ex in exemplos:
        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ex)
        if auditar_arquivo_projeto(caminho, conn):
            sucessos += 1

    print(f"\nResumo da Auditoria Independente: {sucessos}/{len(exemplos)} projetos aprovados.")
    return 0 if sucessos == len(exemplos) else 1


if __name__ == "__main__":
    sys.exit(main())
