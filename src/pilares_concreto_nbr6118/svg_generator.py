"""Gerador do painel técnico vetorial SVG (1440x900) para dimensionamento de pilares.

Representação gráfica completa:
  - Seção transversal detalhada cotada (concreto, estribos e barras longitudinais)
  - Elevação do pilar com diagrama esquemático de deformação de 2ª ordem (e1, ea, e2, etot)
  - Quadro normativo consolidado de cálculo e selo de conformidade da LOFRANO TECNOLOGIA

Norma: ABNT NBR 6118:2023.
"""
from __future__ import annotations

import html
from fractions import Fraction
from typing import List

from pilares_concreto_nbr6118.exporters import formatar_fracao_decimal
from pilares_concreto_nbr6118.models import ResultadoProjetoPilar


def gerar_painel_svg(resultado: ResultadoProjetoPilar) -> str:
    """Gera um documento SVG completo de 1440x900 pixels com o painel estrutural do pilar."""
    geo = resultado.geometria
    esf = resultado.esforcos
    mat = resultado.materiais
    esb = resultado.esbeltez
    exc = resultado.excentricidades
    flx = resultado.flexo_compressao
    det = resultado.detalhamento

    b_cm = float(geo.largura_b_cm)
    h_cm = float(geo.comprimento_h_cm)
    cnom_cm = float(det.cobrimento_adotado_cm)
    qtd_barras = det.quantidade_barras

    status_cor = "#10b981" if resultado.atende_geral else "#ef4444"
    status_texto = "APROVADO" if resultado.atende_geral else "REPROVADO"

    # Escala da seção transversal (caixa de 400x380 em (70, 160))
    max_dim = max(b_cm, h_cm, 30.0)
    scale_sec = 280.0 / max_dim
    w_px = b_cm * scale_sec
    h_px = h_cm * scale_sec

    sec_cx = 280.0
    sec_cy = 340.0
    sec_x0 = sec_cx - w_px / 2.0
    sec_y0 = sec_cy - h_px / 2.0

    # Posições das barras longitudinais
    # Barras distribuídas nas faces
    c_px = cnom_cm * scale_sec
    estribo_x0 = sec_x0 + c_px
    estribo_y0 = sec_y0 + c_px
    estribo_w = w_px - 2.0 * c_px
    estribo_h = h_px - 2.0 * c_px

    # Raio da barra
    raio_barra = max(5.0, float(det.bitola_longitudinal_mm) * 0.45)

    pos_barras: List[tuple[float, float]] = []
    # Quatro cantos fundamentais
    pos_barras.append((estribo_x0 + raio_barra, estribo_y0 + raio_barra))
    pos_barras.append((estribo_x0 + estribo_w - raio_barra, estribo_y0 + raio_barra))
    pos_barras.append((estribo_x0 + raio_barra, estribo_y0 + estribo_h - raio_barra))
    pos_barras.append((estribo_x0 + estribo_w - raio_barra, estribo_y0 + estribo_h - raio_barra))

    barras_restantes = qtd_barras - 4
    if barras_restantes > 0:
        barras_por_lado = barras_restantes // 2
        passo_y = (estribo_h - 2.0 * raio_barra) / (barras_por_lado + 1)
        for i in range(1, barras_por_lado + 1):
            y_b = estribo_y0 + raio_barra + i * passo_y
            pos_barras.append((estribo_x0 + raio_barra, y_b))
            pos_barras.append((estribo_x0 + estribo_w - raio_barra, y_b))

    circulos_barras = []
    for bx, by in pos_barras:
        circulos_barras.append(
            f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{raio_barra:.1f}" fill="url(#metalAco)" stroke="#0f172a" stroke-width="1.5" />'
        )

    # Diagrama de esbeltez e deformada na coluna central (x ~ 620 a 860)
    col_x = 730.0
    col_y_topo = 180.0
    col_y_base = 500.0
    col_h = col_y_base - col_y_topo

    # Curva deformada com flecha e2
    deformada_dx = 55.0 if not esb.dispensa_segunda_ordem else 20.0
    ctrl_x = col_x + deformada_dx
    ctrl_y = (col_y_topo + col_y_base) / 2.0

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" style="background-color: #0b1120; font-family: 'Segoe UI', Inter, -apple-system, BlinkMacSystemFont, Roboto, sans-serif;">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#0369a1" />
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>
    <linearGradient id="metalAco" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="50%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#0c4a6e" />
    </linearGradient>
    <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.8" opacity="0.4" />
    </pattern>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />
    </marker>
    <marker id="arrowMagenta" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
    </marker>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.5" />
    </filter>
  </defs>

  <!-- Fundo com grid sutil -->
  <rect width="1440" height="900" fill="#0b1120" />
  <rect width="1440" height="900" fill="url(#gridPattern)" />

  <!-- Cabeçalho Principal -->
  <rect x="30" y="25" width="1380" height="85" rx="12" fill="url(#headerGrad)" filter="url(#cardShadow)" />
  <text x="60" y="60" font-size="24" font-weight="800" fill="#ffffff" letter-spacing="0.5">LOFRANO TECNOLOGIA — ENGENHARIA ESTRUTURAL DETERMINÍSTICA</text>
  <text x="60" y="88" font-size="14" font-weight="500" fill="#bae6fd">DIMENSIONAMENTO DE PILARES DE CONCRETO ARMADO — ABNT NBR 6118:2023 | MOTOR ZERO FLOAT</text>

  <rect x="1170" y="45" width="210" height="42" rx="8" fill="#0f172a" opacity="0.75" />
  <circle cx="1195" cy="66" r="9" fill="{status_cor}" />
  <text x="1215" y="72" font-size="15" font-weight="700" fill="#ffffff">{status_texto}</text>

  <!-- Painel Esquerdo: Seção Transversal Detalhada Cotada -->
  <rect x="30" y="130" width="500" height="480" rx="12" fill="url(#cardGrad)" stroke="#334155" stroke-width="1.2" filter="url(#cardShadow)" />
  <text x="55" y="165" font-size="16" font-weight="700" fill="#38bdf8">1. SEÇÃO TRANSVERSAL E ARMADURAS ({b_cm:.1f} x {h_cm:.1f} cm)</text>

  <!-- Retângulo do Concreto -->
  <rect x="{sec_x0:.1f}" y="{sec_y0:.1f}" width="{w_px:.1f}" height="{h_px:.1f}" rx="6" fill="#334155" stroke="#94a3b8" stroke-width="2.5" />

  <!-- Estribo Transversal -->
  <rect x="{estribo_x0:.1f}" y="{estribo_y0:.1f}" width="{estribo_w:.1f}" height="{estribo_h:.1f}" rx="4" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="8,2" />

  <!-- Barras Longitudinais -->
  {''.join(circulos_barras)}

  <!-- Linhas de Cota de Largura b e Altura h -->
  <line x1="{sec_x0:.1f}" y1="{sec_y0 + h_px + 25:.1f}" x2="{sec_x0 + w_px:.1f}" y2="{sec_y0 + h_px + 25:.1f}" stroke="#38bdf8" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
  <text x="{sec_cx:.1f}" y="{sec_y0 + h_px + 45:.1f}" font-size="13" font-weight="600" fill="#38bdf8" text-anchor="middle">b = {formatar_fracao_decimal(geo.largura_b_cm, 1)} cm</text>

  <line x1="{sec_x0 + w_px + 25:.1f}" y1="{sec_y0:.1f}" x2="{sec_x0 + w_px + 25:.1f}" y2="{sec_y0 + h_px:.1f}" stroke="#38bdf8" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />
  <text x="{sec_x0 + w_px + 45:.1f}" y="{sec_cy:.1f}" font-size="13" font-weight="600" fill="#38bdf8" text-anchor="start">h = {formatar_fracao_decimal(geo.comprimento_h_cm, 1)} cm</text>

  <!-- Legenda das Armaduras -->
  <text x="55" y="555" font-size="13" font-weight="500" fill="#94a3b8">Longitudinal: <tspan font-weight="700" fill="#38bdf8">{det.quantidade_barras} Φ {formatar_fracao_decimal(det.bitola_longitudinal_mm, 1)} mm (As = {formatar_fracao_decimal(det.area_aco_efetiva_cm2, 2)} cm²)</tspan></text>
  <text x="55" y="580" font-size="13" font-weight="500" fill="#94a3b8">Estribos: <tspan font-weight="700" fill="#f59e0b">Φ {formatar_fracao_decimal(det.bitola_estribo_mm, 1)} mm c/ {formatar_fracao_decimal(det.espacamento_estribos_cm, 1)} cm</tspan> | Cobrimento cnom = {formatar_fracao_decimal(det.cobrimento_adotado_cm, 1)} cm</text>

  <!-- Painel Central: Elevação e Efeitos de 2ª Ordem -->
  <rect x="550" y="130" width="370" height="480" rx="12" fill="url(#cardGrad)" stroke="#334155" stroke-width="1.2" filter="url(#cardShadow)" />
  <text x="575" y="165" font-size="16" font-weight="700" fill="#38bdf8">2. ANÁLISE DE ESBELTEZ E 2ª ORDEM</text>

  <!-- Eixo Indeformado -->
  <line x1="{col_x:.1f}" y1="{col_y_topo:.1f}" x2="{col_x:.1f}" y2="{col_y_base:.1f}" stroke="#64748b" stroke-width="2" stroke-dasharray="6,4" />

  <!-- Curva Deformada de 2ª Ordem -->
  <path d="M {col_x:.1f} {col_y_topo:.1f} Q {ctrl_x:.1f} {ctrl_y:.1f} {col_x:.1f} {col_y_base:.1f}" fill="none" stroke="#f43f5e" stroke-width="3.5" />

  <!-- Vetores de Carga e Momento -->
  <line x1="{col_x:.1f}" y1="{col_y_topo - 35:.1f}" x2="{col_x:.1f}" y2="{col_y_topo - 5:.1f}" stroke="#38bdf8" stroke-width="3" marker-end="url(#arrow)" />
  <text x="{col_x - 15:.1f}" y="{col_y_topo - 15:.1f}" font-size="13" font-weight="700" fill="#38bdf8" text-anchor="end">Nsd</text>

  <path d="M {col_x + 15:.1f} {col_y_topo - 25:.1f} A 15 15 0 0 1 {col_x + 35:.1f} {col_y_topo - 5:.1f}" fill="none" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#arrow)" />
  <text x="{col_x + 45:.1f}" y="{col_y_topo - 12:.1f}" font-size="12" font-weight="700" fill="#f59e0b">M1d</text>

  <!-- Flecha de Excentricidade etot -->
  <line x1="{col_x:.1f}" y1="{ctrl_y:.1f}" x2="{ctrl_x:.1f}" y2="{ctrl_y:.1f}" stroke="#f43f5e" stroke-width="1.8" marker-end="url(#arrowMagenta)" />
  <text x="{ctrl_x + 12:.1f}" y="{ctrl_y + 4:.1f}" font-size="12" font-weight="700" fill="#f43f5e">etot = {formatar_fracao_decimal(exc.excentricidade_total_etot_cm, 2)} cm</text>

  <text x="575" y="535" font-size="13" font-weight="500" fill="#94a3b8">Índice Esbeltez: <tspan font-weight="700" fill="#38bdf8">λ = {formatar_fracao_decimal(esb.indice_esbeltez_lambda, 1)}</tspan> (Limite: {formatar_fracao_decimal(esb.esbeltez_limite_lambda1, 1)})</text>
  <text x="575" y="560" font-size="13" font-weight="500" fill="#94a3b8">Excentricidades: <tspan font-weight="600" fill="#bae6fd">e1={formatar_fracao_decimal(exc.excentricidade_primeira_ordem_e1_cm, 2)} | ea={formatar_fracao_decimal(exc.excentricidade_acidental_ea_cm, 2)} | e2={formatar_fracao_decimal(exc.excentricidade_segunda_ordem_e2_cm, 2)} cm</tspan></text>
  <text x="575" y="585" font-size="13" font-weight="500" fill="#94a3b8">Momento Total Msd: <tspan font-weight="700" fill="#f59e0b">{formatar_fracao_decimal(exc.momento_calculo_total_msd_knm, 2)} kN·m</tspan></text>

  <!-- Painel Direito: Memória Normativa e Verificações -->
  <rect x="940" y="130" width="470" height="740" rx="12" fill="url(#cardGrad)" stroke="#334155" stroke-width="1.2" filter="url(#cardShadow)" />
  <text x="965" y="165" font-size="16" font-weight="700" fill="#38bdf8">3. SÍNTESE DO DIMENSIONAMENTO E ELU</text>

  <g transform="translate(965, 195)" font-size="13">
    <!-- Bloco 1: Geometria e Materiais -->
    <rect x="0" y="0" width="420" height="95" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="15" y="24" font-weight="700" fill="#38bdf8">PARÂMETROS GEOMÉTRICOS E MATERIAIS</text>
    <text x="15" y="46" fill="#94a3b8">Seção Bruta: <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(geo.largura_b_cm, 1)} x {formatar_fracao_decimal(geo.comprimento_h_cm, 1)} cm (Ac = {formatar_fracao_decimal(flx.area_concreto_ac_cm2, 1)} cm²)</tspan></text>
    <text x="15" y="66" fill="#94a3b8">Materiais: <tspan font-weight="600" fill="#ffffff">Concreto C{mat.classe_concreto_fck} | Aço {mat.tipo_aco}</tspan></text>
    <text x="15" y="86" fill="#94a3b8">Comprimento Efetivo le: <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(esb.comprimento_efetivo_le_cm, 1)} cm (γn = {formatar_fracao_decimal(esb.coeficiente_majoracao_gamman, 2)})</tspan></text>

    <!-- Bloco 2: Esforços e Excentricidades -->
    <rect x="0" y="110" width="420" height="115" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="15" y="134" font-weight="700" fill="#38bdf8">ESFORÇOS SOLICITANTES DE CÁLCULO</text>
    <text x="15" y="156" fill="#94a3b8">Força Normal Nk / Nsd: <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(esf.forca_normal_nk_kn, 1)} kN / {formatar_fracao_decimal(exc.forca_normal_calculo_nsd_kn, 1)} kN</tspan></text>
    <text x="15" y="176" fill="#94a3b8">Excentricidade Total etot: <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(exc.excentricidade_total_etot_cm, 2)} cm (e1+ea+e2)</tspan></text>
    <text x="15" y="196" fill="#94a3b8">Momento Total Msd,tot: <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(exc.momento_calculo_total_msd_knm, 2)} kN·m</tspan></text>
    <text x="15" y="216" fill="#94a3b8">Adimensionais: <tspan font-weight="600" fill="#ffffff">ν = {formatar_fracao_decimal(flx.forca_adimensional_nu, 3)} | μ = {formatar_fracao_decimal(flx.momento_adimensional_mu, 3)}</tspan></text>

    <!-- Bloco 3: Armaduras -->
    <rect x="0" y="240" width="420" height="115" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="15" y="264" font-weight="700" fill="#38bdf8">DIMENSIONAMENTO DAS ARMADURAS</text>
    <text x="15" y="286" fill="#94a3b8">Armadura Calculada (As,cal): <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(flx.area_aco_calculada_cm2, 2)} cm²</tspan></text>
    <text x="15" y="306" fill="#94a3b8">Armadura Mínima (As,min): <tspan font-weight="600" fill="#ffffff">{formatar_fracao_decimal(flx.area_aco_minima_cm2, 2)} cm²</tspan></text>
    <text x="15" y="326" fill="#94a3b8">Armadura Adotada Efetiva: <tspan font-weight="700" fill="#38bdf8">{det.quantidade_barras} Φ {formatar_fracao_decimal(det.bitola_longitudinal_mm, 1)} mm ({formatar_fracao_decimal(det.area_aco_efetiva_cm2, 2)} cm²)</tspan></text>
    <text x="15" y="346" fill="#94a3b8">Taxa de Armadura: <tspan font-weight="600" fill="#ffffff">ρ = {formatar_fracao_decimal(flx.taxa_armadura_geometrica_pct, 2)}% (Máx: 8,00%)</tspan></text>

    <!-- Bloco 4: Verificações Normativas -->
    <rect x="0" y="370" width="420" height="145" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1" />
    <text x="15" y="394" font-weight="700" fill="#38bdf8">VERIFICAÇÕES NORMATIVAS (NBR 6118)</text>
    <text x="15" y="416" fill="#94a3b8">Dimensões Mínimas (b≥14, Ac≥360): <tspan font-weight="700" fill="{status_cor}">{'CONFORME' if esb.atende_dimensoes_minimas else 'REPROVADO'}</tspan></text>
    <text x="15" y="438" fill="#94a3b8">Esbeltez Admissível (λ ≤ 200): <tspan font-weight="700" fill="{status_cor}">{'CONFORME' if esb.e_esbeltez_admissivel else 'REPROVADO'}</tspan></text>
    <text x="15" y="460" fill="#94a3b8">Taxa Máxima de Armadura (As ≤ As,max): <tspan font-weight="700" fill="{status_cor}">{'CONFORME' if flx.area_aco_adotada_cm2 <= flx.area_aco_maxima_cm2 else 'REPROVADO'}</tspan></text>
    <text x="15" y="482" fill="#94a3b8">Espaçamento Livre Barras (≥ 2,0 cm): <tspan font-weight="700" fill="{status_cor}">{'CONFORME' if det.espacamento_livre_barras_cm >= Fraction(2, 1) else 'REPROVADO'}</tspan></text>
    <text x="15" y="504" fill="#94a3b8">Efeitos de 2ª Ordem: <tspan font-weight="600" fill="#bae6fd">{'Dispensados' if esb.dispensa_segunda_ordem else 'Considerados (Pilar-Padrão)'}</tspan></text>
  </g>

  <!-- Painel Inferior: Identificação e Notas -->
  <rect x="30" y="630" width="890" height="240" rx="12" fill="url(#cardGrad)" stroke="#334155" stroke-width="1.2" filter="url(#cardShadow)" />
  <text x="55" y="665" font-size="16" font-weight="700" fill="#38bdf8">4. DADOS DO PROJETO E OBSERVAÇÕES EXECUTIVAS</text>
  <text x="55" y="695" font-size="14" font-weight="600" fill="#ffffff">Identificação: {html.escape(resultado.identificacao)}</text>
  <text x="55" y="720" font-size="13" font-weight="400" fill="#94a3b8">• Aritmética 100% Exata: Nenhum ponto flutuante foi utilizado no motor (Zero Float). Todos os cálculos utilizam frações exatas.</text>
  <text x="55" y="742" font-size="13" font-weight="400" fill="#94a3b8">• Efeitos de 2ª Ordem: Avaliados segundo a NBR 6118 item 15.8.3 com curvatura aproximada 1/r e excentricidade acidental ea.</text>
  <text x="55" y="764" font-size="13" font-weight="400" fill="#94a3b8">• Detalhamento Construtivo: Estribos com ganchos padronizados de 135° e cobrimento nominal garantido segundo a CAA {mat.classe_agressividade}.</text>

  <!-- Rodapé de Autoria -->
  <line x1="55" y1="790" x2="895" y2="790" stroke="#334155" stroke-width="1" />
  <text x="55" y="818" font-size="13" font-weight="600" fill="#bae6fd">LOFRANO TECNOLOGIA — Engenharia de Software e Confiabilidade Estrutural</text>
  <text x="55" y="840" font-size="12" font-weight="400" fill="#64748b">Biblioteca Aberta e Determinística | Licença MIT | https://github.com/martinlofranodeoliveira</text>
</svg>
"""
    return svg
