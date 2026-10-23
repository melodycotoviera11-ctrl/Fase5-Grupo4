from pathlib import Path
from conftest import REPO


def test_CP_RNF07_01_separacion_capas_identificable(chk):
    esperados = [REPO / "src" / "view", REPO / "src" / "controller", REPO / "src" / "model", REPO / "src" / "db"]
    faltantes = [str(p.relative_to(REPO)) for p in esperados if not p.exists()]
    model_files = list((REPO / "src" / "model").rglob("*.py"))
    imports_view = []
    for p in model_files:
        texto = p.read_text(encoding="utf-8", errors="replace")
        if "src.view" in texto or "tkinter" in texto:
            imports_view.append(str(p.relative_to(REPO)))
    chk.obs(f"capas existentes={[p.exists() for p in esperados]}; imports de GUI en model={imports_view}")
    chk.ok(not faltantes, f"faltan capas/módulos identificables: {faltantes}")
    chk.ok(not imports_view, f"la lógica de negocio depende de la GUI: {imports_view}")
