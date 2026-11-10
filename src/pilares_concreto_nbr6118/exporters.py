"""Exportadores de memorial técnico descritivo e planilhas CSV sanitizadas.

Regras LOFRANO TECNOLOGIA:
  - Sanitização ativa contra injeção de fórmulas CSV (prefixo apostrofo)
  - Memorial analítico estruturado com terminologia rigorosa da ABNT NBR 6118:2023
  - Formatação decimal de Frações sem uso de ponto flutuante

Norma: ABNT NBR 6118:2023.
"""
from __future__ import annotations

import csv
import io
from fractions import Fraction
from typing import Any, List

from pilares_concreto_nbr6118.models import ResultadoProjetoPilar


def formatar_fracao_decimal(f: Fraction, casas: int = 2) -> str:
    """Formata uma fração como string decimal com precisão fixa sem passar por float."""
    if f.denominator == 1:
        parte_int = str(f.numerator)
        parte_dec = "0" * casas
        return f"{parte_int},{parte_dec}" if casas > 0 else parte_int

    sinal = "-" if f < 0 else ""
    num = abs(f.numerator)
    den = f.denominator

    int_part = num // den
    resto = num % den

    digitos_dec = []
    for _ in range(casas):
        resto *= 10
        d = resto // den
        digitos_dec.append(str(d))
        resto = resto % den

    # Arredondamento do último dígito
    resto *= 10
    proximo_d = resto // den
    if proximo_d >= 5:
        idx = casas - 1
        carry = 1
        while idx >= 0 and carry:
            val = int(digitos_dec[idx]) + carry
            if val == 10:
                digitos_dec[idx] = "0"
                carry = 1
                idx -= 1
            else:
                digitos_dec[idx] = str(val)
                carry = 0
        if carry:
            int_part += 1

    dec_str = "".join(digitos_dec)
    return f"{sinal}{int_part},{dec_str}" if casas > 0 else f"{sinal}{int_part}"


