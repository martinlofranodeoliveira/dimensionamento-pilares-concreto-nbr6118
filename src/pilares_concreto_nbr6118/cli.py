"""Interface de linha de comando (CLI) para dimensionamento de pilares de concreto armado.

ABNT NBR 6118:2023 - LOFRANO TECNOLOGIA.
Aritmética 100% exata (Zero Float) com Frações.
"""
from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from typing import List, Optional

from pilares_concreto_nbr6118 import __version__
from pilares_concreto_nbr6118.constants import (
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
)
from pilares_concreto_nbr6118.calculator import dimensionar_pilar_concreto
from pilares_concreto_nbr6118.codecs import (
    carregar_json_canonico,
    salvar_json_canonico,
    deserializar_projeto,
)
from pilares_concreto_nbr6118.exporters import (
    gerar_relatorio_memorial,
    exportar_csv,
    formatar_fracao_decimal,
)
from pilares_concreto_nbr6118.svg_generator import gerar_painel_svg


def parse_fracao_cli(valor: str) -> Fraction:
    """Converte argumentos da CLI em Fraction sem passar por float."""
    s = valor.strip().replace(",", ".")
    if "/" in s:
        p = s.split("/")
        return Fraction(int(p[0]), int(p[1]))
    if "." in s:
        partes = s.split(".")
        inteiro = int(partes[0]) if partes[0] else 0
        dec = partes[1]
        den = 10 ** len(dec)
        num = abs(inteiro) * den + int(dec)
        if s.startswith("-"):
            num = -num
        return Fraction(num, den)
    return Fraction(int(s), 1)


def comando_tabelas() -> int:
    """Exibe as tabelas normativas de agressividade, cobrimentos e armaduras de pilares."""
    print("=" * 80)
    print("TABELAS NORMATIVAS — PILARES DE CONCRETO ARMADO (ABNT NBR 6118:2023)")
    print("=" * 80)
    print("\nCLASSES DE AGRESSIVIDADE AMBIENTAL E COBRIMENTOS NOMINAIS (PILARES):")
    print("-" * 80)
    print(f"{'Classe':<10} | {'Agressividade':<30} | {'Cobrimento':<15} | {'w_lim (Fissura)'}")
    print("-" * 80)
    for caa, info in TABELA_CAA_PILARES.items():
        cnom_str = formatar_fracao_decimal(info["cobrimento_nominal_cm"], 1)
        wlim_str = formatar_fracao_decimal(info["w_lim_mm"], 2)
        print(f"{caa:<10} | {info['agressividade']:<30} | {cnom_str} cm{'':<9} | {wlim_str} mm")
    print("=" * 80)
    return 0


def comando_materiais() -> int:
    """Lista as classes de concreto, aços e bitolas comerciais cadastrados."""
    print("=" * 80)
    print("CATÁLOGO DE MATERIAIS ESTRUTURAIS E BITOLAS COMERCIAIS PARA PILARES")
    print("=" * 80)
    print("\n1. CONCRETOS ESTRUTURAIS DO GRUPO I (NBR 6118)")
    print("-" * 60)
    for fck, info in TABELA_CONCRETOS_NBR6118.items():
        fcd_str = formatar_fracao_decimal(info["fcd_kN_cm2"], 2)
        print(f"Classe C{fck} | fck = {fck} MPa | fcd = {fcd_str} kN/cm²")

    print("\n2. AÇOS ESTRUTURAIS")
    print("-" * 60)
    for k, info in TABELA_ACOS_NBR6118.items():
        fyd_str = formatar_fracao_decimal(info["fyd_kN_cm2"], 2)
        print(f"{k:<10} | {info['nome']:<30} | fyd = {fyd_str} kN/cm²")

    print("\n3. BITOLAS PADRONIZADAS LONGITUDINAIS (Φ >= 10 mm)")
    print("-" * 60)
    for k, info in TABELA_BITOLAS_LONGITUDINAIS.items():
        d_str = formatar_fracao_decimal(info["diametro_mm"], 1)
        a_str = formatar_fracao_decimal(info["area_cm2"], 3)
        print(f"Φ {d_str} mm{'':<12} | {a_str} cm²")

    print("\n4. BITOLAS PADRONIZADAS PARA ESTRIBOS TRANSVERSAIS")
    print("-" * 60)
    for k, info in TABELA_BITOLAS_ESTRIBOS.items():
        d_str = formatar_fracao_decimal(info["diametro_mm"], 1)
        a_str = formatar_fracao_decimal(info["area_cm2"], 3)
        print(f"Φ {d_str} mm{'':<12} | {a_str} cm²")
    print("=" * 80)
    return 0


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser com os argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="pilares-concreto",
        description="Dimensionamento analítico e verificação de pilares de concreto armado segundo ABNT NBR 6118:2023. LOFRANO TECNOLOGIA.",
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Subcomando dimensionar
    p_dim = subparsers.add_parser("dimensionar", help="Dimensiona o pilar e verifica esbeltez e flexo-compressão")
    p_dim.add_argument("-a", "--arquivo", type=str, help="Caminho do arquivo JSON de entrada do projeto")
    p_dim.add_argument("--b", type=str, help="Largura da seção transversal b em cm (ex: 20)")
    p_dim.add_argument("--h", type=str, help="Comprimento da seção transversal h em cm (ex: 40)")
    p_dim.add_argument("--l", type=str, help="Altura livre do pilar l em cm (ex: 300)")
    p_dim.add_argument("--alpha", type=str, default="1.0", help="Coeficiente de flambagem alpha (padrão: 1.0)")
    p_dim.add_argument("--nk", type=str, help="Força normal característica Nk em kN (ex: 600)")
    p_dim.add_argument("--mk-topo", type=str, default="0", help="Momento fletor característico de topo em kN·m")
    p_dim.add_argument("--mk-base", type=str, default="0", help="Momento fletor característico de base em kN·m")
    p_dim.add_argument("--eixo", type=str, default="h", choices=["h", "b"], help="Eixo de flexão ('h' ou 'b')")
    p_dim.add_argument("--fck", type=int, default=25, help="Resistência característica do concreto em MPa (padrão: 25)")
    p_dim.add_argument("--aco", type=str, default="CA_50", choices=["CA_50", "CA_60"], help="Tipo de aço (padrão: CA_50)")
    p_dim.add_argument("--caa", type=str, default="CAA_II", choices=["CAA_I", "CAA_II", "CAA_III", "CAA_IV"], help="Classe de agressividade ambiental")
    p_dim.add_argument("--identificacao", type=str, default="Pilar Dimensionado", help="Identificação do pilar")

    p_dim.add_argument("--relatorio", type=str, help="Caminho para salvar o memorial descritivo em texto")
    p_dim.add_argument("--json-saida", type=str, help="Caminho para salvar o resultado em JSON canônico")
    p_dim.add_argument("--csv", type=str, dest="saida_csv", help="Caminho para exportar planilha CSV sanitizada")
    p_dim.add_argument("--svg", type=str, dest="painel_svg", help="Caminho para gerar o painel técnico vetorial SVG")

    # Subcomandos informativos
    subparsers.add_parser("tabelas", help="Exibe as tabelas normativas de agressividade e cobrimentos")
    subparsers.add_parser("materiais", help="Lista as classes de concreto, aços e bitolas comerciais")
    subparsers.add_parser("versao", help="Exibe a versão do pacote")

    return parser


