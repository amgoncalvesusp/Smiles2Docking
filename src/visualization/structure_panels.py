from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor

from src.utils.models import ProtonatedLigandRecord


class StructurePanelError(Exception):
    """Raised when the protonated structure panel PDF cannot be created."""


@dataclass(slots=True)
class StructurePanelGenerator:
    settings: dict

    def generate(self, ligands: list[ProtonatedLigandRecord], ph: float) -> tuple[Path, int]:
        if not ligands:
            raise StructurePanelError("No ligands available for figure generation.")

        output_dir = Path(self.settings["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        rows = int(self.settings.get("page_rows", 4))
        columns = int(self.settings.get("page_columns", 3))
        molecules_per_page = rows * columns
        image_width = int(self.settings.get("image_width_px", 420))
        image_height = int(self.settings.get("image_height_px", 260))

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pdf_path = output_dir / f"protonated_ligands_pH_{ph:.2f}_{timestamp}.pdf"

        page_count = ceil(len(ligands) / molecules_per_page)
        with PdfPages(pdf_path) as pdf:
            for page_index in range(page_count):
                page_items = ligands[page_index * molecules_per_page : (page_index + 1) * molecules_per_page]
                figure, axes = plt.subplots(rows, columns, figsize=(8.27, 11.69))
                figure.patch.set_facecolor("#f7f4ed")
                figure.suptitle(
                    f"Ligantes Protonados em pH {ph:.2f}",
                    fontsize=16,
                    fontweight="bold",
                    color="#17324d",
                )
                axes_iterable = axes.flatten() if hasattr(axes, "flatten") else [axes]

                for axis, ligand in zip(axes_iterable, page_items):
                    axis.set_facecolor("#fffdf8")
                    axis.axis("off")
                    axis.set_title(ligand.access_code, fontsize=10, fontweight="bold", color="#1b2a41", pad=10)
                    axis.text(
                        0.5,
                        1.02,
                        fill(ligand.protonated_smiles, width=32),
                        ha="center",
                        va="bottom",
                        fontsize=6.5,
                        color="#506070",
                        transform=axis.transAxes,
                    )
                    image = self._draw_image(ligand.protonated_smiles, image_width, image_height)
                    axis.imshow(image)

                for axis in axes_iterable[len(page_items) :]:
                    axis.set_facecolor("#f7f4ed")
                    axis.axis("off")

                figure.text(
                    0.5,
                    0.02,
                    f"Página {page_index + 1} de {page_count} | {len(ligands)} ligantes | SMILES2Docking",
                    ha="center",
                    fontsize=8,
                    color="#506070",
                )
                figure.tight_layout(rect=(0.04, 0.04, 0.96, 0.95))
                pdf.savefig(figure, dpi=300)
                plt.close(figure)

        return pdf_path, page_count

    def _draw_image(self, smiles: str, width: int, height: int):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise StructurePanelError(f"Unable to depict protonated SMILES: {smiles}")
        rdDepictor.Compute2DCoords(molecule)
        return Draw.MolToImage(molecule, size=(width, height), kekulize=True)
