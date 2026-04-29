import shutil
import uuid

from src.utils.config import PROJECT_ROOT
from src.utils.models import ProtonatedLigandRecord
from src.visualization.structure_panels import StructurePanelGenerator


def test_generate_structure_panel_pdf() -> None:
    output_dir = PROJECT_ROOT / "data" / "intermediate" / "test_tmp" / str(uuid.uuid4())
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = StructurePanelGenerator(
        {
            "output_dir": str(output_dir),
            "page_rows": 2,
            "page_columns": 2,
            "image_width_px": 320,
            "image_height_px": 220,
        }
    )
    ligands = [
        ProtonatedLigandRecord(access_code="CMPD_001", protonated_smiles="CCO"),
        ProtonatedLigandRecord(access_code="CMPD_002", protonated_smiles="CC[NH+](C)C"),
        ProtonatedLigandRecord(access_code="CMPD_003", protonated_smiles="c1ccccc1"),
    ]

    pdf_path, page_count = generator.generate(ligands, ph=7.4)

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert page_count == 1

    shutil.rmtree(output_dir, ignore_errors=True)
