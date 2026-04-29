from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MopacMethodInfo:
    keyword: str
    title_en: str
    title_pt: str
    description_en: str
    description_pt: str


COMMON_MOPAC_METHODS: tuple[MopacMethodInfo, ...] = (
    MopacMethodInfo(
        keyword="PM7",
        title_en="Default general-purpose method.",
        title_pt="Metodo geral padrao.",
        description_en="Recommended starting point for most organic, medicinal chemistry, and mixed-element ligand workflows. MOPAC uses PM7 by default.",
        description_pt="Ponto de partida recomendado para a maioria dos ligantes organicos, de quimica medicinal e sistemas mistos. O MOPAC usa PM7 por padrao.",
    ),
    MopacMethodInfo(
        keyword="PM6",
        title_en="Older broad-coverage semiempirical method.",
        title_pt="Metodo semiempirico mais antigo e abrangente.",
        description_en="Useful when you need compatibility with older PM6 workflows or literature benchmarks. Reasonable as a comparison baseline against PM7.",
        description_pt="Util para compatibilidade com fluxos antigos baseados em PM6 ou com benchmarks da literatura. Bom como linha de base para comparar com PM7.",
    ),
    MopacMethodInfo(
        keyword="PM6-D3H4X",
        title_en="PM6 with dispersion, hydrogen-bond, and halogen-bond corrections.",
        title_pt="PM6 com correcoes de dispersao, ligacao de hidrogenio e halogenios.",
        description_en="Good option for noncovalent complexes, halogenated ligands, and protein-ligand style interactions where halogen contacts matter.",
        description_pt="Boa opcao para complexos nao covalentes, ligantes halogenados e interacoes tipo proteina-ligante onde contatos com halogenios importam.",
    ),
    MopacMethodInfo(
        keyword="PM6-ORG",
        title_en="PM6 variant optimized for organic chemistry and protein-like geometries.",
        title_pt="Variante do PM6 otimizada para quimica organica e geometrias tipo proteina.",
        description_en="Useful for organic molecules, noncovalent interactions, and biomolecular geometries. Avoid relying on it when problematic iodine-containing systems are expected.",
        description_pt="Util para moleculas organicas, interacoes nao covalentes e geometrias biomoleculares. Evite confiar nele quando houver sistemas problematicos contendo iodo.",
    ),
    MopacMethodInfo(
        keyword="RM1",
        title_en="Legacy reparameterized model for survey and compatibility studies.",
        title_pt="Modelo legado reparametrizado para estudos de compatibilidade e triagem.",
        description_en="Best used when reproducing older workflows or comparing against literature that explicitly used RM1. Not the default choice for new projects.",
        description_pt="Mais util para reproduzir fluxos antigos ou comparar com literatura que usou RM1 explicitamente. Nao e a escolha padrao para projetos novos.",
    ),
    MopacMethodInfo(
        keyword="PM3",
        title_en="Legacy semiempirical model retained for historical comparisons.",
        title_pt="Modelo semiempirico legado mantido para comparacoes historicas.",
        description_en="Use mainly for compatibility with older datasets, QSAR workflows, or literature methods that were developed around PM3.",
        description_pt="Use principalmente para compatibilidade com conjuntos antigos, fluxos QSAR ou metodos da literatura desenvolvidos em torno do PM3.",
    ),
    MopacMethodInfo(
        keyword="AM1",
        title_en="Classic legacy semiempirical model.",
        title_pt="Modelo semiempirico classico e legado.",
        description_en="Relevant mostly for reproducing historical calculations and comparing with older medicinal chemistry literature.",
        description_pt="Relevante principalmente para reproduzir calculos historicos e comparar com literatura antiga de quimica medicinal.",
    ),
    MopacMethodInfo(
        keyword="MNDO",
        title_en="Earliest family baseline model.",
        title_pt="Modelo basal mais antigo da familia.",
        description_en="Primarily useful for educational purposes, method comparisons, and reproducing very old literature.",
        description_pt="Principalmente util para fins didaticos, comparacoes metodologicas e reproducao de literatura muito antiga.",
    ),
)


COMMON_MOPAC_METHOD_KEYWORDS = tuple(method.keyword for method in COMMON_MOPAC_METHODS)


def normalize_mopac_method(value: str | None) -> str:
    normalized = (value or "PM7").strip().upper()
    return normalized or "PM7"


def get_method_info(method: str | None) -> MopacMethodInfo | None:
    normalized = normalize_mopac_method(method)
    for info in COMMON_MOPAC_METHODS:
        if info.keyword == normalized:
            return info
    return None
