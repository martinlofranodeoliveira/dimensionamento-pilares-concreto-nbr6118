"""Motor analítico de cálculo e dimensionamento de pilares de concreto armado.

Implementa as formulações da ABNT NBR 6118:2023:
  - Verificação de dimensões mínimas e coeficiente gamma_n (Item 13.2.3)
  - Análise de esbeltez global e local (Item 15.8)
  - Imperfeições geométricas locais e momentos de 1ª ordem (Item 11.3 e 15.8.2)
  - Efeitos locais de 2ª ordem via Método do Pilar-Padrão com Curvatura Aproximada (Item 15.8.3.3.2)
  - Flexo-compressão normal com armadura simétrica (Item 17.2 e 17.3)
  - Detalhamento de armaduras longitudinais e estribos (Item 18.4)

LOFRANO TECNOLOGIA - Aritmética 100% exata (Zero Float) com Frações e inteiros.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from pilares_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    LARGURA_MINIMA_PILAR_CM,
    AREA_MINIMA_SECAO_CM2,
    ESBELTEZ_MAXIMA_ADMISSIVEL,
    ESBELTEZ_LIMITE_METODO_PILAR_PADRAO,
    RHO_MIN_PILAR_AC,
    RHO_MIN_PILAR_NSD,
    RHO_MAX_PILAR_EMENDA,
    RHO_MAX_PILAR_NORMAL,
    DIAMETRO_MINIMO_LONGITUDINAL_MM,
    NUMERO_MINIMO_BARRAS_RETANGULAR,
    DIAMETRO_MINIMO_ESTRIBO_MM,
    ESPACAMENTO_MAXIMO_ESTRIBOS_ABSOLUTO_CM,
    ESPACAMENTO_MAXIMO_LONGITUDINAL_EIXOS_CM,
    ESPACAMENTO_LIVRE_MINIMO_LONGITUDINAL_CM,
    TABELA_CAA_PILARES,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_LONGITUDINAIS,
    TABELA_BITOLAS_ESTRIBOS,
)
from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoPilar,
    ResultadoEsbeltezPilar,
    ResultadoExcentricidadesPilar,
    ResultadoFlexoCompressaoPilar,
    ResultadoDetalhamentoPilar,
    ResultadoProjetoPilar,
)


def raiz_quadrada_fracao(frac: Fraction, precisao: int = 12) -> Fraction:
    """Calcula a aproximação racional exata de raiz quadrada de uma fração sem usar float."""
    if frac < 0:
        raise ValueError("Não é possível calcular raiz quadrada de fração negativa.")
    if frac == 0:
        return Fraction(0, 1)

    p = frac.numerator
    q = frac.denominator
    fator_escala = 10 ** (2 * precisao)
    radicando_inteiro = p * q * fator_escala
    raiz_int = math.isqrt(radicando_inteiro)
    denominador = q * (10 ** precisao)
    return Fraction(raiz_int, denominador)


def obter_cobrimento_nominal(materiais: PropriedadesMateriais) -> Fraction:
    """Determina o cobrimento nominal do pilar em cm."""
    if materiais.cobrimento_nominal_cm is not None:
        return materiais.cobrimento_nominal_cm
    info = TABELA_CAA_PILARES.get(materiais.classe_agressividade, TABELA_CAA_PILARES["CAA_II"])
    return info["cobrimento_nominal_cm"]


def calcular_coeficiente_gamman(menor_dimensao_cm: Fraction) -> Fraction:
    """Calcula o coeficiente adicional de majoração gamma_n (NBR 6118 item 13.2.3)."""
    if menor_dimensao_cm >= Fraction(19, 1):
        return Fraction(1, 1)
    if menor_dimensao_cm < LARGURA_MINIMA_PILAR_CM:
        # Abaixo de 14 cm é vedado pela norma, mas calcula valor proporcional
        return Fraction(195, 100) - Fraction(5, 100) * menor_dimensao_cm
    # Para 14 <= b < 19 cm: gamma_n = 1.95 - 0.05 * b
    return Fraction(195, 100) - Fraction(5, 100) * menor_dimensao_cm


def calcular_esbeltez_pilar(
    geometria: GeometriaPilar,
    esforcos: EsforcosPilar,
) -> ResultadoEsbeltezPilar:
    """Calcula o comprimento efetivo, raio de giração e índice de esbeltez lambda."""
    b = geometria.largura_b_cm
    h = geometria.comprimento_h_cm
    le = geometria.altura_livre_l_cm * geometria.coeficiente_flambagem_alpha

    # Dimensão na direção de flambagem / flexão
    dim_flexao = h if esforcos.eixo_flexao == "h" else b
    menor_dim = min(b, h)

    # Raio de giração i = h / sqrt(12) => i^2 = h^2 / 12
    # lambda = le / i = le * sqrt(12) / h => lambda^2 = 12 * le^2 / h^2
    lambda_sq = Fraction(12, 1) * (le ** 2) / (dim_flexao ** 2)
    lambda_val = raiz_quadrada_fracao(lambda_sq)

    i_sq = (dim_flexao ** 2) / Fraction(12, 1)
    i_val = raiz_quadrada_fracao(i_sq)

    # Coeficiente gamma_n
    gamman = calcular_coeficiente_gamman(menor_dim)

    # Verificação de dimensões mínimas (NBR 6118 item 13.2.3)
    ac = b * h
    atende_dim = (menor_dim >= LARGURA_MINIMA_PILAR_CM) and (ac >= AREA_MINIMA_SECAO_CM2)
    atende_esbeltez = lambda_val <= ESBELTEZ_MAXIMA_ADMISSIVEL

    # Esbeltez limite lambda1 preliminar (será refinada com e1 em calcular_excentricidades)
    lambda1_padrao = Fraction(35, 1)
    dispensa_2a_ordem = lambda_val <= lambda1_padrao

    return ResultadoEsbeltezPilar(
        comprimento_efetivo_le_cm=le,
        raio_giracao_i_cm=i_val,
        indice_esbeltez_lambda=lambda_val,
        coeficiente_majoracao_gamman=gamman,
        esbeltez_limite_lambda1=lambda1_padrao,
        dispensa_segunda_ordem=dispensa_2a_ordem,
        e_esbeltez_admissivel=atende_esbeltez,
        atende_dimensoes_minimas=atende_dim,
    )


def calcular_excentricidades_pilar(
    geometria: GeometriaPilar,
    esforcos: EsforcosPilar,
    materiais: PropriedadesMateriais,
    esbeltez: ResultadoEsbeltezPilar,
) -> Tuple[ResultadoExcentricidadesPilar, ResultadoEsbeltezPilar]:
    """Determina as excentricidades de 1ª ordem, acidental e de 2ª ordem local."""
    gamman = esbeltez.coeficiente_majoracao_gamman
    nk = esforcos.forca_normal_nk_kn
    nsd = nk * GAMMA_F * gamman  # kN

    b = geometria.largura_b_cm
    h = geometria.comprimento_h_cm
    dim_flexao = h if esforcos.eixo_flexao == "h" else b
    le = esbeltez.comprimento_efetivo_le_cm

    # Momentos de 1ª ordem de cálculo nas extremidades (topo e base) em kN·cm
    mk_topo = abs(esforcos.momento_topo_mk_topo_knm)
    mk_base = abs(esforcos.momento_base_mk_base_knm)
    m1d_topo_kNcm = mk_topo * Fraction(100, 1) * GAMMA_F * gamman
    m1d_base_kNcm = mk_base * Fraction(100, 1) * GAMMA_F * gamman

    m1d_max_kNcm = max(m1d_topo_kNcm, m1d_base_kNcm)
    m1d_min_kNcm = min(m1d_topo_kNcm, m1d_base_kNcm)

    # Excentricidade primária de 1ª ordem
    e1_bruta = m1d_max_kNcm / nsd if nsd > 0 else Fraction(0, 1)

    # Fator alpha_b para momento equivalente (NBR 6118 item 15.8.2)
    if m1d_max_kNcm > 0:
        alpha_b = Fraction(60, 100) + Fraction(40, 100) * (m1d_min_kNcm / m1d_max_kNcm)
        alpha_b = max(alpha_b, Fraction(40, 100))
    else:
        alpha_b = Fraction(1, 1)

    e1_equiv = max(alpha_b * e1_bruta, Fraction(40, 100) * e1_bruta)

    # Excentricidade acidental / imperfeição local (NBR 6118 item 11.3.3.4.1):
    # ea = max(le / 400, h / 30, 1,5 cm)
    ea_1 = le / Fraction(400, 1)
    ea_2 = dim_flexao / Fraction(30, 1)
    ea_3 = Fraction(15, 10)  # 1,5 cm
    ea = max(ea_1, ea_2, ea_3)

    e1_tot = e1_equiv + ea

    # Esbeltez limite lambda1 (NBR 6118 item 15.8.2):
    # lambda1 = (25 + 12.5 * (e1 / h)) / alpha_b, com 35 <= lambda1 <= 90
    termo_e1_h = (e1_bruta / dim_flexao) * Fraction(125, 10)
    lambda1_calc = (Fraction(25, 1) + termo_e1_h) / alpha_b
    lambda1 = max(Fraction(35, 1), min(Fraction(90, 1), lambda1_calc))

    dispensa_2a_ordem = esbeltez.indice_esbeltez_lambda <= lambda1

    # Cálculo da excentricidade de 2ª ordem local e2
    # Método do Pilar-Padrão com Curvatura Aproximada (NBR 6118 item 15.8.3.3.2)
    fck = materiais.classe_concreto_fck
    info_conc = TABELA_CONCRETOS_NBR6118[fck]
    fcd_kN_cm2 = info_conc["fcd_kN_cm2"]
    ac_cm2 = b * h

    nu = nsd / (ac_cm2 * fcd_kN_cm2)  # Força normal adimensional

    if dispensa_2a_ordem:
        e2 = Fraction(0, 1)
        um_sobre_r = Fraction(0, 1)
    else:
        # 1/r = 0,005 / (h * (nu + 0,5)) <= 0,005 / h
        den_r = dim_flexao * (nu + Fraction(1, 2))
        um_sobre_r_calc = Fraction(5, 1000) / den_r
        um_sobre_r_max = Fraction(5, 1000) / dim_flexao
        um_sobre_r = min(um_sobre_r_calc, um_sobre_r_max)

        # e2 = (le^2 / 10) * (1/r)
        e2 = ((le ** 2) / Fraction(10, 1)) * um_sobre_r

    # Excentricidade total e momento final de cálculo
    etot = e1_tot + e2
    msd_tot_kNcm = nsd * etot
    msd_tot_kNm = msd_tot_kNcm / Fraction(100, 1)

    res_excentricidades = ResultadoExcentricidadesPilar(
        forca_normal_calculo_nsd_kn=nsd,
        excentricidade_primeira_ordem_e1_cm=e1_bruta,
        excentricidade_acidental_ea_cm=ea,
        excentricidade_segunda_ordem_e2_cm=e2,
        excentricidade_total_etot_cm=etot,
        momento_calculo_total_msd_knm=msd_tot_kNm,
        curvatura_aproximada_1_r=um_sobre_r,
    )

    res_esbeltez_atualizada = ResultadoEsbeltezPilar(
        comprimento_efetivo_le_cm=esbeltez.comprimento_efetivo_le_cm,
        raio_giracao_i_cm=esbeltez.raio_giracao_i_cm,
        indice_esbeltez_lambda=esbeltez.indice_esbeltez_lambda,
        coeficiente_majoracao_gamman=esbeltez.coeficiente_majoracao_gamman,
        esbeltez_limite_lambda1=lambda1,
        dispensa_segunda_ordem=dispensa_2a_ordem,
        e_esbeltez_admissivel=esbeltez.e_esbeltez_admissivel,
        atende_dimensoes_minimas=esbeltez.atende_dimensoes_minimas,
    )

    return res_excentricidades, res_esbeltez_atualizada


def dimensionar_flexo_compressao_pilar(
    geometria: GeometriaPilar,
    esforcos: EsforcosPilar,
    materiais: PropriedadesMateriais,
    excentricidades: ResultadoExcentricidadesPilar,
) -> ResultadoFlexoCompressaoPilar:
    """Dimensiona as armaduras longitudinais sob flexo-compressão normal com armadura simétrica."""
    b = geometria.largura_b_cm
    h = geometria.comprimento_h_cm
    dim_flexao = h if esforcos.eixo_flexao == "h" else b
    dim_largura = b if esforcos.eixo_flexao == "h" else h

    cnom = obter_cobrimento_nominal(materiais)
    # Estimativa de centroide da armadura d': cnom + estribo (0,5 cm) + phi_l/2 (0,8 cm) ~ cnom + 1,3 cm
    d_linha = cnom + Fraction(13, 10)
    d_util = dim_flexao - d_linha
    delta = d_linha / dim_flexao

    fck = materiais.classe_concreto_fck
    info_conc = TABELA_CONCRETOS_NBR6118[fck]
    fcd_kN_cm2 = info_conc["fcd_kN_cm2"]

    aco_info = TABELA_ACOS_NBR6118[materiais.tipo_aco]
    fyd_kN_cm2 = aco_info["fyd_kN_cm2"]

    ac_cm2 = b * h
    nsd = excentricidades.forca_normal_calculo_nsd_kn
    msd_kNcm = excentricidades.momento_calculo_total_msd_knm * Fraction(100, 1)

    # Parâmetros adimensionais de força normal nu e momento mu
    nu = nsd / (ac_cm2 * fcd_kN_cm2)
    mu = msd_kNcm / (dim_largura * (dim_flexao ** 2) * fcd_kN_cm2)

    # Taxa mecânica de armadura omega = (As * fyd) / (Ac * fcd)
    # Formulação analítica fechada e robusta de flexo-compressão com armadura simétrica:
    # O momento resistente da armadura de tração/compressão com braço de alavanca (1 - 2*delta):
    # m_s = omega * (1 - 2*delta) / 2
    # Parcela de momento absorvida pelo concreto:
    # m_c ~ nu * (1 - nu) / 2 para nu <= 0.80, e decrescente para nu > 0.80.
    braço_aco = Fraction(1, 1) - Fraction(2, 1) * delta
    if braço_aco <= 0:
        braço_aco = Fraction(70, 100)

    if nu <= Fraction(80, 100):
        mu_c = (nu * (Fraction(1, 1) - nu)) / Fraction(2, 1)
    else:
        mu_c = Fraction(16, 100) * (Fraction(1, 1) - (nu - Fraction(80, 100)))
        mu_c = max(Fraction(0, 1), mu_c)

    delta_mu = mu - mu_c
    if delta_mu > 0:
        omega_calc = delta_mu / (braço_aco / Fraction(2, 1))
    else:
        # Se a compressão absorve o momento, armadura calculada por compressão pura ou mínima
        if nu > Fraction(1, 1):
            omega_calc = nu - Fraction(1, 1)
        else:
            omega_calc = Fraction(0, 1)

    # Área de aço calculada em cm²
    as_calc_cm2 = omega_calc * (ac_cm2 * fcd_kN_cm2) / fyd_kN_cm2

    # Armadura mínima (NBR 6118 item 17.3.5.3):
    # As,min >= 0,15% * Nsd / fyd
    # As,min >= 0,40% * Ac
    as_min_1 = RHO_MIN_PILAR_NSD * (nsd / fyd_kN_cm2)
    as_min_2 = RHO_MIN_PILAR_AC * ac_cm2
    as_min_cm2 = max(as_min_1, as_min_2)

    # Armadura máxima (NBR 6118 item 17.3.5.3):
    as_max_cm2 = RHO_MAX_PILAR_EMENDA * ac_cm2

    as_adotado_cm2 = max(as_calc_cm2, as_min_cm2)
    taxa_geom_pct = (as_adotado_cm2 / ac_cm2) * Fraction(100, 1)

    return ResultadoFlexoCompressaoPilar(
        area_concreto_ac_cm2=ac_cm2,
        forca_adimensional_nu=nu,
        momento_adimensional_mu=mu,
        taxa_mecanica_omega=omega_calc,
        area_aco_calculada_cm2=as_calc_cm2,
        area_aco_minima_cm2=as_min_cm2,
        area_aco_maxima_cm2=as_max_cm2,
        area_aco_adotada_cm2=as_adotado_cm2,
        taxa_armadura_geometrica_pct=taxa_geom_pct,
    )


def detalhar_armaduras_pilar(
    geometria: GeometriaPilar,
    esforcos: EsforcosPilar,
    materiais: PropriedadesMateriais,
    flexo_comp: ResultadoFlexoCompressaoPilar,
    pref: PreferenciasDetalhamento,
) -> ResultadoDetalhamentoPilar:
    """Seleciona bitolas, quantidade de barras e estribos para o pilar."""
    as_nec = flexo_comp.area_aco_adotada_cm2
    cnom = obter_cobrimento_nominal(materiais)

    # Bitola longitudinal sugerida ou automática
    bitolas_candidatas = ["10.0", "12.5", "16.0", "20.0", "25.0"]
    if pref.bitola_longitudinal_sugerida_mm is not None:
        bit_sug_str = f"{float(pref.bitola_longitudinal_sugerida_mm):.1f}"
        if bit_sug_str in TABELA_BITOLAS_LONGITUDINAIS:
            bitolas_candidatas = [bit_sug_str] + [b for b in bitolas_candidatas if b != bit_sug_str]

    melhor_phi_mm = Fraction(10, 1)
    melhor_qtd = 4
    melhor_as_ef = Fraction(0, 1)
    encontrou = False

    for bit_str in bitolas_candidatas:
        info_bit = TABELA_BITOLAS_LONGITUDINAIS[bit_str]
        area_barra = info_bit["area_cm2"]
        phi_mm = info_bit["diametro_mm"]

        # Quantidade mínima de 4 barras (número par)
        qtd = 4
        while qtd * area_barra < as_nec:
            qtd += 2

        as_ef = qtd * area_barra
        # Verificar se não ultrapassa As,max
        if as_ef <= flexo_comp.area_aco_maxima_cm2:
            melhor_phi_mm = phi_mm
            melhor_qtd = qtd
            melhor_as_ef = as_ef
            encontrou = True
            break

    if not encontrou:
        # Fallback para maior bitola
        info_bit = TABELA_BITOLAS_LONGITUDINAIS["25.0"]
        melhor_phi_mm = info_bit["diametro_mm"]
        qtd = 4
        while qtd * info_bit["area_cm2"] < as_nec:
            qtd += 2
        melhor_qtd = qtd
        melhor_as_ef = melhor_qtd * info_bit["area_cm2"]

    # Detalhamento dos estribos transversais
    # phi_t >= max(5 mm, phi_l / 4)
    phi_t_min = max(DIAMETRO_MINIMO_ESTRIBO_MM, melhor_phi_mm / Fraction(4, 1))
    bitolas_estribo = ["5.0", "6.3", "8.0", "10.0"]
    phi_estribo_mm = Fraction(5, 1)
    for be_str in bitolas_estribo:
        info_be = TABELA_BITOLAS_ESTRIBOS[be_str]
        if info_be["diametro_mm"] >= phi_t_min:
            phi_estribo_mm = info_be["diametro_mm"]
            break

    # Espaçamento máximo dos estribos (NBR 6118 item 18.4.3):
    # s_max <= min(20 cm, menor_dimensao_pilar, 12 * phi_l_min)
    menor_dim = min(geometria.largura_b_cm, geometria.comprimento_h_cm)
    s_max_1 = ESPACAMENTO_MAXIMO_ESTRIBOS_ABSOLUTO_CM  # 20 cm
    s_max_2 = menor_dim
    s_max_3 = Fraction(12, 1) * (melhor_phi_mm / Fraction(10, 1))
    s_max = min(s_max_1, s_max_2, s_max_3)
    # Arredondar para inteiro inferior em cm
    s_adotado = Fraction(max(5, int(s_max)), 1)

    # Espaçamento livre entre barras na face mais solicitada
    phi_l_cm = melhor_phi_mm / Fraction(10, 1)
    phi_t_cm = phi_estribo_mm / Fraction(10, 1)
    d_util = (geometria.comprimento_h_cm if esforcos.eixo_flexao == "h" else geometria.largura_b_cm) - cnom - phi_t_cm - (phi_l_cm / Fraction(2, 1))

    # Número de barras por face
    barras_por_face = melhor_qtd // 2
    if barras_por_face > 1:
        dim_face = geometria.comprimento_h_cm if esforcos.eixo_flexao == "h" else geometria.largura_b_cm
        esp_livre = (dim_face - Fraction(2, 1) * cnom - Fraction(2, 1) * phi_t_cm - Fraction(barras_por_face, 1) * phi_l_cm) / Fraction(barras_por_face - 1, 1)
    else:
        esp_livre = Fraction(10, 1)

    return ResultadoDetalhamentoPilar(
        bitola_longitudinal_mm=melhor_phi_mm,
        quantidade_barras=melhor_qtd,
        area_aco_efetiva_cm2=melhor_as_ef,
        espacamento_livre_barras_cm=esp_livre,
        bitola_estribo_mm=phi_estribo_mm,
        espacamento_estribos_cm=s_adotado,
        cobrimento_adotado_cm=cnom,
        altura_util_d_cm=d_util,
    )


def dimensionar_pilar_concreto(projeto: ProjetoPilar) -> ResultadoProjetoPilar:
    """Executa o fluxo normativo integral de dimensionamento e verificação do pilar."""
    esbeltez = calcular_esbeltez_pilar(projeto.geometria, projeto.esforcos)
    excentricidades, esbeltez_refinada = calcular_excentricidades_pilar(
        projeto.geometria,
        projeto.esforcos,
        projeto.materiais,
        esbeltez,
    )
    flexo_comp = dimensionar_flexo_compressao_pilar(
        projeto.geometria,
        projeto.esforcos,
        projeto.materiais,
        excentricidades,
    )
    detalhamento = detalhar_armaduras_pilar(
        projeto.geometria,
        projeto.esforcos,
        projeto.materiais,
        flexo_comp,
        projeto.detalhamento,
    )

    # Verificações de conformidade
    conf_dim = esbeltez_refinada.atende_dimensoes_minimas
    conf_esbeltez = esbeltez_refinada.e_esbeltez_admissivel
    conf_arm_max = flexo_comp.area_aco_adotada_cm2 <= flexo_comp.area_aco_maxima_cm2
    conf_esp_livre = detalhamento.espacamento_livre_barras_cm >= ESPACAMENTO_LIVRE_MINIMO_LONGITUDINAL_CM

    conformidades = {
        "dimensoes_minimas": conf_dim,
        "esbeltez_admissivel": conf_esbeltez,
        "taxa_armadura_maxima": conf_arm_max,
        "espacamento_livre_barras": conf_esp_livre,
    }

    atende_geral = all(conformidades.values())

    avisos = []
    if not conf_dim:
        avisos.append("Pilar não atende às dimensões mínimas normativas (b >= 14 cm e Ac >= 360 cm²).")
    if not conf_esbeltez:
        avisos.append(f"Índice de esbeltez ({float(esbeltez_refinada.indice_esbeltez_lambda):.1f}) excede o limite normativo de 200.")
    if not esbeltez_refinada.dispensa_segunda_ordem:
        avisos.append("Efeitos locais de 2ª ordem calculados pelo Método do Pilar-Padrão com Curvatura Aproximada.")
    if esbeltez_refinada.coeficiente_majoracao_gamman > Fraction(1, 1):
        avisos.append(f"Aplicado coeficiente de majoração adicional gamma_n = {float(esbeltez_refinada.coeficiente_majoracao_gamman):.2f} por espessura < 19 cm.")

    return ResultadoProjetoPilar(
        identificacao=projeto.identificacao,
        geometria=projeto.geometria,
        esforcos=projeto.esforcos,
        materiais=projeto.materiais,
        esbeltez=esbeltez_refinada,
        excentricidades=excentricidades,
        flexo_compressao=flexo_comp,
        detalhamento=detalhamento,
        atende_geral=atende_geral,
        conformidades=conformidades,
        avisos=avisos,
    )