def sanitizar_campo_csv(valor: Any) -> str:
    """Protege contra injeção de fórmulas prefixando apóstrofo em caracteres sensíveis."""
    texto = str(valor)
    if texto and texto[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{texto}"
    return texto


def gerar_relatorio_memorial(resultado: ResultadoProjetoPilar) -> str:
    """Gera um memorial técnico descritivo formatado em texto segundo a NBR 6118:2023."""
    geo = resultado.geometria
    esf = resultado.esforcos
    mat = resultado.materiais
    esb = resultado.esbeltez
    exc = resultado.excentricidades
    flx = resultado.flexo_compressao
    det = resultado.detalhamento

    status_str = "APROVADO" if resultado.atende_geral else "REPROVADO"

    linhas = [
        "=" * 80,
        "       LOFRANO TECNOLOGIA - ENGENHARIA ESTRUTURAL E DE SOFTWARE",
        "         MEMORIAL DE CÁLCULO NORMATIVO - PILARES DE CONCRETO ARMADO",
        "=" * 80,
        f"Projeto / Identificação: {resultado.identificacao}",
        f"Norma Regulamentadora:   ABNT NBR 6118:2023",
        f"Status Geral:            {status_str}",
        "-" * 80,
        "1. CARACTERÍSTICAS GEOMÉTRICAS E MATERIAIS",
        f"  - Seção transversal (b x h): {formatar_fracao_decimal(geo.largura_b_cm, 1)} x {formatar_fracao_decimal(geo.comprimento_h_cm, 1)} cm",
        f"  - Área da seção bruta (Ac):  {formatar_fracao_decimal(flx.area_concreto_ac_cm2, 1)} cm²",
        f"  - Altura livre do pilar (l): {formatar_fracao_decimal(geo.altura_livre_l_cm, 1)} cm (alpha = {formatar_fracao_decimal(geo.coeficiente_flambagem_alpha, 2)})",
        f"  - Comprimento efetivo (le):  {formatar_fracao_decimal(esb.comprimento_efetivo_le_cm, 1)} cm",
        f"  - Raio de giração (i):       {formatar_fracao_decimal(esb.raio_giracao_i_cm, 2)} cm",
        f"  - Concreto estrutural:       C{mat.classe_concreto_fck} (fck = {mat.classe_concreto_fck} MPa)",
        f"  - Aço estrutural:            {mat.tipo_aco}",
        f"  - Agressividade Ambiental:   {mat.classe_agressividade} (Cobrimento cnom = {formatar_fracao_decimal(det.cobrimento_adotado_cm, 1)} cm)",
        f"  - Coeficiente gamma_n:       {formatar_fracao_decimal(esb.coeficiente_majoracao_gamman, 2)}",
        "",
        "2. ANÁLISE DE ESBELTEZ E EFEITOS DE 2ª ORDEM LOCAIS",
        f"  - Índice de esbeltez (lambda): {formatar_fracao_decimal(esb.indice_esbeltez_lambda, 1)} (Limite máximo: 200)",
        f"  - Esbeltez limite (lambda_1):  {formatar_fracao_decimal(esb.esbeltez_limite_lambda1, 1)}",
        f"  - Dispensa efeitos 2ª ordem:   {'SIM' if esb.dispensa_segunda_ordem else 'NÃO (Método Pilar-Padrão Curvatura)'}",
        f"  - Força normal serviço (Nk):   {formatar_fracao_decimal(esf.forca_normal_nk_kn, 1)} kN",
        f"  - Força normal cálculo (Nsd):  {formatar_fracao_decimal(exc.forca_normal_calculo_nsd_kn, 1)} kN",
        f"  - Excentricidade 1ª ordem e1:  {formatar_fracao_decimal(exc.excentricidade_primeira_ordem_e1_cm, 2)} cm",
        f"  - Excentricidade acidental ea: {formatar_fracao_decimal(exc.excentricidade_acidental_ea_cm, 2)} cm",
        f"  - Excentricidade 2ª ordem e2:  {formatar_fracao_decimal(exc.excentricidade_segunda_ordem_e2_cm, 2)} cm",
        f"  - Excentricidade total (etot): {formatar_fracao_decimal(exc.excentricidade_total_etot_cm, 2)} cm",
        f"  - Momento fletor total (Msd):  {formatar_fracao_decimal(exc.momento_calculo_total_msd_knm, 2)} kN·m",
        "",
        "3. DIMENSIONAMENTO À FLEXO-COMPRESSÃO NORMAL NO ELU",
        f"  - Força adimensional (nu):     {formatar_fracao_decimal(flx.forca_adimensional_nu, 3)}",
        f"  - Momento adimensional (mu):   {formatar_fracao_decimal(flx.momento_adimensional_mu, 3)}",
        f"  - Taxa mecânica (omega):       {formatar_fracao_decimal(flx.taxa_mecanica_omega, 3)}",
        f"  - Armadura calculada (As,cal): {formatar_fracao_decimal(flx.area_aco_calculada_cm2, 2)} cm²",
        f"  - Armadura mínima (As,min):    {formatar_fracao_decimal(flx.area_aco_minima_cm2, 2)} cm²",
        f"  - Armadura máxima (As,max):    {formatar_fracao_decimal(flx.area_aco_maxima_cm2, 2)} cm²",
        f"  - Armadura adotada (As,nec):   {formatar_fracao_decimal(flx.area_aco_adotada_cm2, 2)} cm²",
        f"  - Taxa geométrica (rho_s):     {formatar_fracao_decimal(flx.taxa_armadura_geometrica_pct, 2)}%",
        "",
        "4. DETALHAMENTO DAS ARMADURAS NORMATIVAS",
        f"  - Armadura longitudinal:       {det.quantidade_barras} Φ {formatar_fracao_decimal(det.bitola_longitudinal_mm, 1)} mm (As,ef = {formatar_fracao_decimal(det.area_aco_efetiva_cm2, 2)} cm²)",
        f"  - Espaçamento livre entre barras: {formatar_fracao_decimal(det.espacamento_livre_barras_cm, 1)} cm (Mínimo: 2,0 cm)",
        f"  - Estribos transversais:       Φ {formatar_fracao_decimal(det.bitola_estribo_mm, 1)} mm c/ {formatar_fracao_decimal(det.espacamento_estribos_cm, 1)} cm",
        f"  - Altura útil (d):             {formatar_fracao_decimal(det.altura_util_d_cm, 1)} cm",
        "",
        "5. SÍNTESE DE CONFORMIDADES NORMATIVAS",
    ]

    for k, v in resultado.conformidades.items():
        linhas.append(f"  - [{k}]:{'':<28} {'CONFORME' if v else 'NÃO CONFORME'}")

    if resultado.avisos:
        linhas.append("  OBSERVAÇÕES E NOTAS DE PROJETO:")
        for av in resultado.avisos:
            linhas.append(f"    [*] {av}")

    linhas.extend([
        "=" * 80,
        "LOFRANO TECNOLOGIA - Soluções Determinísticas e Engenharia Confiável.",
        "=" * 80,
    ])

    return "\n".join(linhas)


def exportar_csv(resultado: ResultadoProjetoPilar) -> str:
    """Gera planilha CSV com sanitização ativa de fórmulas de planilhas."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    writer.writerow([sanitizar_campo_csv("PARAMETRO"), sanitizar_campo_csv("VALOR"), sanitizar_campo_csv("UNIDADE")])
    writer.writerow([sanitizar_campo_csv("Identificacao"), sanitizar_campo_csv(resultado.identificacao), ""])
    writer.writerow([sanitizar_campo_csv("Norma"), "ABNT NBR 6118:2023", ""])
    writer.writerow([sanitizar_campo_csv("Status Geral"), "APROVADO" if resultado.atende_geral else "REPROVADO", ""])

    writer.writerow([sanitizar_campo_csv("Largura b"), formatar_fracao_decimal(resultado.geometria.largura_b_cm, 1), "cm"])
    writer.writerow([sanitizar_campo_csv("Comprimento h"), formatar_fracao_decimal(resultado.geometria.comprimento_h_cm, 1), "cm"])
    writer.writerow([sanitizar_campo_csv("Area Concreto Ac"), formatar_fracao_decimal(resultado.flexo_compressao.area_concreto_ac_cm2, 1), "cm2"])
    writer.writerow([sanitizar_campo_csv("Altura Livre l"), formatar_fracao_decimal(resultado.geometria.altura_livre_l_cm, 1), "cm"])
    writer.writerow([sanitizar_campo_csv("Comprimento Efetivo le"), formatar_fracao_decimal(resultado.esbeltez.comprimento_efetivo_le_cm, 1), "cm"])
    writer.writerow([sanitizar_campo_csv("Indice Esbeltez lambda"), formatar_fracao_decimal(resultado.esbeltez.indice_esbeltez_lambda, 1), ""])
    writer.writerow([sanitizar_campo_csv("Esbeltez Limite lambda1"), formatar_fracao_decimal(resultado.esbeltez.esbeltez_limite_lambda1, 1), ""])
    writer.writerow([sanitizar_campo_csv("Coeficiente gamma_n"), formatar_fracao_decimal(resultado.esbeltez.coeficiente_majoracao_gamman, 2), ""])

    writer.writerow([sanitizar_campo_csv("Carga Nk"), formatar_fracao_decimal(resultado.esforcos.forca_normal_nk_kn, 1), "kN"])
    writer.writerow([sanitizar_campo_csv("Carga Nsd"), formatar_fracao_decimal(resultado.excentricidades.forca_normal_calculo_nsd_kn, 1), "kN"])
    writer.writerow([sanitizar_campo_csv("Excentricidade e1"), formatar_fracao_decimal(resultado.excentricidades.excentricidade_primeira_ordem_e1_cm, 2), "cm"])
    writer.writerow([sanitizar_campo_csv("Excentricidade ea"), formatar_fracao_decimal(resultado.excentricidades.excentricidade_acidental_ea_cm, 2), "cm"])
    writer.writerow([sanitizar_campo_csv("Excentricidade e2"), formatar_fracao_decimal(resultado.excentricidades.excentricidade_segunda_ordem_e2_cm, 2), "cm"])
    writer.writerow([sanitizar_campo_csv("Excentricidade etot"), formatar_fracao_decimal(resultado.excentricidades.excentricidade_total_etot_cm, 2), "cm"])
    writer.writerow([sanitizar_campo_csv("Momento Total Msd"), formatar_fracao_decimal(resultado.excentricidades.momento_calculo_total_msd_knm, 2), "kNm"])

    writer.writerow([sanitizar_campo_csv("Area Aco Calculada"), formatar_fracao_decimal(resultado.flexo_compressao.area_aco_calculada_cm2, 2), "cm2"])
    writer.writerow([sanitizar_campo_csv("Area Aco Minima"), formatar_fracao_decimal(resultado.flexo_compressao.area_aco_minima_cm2, 2), "cm2"])
    writer.writerow([sanitizar_campo_csv("Area Aco Adotada"), formatar_fracao_decimal(resultado.flexo_compressao.area_aco_adotada_cm2, 2), "cm2"])
    writer.writerow([sanitizar_campo_csv("Barras Longitudinais"), f"{resultado.detalhamento.quantidade_barras} x {formatar_fracao_decimal(resultado.detalhamento.bitola_longitudinal_mm, 1)}mm", ""])
    writer.writerow([sanitizar_campo_csv("Area Aco Efetiva"), formatar_fracao_decimal(resultado.detalhamento.area_aco_efetiva_cm2, 2), "cm2"])
    writer.writerow([sanitizar_campo_csv("Estribos"), f"{formatar_fracao_decimal(resultado.detalhamento.bitola_estribo_mm, 1)}mm c/ {formatar_fracao_decimal(resultado.detalhamento.espacamento_estribos_cm, 1)}cm", ""])

    return output.getvalue()
