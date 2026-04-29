# MOPAC Methods in SMILES2DockingFULL

`PM7` is the default method in the application. It is the recommended starting point for most ligand-preparation workflows.

Methods exposed in the GUI:

- `PM7`: general-purpose default for most organic and medicinal-chemistry ligands.
- `PM6`: useful when reproducing older PM6-based workflows or comparing against older benchmarks.
- `PM6-D3H4X`: better suited to noncovalent systems, halogenated ligands, and cases where dispersion and halogen-bond corrections can matter.
- `PM6-ORG`: tuned toward organic chemistry and biomolecular-like geometries.
- `RM1`: legacy reparameterized model, mainly for compatibility studies and older literature.
- `PM3`: legacy model, mainly for historical comparison and reproduction of older workflows.
- `AM1`: classic legacy semiempirical model, mainly for historical comparison.
- `MNDO`: oldest baseline model in this set, mainly for teaching, benchmarking, and very old literature reproduction.

The method selector in the GUI is editable. If a needed method is not listed, a valid MOPAC keyword can be typed manually.

These short recommendations are intended as workflow guidance, not as a substitute for method validation on a specific chemical series.