def executar_dimensionamento_cli(args: argparse.Namespace) -> int:
    """Processa a solicitação de dimensionamento a partir dos argumentos da CLI."""
    if args.arquivo:
        dados = carregar_json_canonico(args.arquivo)
        projeto = deserializar_projeto(dados)
    else:
        if not args.nk or not args.b or not args.h or not args.l:
            print("Erro: Forneça um arquivo JSON (--arquivo) ou informe as dimensões (--b, --h, --l) e a carga normal (--nk).", file=sys.stderr)
            return 1

        geo = GeometriaPilar(
            largura_b_cm=parse_fracao_cli(args.b),
            comprimento_h_cm=parse_fracao_cli(args.h),
            altura_livre_l_cm=parse_fracao_cli(args.l),
            coeficiente_flambagem_alpha=parse_fracao_cli(args.alpha),
        )
        esf = EsforcosPilar(
            forca_normal_nk_kn=parse_fracao_cli(args.nk),
            momento_topo_mk_topo_knm=parse_fracao_cli(args.mk_topo),
            momento_base_mk_base_knm=parse_fracao_cli(args.mk_base),
            eixo_flexao=args.eixo,
        )
        mat = PropriedadesMateriais(
            classe_concreto_fck=args.fck,
            tipo_aco=args.aco,
            classe_agressividade=args.caa,
        )
        projeto = ProjetoPilar(
            geometria=geo,
            esforcos=esf,
            materiais=mat,
            identificacao=args.identificacao,
        )

    resultado = dimensionar_pilar_concreto(projeto)
    relatorio = gerar_relatorio_memorial(resultado)
    print(relatorio)

    if args.relatorio:
        with open(args.relatorio, "w", encoding="utf-8") as f:
            f.write(relatorio)
            f.write("\n")
        print(f"Memorial descritivo salvo em: {args.relatorio}")

    if args.json_saida:
        salvar_json_canonico(args.json_saida, resultado)
        print(f"Resultado JSON canônico salvo em: {args.json_saida}")

    if args.saida_csv:
        csv_texto = exportar_csv(resultado)
        with open(args.saida_csv, "w", encoding="utf-8") as f:
            f.write(csv_texto)
        print(f"Planilha CSV salva em: {args.saida_csv}")

    if args.painel_svg:
        svg_conteudo = gerar_painel_svg(resultado)
        with open(args.painel_svg, "w", encoding="utf-8") as f:
            f.write(svg_conteudo)
        print(f"Painel técnico SVG salvo em: {args.painel_svg}")

    return 0 if resultado.atende_geral else 1


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass

    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.comando == "tabelas":
        return comando_tabelas()
    elif args.comando == "materiais":
        return comando_materiais()
    elif args.comando == "versao":
        print(f"pilares-concreto v{__version__} — ABNT NBR 6118:2023 (LOFRANO TECNOLOGIA)")
        return 0
    elif args.comando == "dimensionar":
        return executar_dimensionamento_cli(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
