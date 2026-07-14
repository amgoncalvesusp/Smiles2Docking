"""Per-atom pKa prediction for MolGpKa.

Vendored from MolGpKa (https://github.com/Xundrug/MolGpKa), MIT License.
Patched for SMILES2Docking:
  * Package-relative imports and package-local model weights.
  * Models are loaded once and cached (the upstream code reloaded the weights
    on every molecule).
"""

from __future__ import annotations

import os.path as osp
from functools import lru_cache

import torch
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")
from rdkit.Chem.MolStandardize import rdMolStandardize

from .descriptor import mol2vec
from .ionization_group import get_ionization_aid
from .net import GCNNet

root = osp.abspath(osp.dirname(__file__))


@lru_cache(maxsize=2)
def load_model(model_file, device="cpu"):
    model = GCNNet().to(device)
    model.load_state_dict(torch.load(model_file, map_location=device))
    model.eval()
    return model


def model_pred(m2, aid, model, device="cpu"):
    data = mol2vec(m2, aid)
    with torch.no_grad():
        data = data.to(device)
        pKa = model(data)
        pKa = pKa.cpu().numpy()
        pka = pKa[0][0]
    return pka


def predict_acid(mol):
    model_file = osp.join(root, "models", "weight_acid.pth")
    model_acid = load_model(model_file)

    acid_idxs = get_ionization_aid(mol, acid_or_base="acid")
    acid_res = {}
    for aid in acid_idxs:
        apka = model_pred(mol, aid, model_acid)
        acid_res.update({aid: apka})
    return acid_res


def predict_base(mol):
    model_file = osp.join(root, "models", "weight_base.pth")
    model_base = load_model(model_file)

    base_idxs = get_ionization_aid(mol, acid_or_base="base")
    base_res = {}
    for aid in base_idxs:
        bpka = model_pred(mol, aid, model_base)
        base_res.update({aid: bpka})
    return base_res


def predict(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict


def predict_for_protonate(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict, mol
