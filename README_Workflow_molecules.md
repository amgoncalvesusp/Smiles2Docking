# Workflow_molecules

## System Instructions for the OpenClaw Agent

You are responsible for designing, maintaining, and executing the `Workflow_molecules` project. Your behavior in this repository must follow the instructions below exactly unless the user explicitly changes them.

If any requirement is ambiguous, underspecified, conflicting, or chemically unsafe, you must stop and ask for clarification before proceeding.

---

## 1. The Goal

The purpose of the `Workflow_molecules` project is to build a reliable, chemistry-aware Python workflow that:

1. Connects to a database or data source.
2. Retrieves molecular records and their associated access codes.
3. Extracts SMILES strings from those records.
4. Standardizes and preprocesses the SMILES according to medicinal chemistry best practices.
5. Removes ions, salts, counterions, and disconnected inorganic fragments when present.
6. Preserves Kekulé representations whenever possible and chemically appropriate.
7. Evaluates and assigns protonation-related states using Open Babel.
8. Builds 3D molecular structures.
9. Saves the final prepared molecules in `.mol2` format.
10. Names each final 3D structure file using the molecule access code from the database.
11. Produces a final summary report describing how many molecules were processed and how many were successfully transformed.

The workflow must prioritize chemical plausibility, traceability, reproducibility, and safe handling of edge cases.

---

## 2. Environment and Tooling Rules

You must create and manage your own Conda environment for this project.

### Mandatory environment requirements

The environment must include, at minimum:

- Python
- RDKit
- Open Babel
- Standard logging and data-processing support packages
- Any additional Python packages that you determine are necessary for robust execution

You are allowed to decide which additional packages are best suited for the task, provided that they improve reliability, maintainability, reproducibility, or chemical correctness.

### Environment behavior

- Use an isolated Conda environment dedicated to this project.
- Record the environment specification in a reproducible form whenever possible.
- Prefer stable, well-maintained packages.
- Avoid unnecessary dependencies.
- Ensure RDKit and Open Babel are available and functional before running any molecular workflow.
- Validate that the environment can successfully parse SMILES, manipulate molecular structures, and export MOL2 files.

If package conflicts prevent a stable setup, you must stop and ask for clarification before improvising a workaround that may affect chemistry results.

---

## 3. Structure

The project should remain organized and easy for both humans and AI agents to understand. Use or maintain a structure similar to the one below.

```text
Workflow_molecules/
├── README.md
├── environment/
│   ├── environment.yml
│   └── requirements.txt
├── config/
│   ├── settings.yaml
│   └── database_config.example.yaml
├── data/
│   ├── raw/
│   ├── intermediate/
│   ├── processed/
│   └── reports/
├── logs/
├── src/
│   ├── database/
│   ├── preprocessing/
│   ├── protonation/
│   ├── structure_generation/
│   ├── export/
│   └── utils/
├── scripts/
└── tests/
```

### Directory descriptions

#### `environment/`
Contains reproducibility files for the Conda environment and any dependency declarations.

#### `config/`
Contains configuration files for database access, runtime parameters, file paths, protonation options, filtering rules, and export settings.

#### `data/raw/`
Stores raw inputs obtained directly from the database or source system, without modification.

#### `data/intermediate/`
Stores temporary or partially processed molecular records, such as cleaned SMILES, fragment-filtered molecules, or protonation-stage outputs.

#### `data/processed/`
Stores final prepared molecules. Final 3D `.mol2` files must be written here unless the user specifies another output directory.

#### `data/reports/`
Stores final run summaries and molecule-processing reports.

#### `logs/`
Stores execution logs, warnings, errors, skipped records, and diagnostic information.

#### `src/database/`
Implements data-source access and record retrieval.

#### `src/preprocessing/`
Implements SMILES cleaning, fragment handling, ion removal, standardization, and Kekulé-preserving logic.

#### `src/protonation/`
Implements protonation-state handling using Open Babel and any related validation steps.

#### `src/structure_generation/`
Implements 3D coordinate generation, conformation building, geometry optimization, and quality checks.

#### `src/export/`
Implements writing of final `.mol2` files and naming rules.

#### `src/utils/`
Contains shared helper functions, logging utilities, validation routines, and reusable components.

#### `scripts/`
Contains executable entry points for running the workflow.

#### `tests/`
Contains tests for the database connection layer, molecule preprocessing, protonation handling, naming conventions, and output generation.

---

## 4. Workflow

You must follow a consistent workflow whenever working on this project.

### Step 1: Initialize the environment

- Create the Conda environment.
- Install RDKit, Open Babel, and any other required packages.
- Verify that all core tools are functioning.
- Do not continue if the environment is broken.

### Step 2: Connect to the data source

- Access the database or approved source.
- Retrieve molecular records and their unique access codes.
- Preserve the access code because it will become the final output filename.
- Log records that cannot be retrieved cleanly.

### Step 3: Extract and validate SMILES

- Read the SMILES string for each record.
- Validate whether the SMILES can be parsed.
- Reject or flag records with invalid, empty, or corrupt SMILES.
- Preserve an audit trail for failed records.

### Step 4: Remove ions, salts, and disconnected non-target fragments

When a SMILES contains ions or multiple disconnected fragments:

- Remove salts, counterions, spectator ions, and unrelated inorganic fragments.
- Retain the chemically relevant parent structure whenever that choice is clear.
- Apply medicinal chemistry best practices when deciding which fragment is the principal molecule.
- Do not silently guess when the principal fragment is ambiguous.
- If ambiguity exists, stop and ask the user how to proceed.

This behavior is mandatory. Molecules containing ionic companions must not be exported with those unwanted ions attached as separate fragments.

### Step 5: Preserve Kekulé representations

- Preserve Kekulé structure information whenever possible and chemically meaningful.
- Avoid unnecessary aromaticity transformations that would erase a valid Kekulé representation.
- Ensure the final representation remains chemically valid and exportable.
- If software conversions force changes in bond representation, document that in logs or reports.

### Step 6: Evaluate protonation state

- Use Open Babel to evaluate protonation-related states as part of molecular preparation.
- Apply a chemically reasonable protonation workflow.
- Ensure the method is consistent across molecules in the same run unless the user instructs otherwise.
- Record important protonation decisions when relevant.
- If protonation treatment may significantly affect interpretation, stop and ask for clarification before continuing.

### Step 7: Generate 3D structures

- Build 3D coordinates for the cleaned parent molecule.
- Use robust methods for conformation generation and structural preparation.
- Perform basic geometry refinement when appropriate.
- Reject structures that fail generation or are chemically nonsensical.
- Record failures in logs and reports.

### Step 8: Export final molecules

- Save final structures in `.mol2` format.
- Each exported 3D structure must be named using the database access code of that molecule.
- Do not use generic filenames when the access code is available.
- Ensure filenames are filesystem-safe while preserving the record identity.

Example naming rule:

```text
<data_access_code>.mol2
```

### Step 9: Produce a final run report

At the end of every molecule-processing operation, you must generate a small report file.

The report must include, at minimum:

- Total number of molecular records retrieved
- Total number of SMILES evaluated
- Number of invalid or unreadable SMILES
- Number of molecules successfully cleaned
- Number of molecules from which ions or salts were removed
- Number of molecules successfully converted to 3D
- Number of final `.mol2` files written
- Number of failures or skipped entries

The report should be written to `data/reports/` in a machine-readable or human-readable format such as `.txt`, `.md`, `.csv`, or `.json`.

This reporting step is mandatory and must always occur at the end of processing.

---

## 5. Medicinal Chemistry Best Practices

You must follow best practices appropriate for medicinal chemistry workflows.

### Required principles

- Prefer the biologically relevant parent structure over salts and counterions.
- Avoid retaining disconnected ions unless the user explicitly asks for them.
- Preserve chemically meaningful valence states.
- Avoid destructive transformations that alter molecular identity without justification.
- Keep preprocessing consistent across the dataset.
- Maintain traceability from raw record to final exported file.
- Log all major transformations that affect chemical interpretation.

### Do not do the following

- Do not silently keep salts or ionic spectators when the workflow requires parent compounds.
- Do not silently merge disconnected fragments into an invented single molecule.
- Do not overwrite record identity.
- Do not continue after ambiguous chemistry decisions without asking the user.
- Do not assume protonation rules that materially affect the project without clarification when uncertainty exists.

---

## 6. Clarification Policy

If there is any doubt, you must ask before continuing.

You must ask for clarification when:

- the principal fragment cannot be identified confidently,
- the protonation strategy is ambiguous,
- the database schema is unclear,
- multiple valid naming policies are possible,
- the requested chemistry behavior conflicts with the current implementation,
- package installation choices may materially affect reproducibility or output chemistry.

Never hide uncertainty. Never continue through unresolved ambiguity when it may affect molecular identity, structure, protonation, or final output.

---

## 7. Minimum Expected Outputs

A successful run of the project should produce:

1. A functioning Conda environment that includes RDKit and Open Babel.
2. A reproducible workflow script or pipeline.
3. Final cleaned and protonation-processed 3D molecules in `.mol2` format.
4. Output filenames based on the database access code.
5. Logs describing important events and failures.
6. A final small report summarizing how many molecules were transformed.

---

## 8. Operational Summary

In every standard execution, you must:

- create and validate the Conda environment,
- include RDKit and Open Babel,
- retrieve molecular records from the database,
- extract and validate SMILES,
- remove ions and salts,
- preserve Kekulé structure information,
- evaluate protonation state with Open Babel,
- generate 3D structures,
- save final files as access-code-based `.mol2` files,
- and produce a final report with molecule counts.

If anything important is unclear, ask before proceeding.
