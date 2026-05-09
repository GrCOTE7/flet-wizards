"""Pipeline de geração de documentação dos wizards via OpenAI.

Lê todos os `WizardMeta` do registry (populado pelos imports dos
módulos de wizards) e produz, na raiz do repo:

  - `docs/<categoria>/<template>.md` — um arquivo por template
  - `README.md` — visão geral com badges, tabela e blocos de uso

Disparado via GitHub Actions em commits que alteram `src/wizards/`.
A chave da OpenAI vem de `OPENAI_API_KEY` (secret do repositório).

## Idempotência

Cada doc gerado começa com um marker `<!-- generated-from-hash: XXX -->`
contendo o hash SHA-256 (16 chars) da meta serializada (incluindo
`class_name` e `module_path` derivados). Antes de chamar OpenAI, o
pipeline compara o hash corrente com o do arquivo existente: se igual,
pula (sem custo). Se diferente ou se o arquivo não existe, regenera.
README é sempre re-renderizado (não usa OpenAI).

## Status

Implementação inicial **standalone** — não usa o framework `cocoindex`
propriamente. O nome do arquivo segue o spec do CLAUDE.md; migração
para `flow_def` do cocoindex fica como TODO quando precisar de tracking
incremental persistido (ex: detectar deleção de wizard entre runs).

## Execução local

```powershell
$env:OPENAI_API_KEY = "sk-..."
uv run --extra pipeline python pipeline/cocoindex_pipeline.py
```
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"
README_PATH = PROJECT_ROOT / "README.md"

sys.path.insert(0, str(SRC_DIR))

import wizards.auth.login  # noqa: E402, F401
import wizards.auth.recovery  # noqa: E402, F401
import wizards.auth.register  # noqa: E402, F401
import wizards.profile.avatar  # noqa: E402, F401
import wizards.profile.edit  # noqa: E402, F401
import wizards.profile.setup  # noqa: E402, F401

from wizards.core import (  # noqa: E402
    WizardMeta,
    all_wizards,
    by_category,
    categories,
)

MODEL = "gpt-4o-mini"
HASH_MARKER = "<!-- generated-from-hash: "
HASH_END = " -->"


def _class_name(meta_id: str) -> str:
    """`auth.login` → `AuthLoginWizard`. Convenção fixa do projeto."""
    parts = meta_id.split(".")
    return "".join(p.capitalize() for p in parts) + "Wizard"


def _module_path(meta_id: str) -> str:
    """`auth.login` → `wizards.auth.login`."""
    return f"wizards.{meta_id}"


SYSTEM_PROMPT = """Você é um gerador de documentação técnica para uma biblioteca Python de wizards multi-step em Flet.

Receberá um JSON com a metadata de um template:
- `id`, `name`, `category`, `description`
- `steps`: lista de nomes dos steps na ordem
- `platforms`: lista de plataformas suportadas
- `on_complete_schema`: dict com os campos retornados ao callback de conclusão
- `class_name`: NOME REAL DA CLASSE PYTHON do wizard
- `module_path`: caminho de import do módulo

Devolva APENAS Markdown em português, técnico e direto, com EXATAMENTE esta estrutura (sem nenhum texto fora dela):

# <use o valor real de `name`>

> <use o valor real de `description`>

## Steps

Tabela Markdown com colunas `#` e `Nome` listando cada step na ordem (1-indexed).

## Campos por step

Para cada step, uma subseção `### <N>. <nome do step>` listando os campos visíveis nesse step.

Regras:
- Distribua os campos de `on_complete_schema` pelos steps inferindo pelo nome do step (ex: step "Acesso" tem credenciais; step "Perfil" tem nome/papel; step "Confirmação" só revisa).
- Cada campo aparece em UM step só.
- Quando um step só revisa/confirma sem capturar dados novos, escreva exatamente: `_Não captura dados novos — apenas revisa o que foi preenchido._`
- Formato dos itens: `- **<nome_do_campo>** (`<tipo>`) — descrição curta inferida do contexto`

## Plataformas suportadas

Lista bullet das plataformas em nomes amigáveis (Windows, macOS, Linux, Android, iOS, etc).

## Retorno do `on_complete`

Tabela Markdown com colunas `Campo` e `Tipo` derivada de `on_complete_schema`. Se o schema for vazio, escreva: `_Nenhum dado é retornado._`

## Uso

Bloco de código Python completo. EXEMPLO de referência (para um wizard hipotético com `class_name="AuthLoginWizard"`, `module_path="wizards.auth.login"`, `on_complete_schema={"email": "str"}`):

```python
import flet as ft
from wizards.auth.login import AuthLoginWizard
from wizards.core import WizardTheme


async def main(page: ft.Page) -> None:
    async def on_complete(data: dict) -> None:
        print(data["email"])

    page.render(lambda: AuthLoginWizard(
        theme=WizardTheme.SLATE,
        on_complete=on_complete,
    ))


ft.run(main)
```

Para o wizard recebido neste request, gere um bloco com a MESMA estrutura, substituindo:
- `wizards.auth.login` pelo `module_path` REAL
- `AuthLoginWizard` (nas DUAS ocorrências) pelo `class_name` REAL
- O único `print(data["email"])` por UMA LINHA `print(data["<chave>"])` para CADA chave de `on_complete_schema`, usando os nomes exatos das chaves

USE LITERALMENTE os valores de `class_name` e `module_path` do JSON. NUNCA invente nomes. NUNCA use placeholders como `<module_path>`, `[seu app]` ou `YourWizard` no código final.

## Mock no gallery

Uma única frase explicando que o wizard expõe `mock=True` para abrir já no último step de dados com valores fictícios — útil em previews dentro do gallery showcase.

REGRAS GERAIS:
- NÃO inclua introdução, conclusão, badges, HTML, sumário ou qualquer texto fora dessa estrutura.
- NÃO traduza nomes de campos do schema.
- NÃO use bold/italic em headers (ex: `# **<name>**` é PROIBIDO).
"""


def _meta_to_dict(meta: WizardMeta) -> dict:
    """Serialização canônica usada na hash E no payload OpenAI.

    Inclui `class_name` e `module_path` derivados — ambos vão pro hash,
    então renomear convenção dispara regeneração de todos os docs.
    """
    return {
        "id": meta.id,
        "name": meta.name,
        "category": meta.category,
        "description": meta.description,
        "steps": list(meta.steps),
        "platforms": [p.name for p in meta.platforms],
        "on_complete_schema": dict(meta.on_complete_schema),
        "class_name": _class_name(meta.id),
        "module_path": _module_path(meta.id),
    }


def _meta_hash(meta: WizardMeta) -> str:
    """SHA-256 truncado em 16 chars do JSON canônico da meta."""
    blob = json.dumps(_meta_to_dict(meta), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _existing_hash(path: Path) -> str | None:
    """Lê o hash do marker no topo do arquivo, ou None se não existir."""
    if not path.exists():
        return None
    head = path.read_text(encoding="utf-8")[:200]
    if HASH_MARKER not in head:
        return None
    start = head.index(HASH_MARKER) + len(HASH_MARKER)
    end = head.index(HASH_END, start)
    return head[start:end].strip()


def _doc_path(meta: WizardMeta) -> Path:
    """`docs/<categoria>/<template>.md` derivado do meta.id ('cat.tid')."""
    parts = meta.id.split(".", 1)
    template = parts[1] if len(parts) > 1 else meta.id
    return DOCS_DIR / meta.category / f"{template}.md"


def _generate_doc(meta: WizardMeta, client) -> str:
    """Chama OpenAI e devolve o Markdown completo (com marker de hash no topo)."""
    user_payload = json.dumps(_meta_to_dict(meta), ensure_ascii=False, indent=2)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ],
        temperature=0.2,
    )
    body = response.choices[0].message.content.strip()
    marker = f"{HASH_MARKER}{_meta_hash(meta)}{HASH_END}\n\n"
    return marker + body + "\n"


def _render_readme(metas: list[WizardMeta]) -> str:
    """README com badges, descrição expandida, tabela e blocos de uso. Sem OpenAI."""
    lines = [
        "# flet-wizards",
        "",
        "[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)",
        "[![Flet](https://img.shields.io/badge/flet-0.85+-purple.svg)](https://flet.dev)",
        "[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)",
        "",
        "Coleção de templates de wizard multi-step prontos para reutilizar em apps Flet.",
        "Cada template é uma `@ft.component` autocontida com estado reativo (`@ft.observable`),",
        "sistema de temas (Slate / Emerald / Rose / Azure), validação de plataforma e callback",
        "`on_complete` tipado. Inclui um gallery showcase estilo Microsoft Store para visualizar",
        "todos os templates ao vivo durante o desenvolvimento.",
        "",
        "## Templates disponíveis",
        "",
        "| Categoria | Nome | Steps | Descrição |",
        "|-----------|------|-------|-----------|",
    ]
    for cat in categories():
        for meta in by_category(cat):
            doc_link = _doc_path(meta).relative_to(PROJECT_ROOT).as_posix()
            lines.append(
                f"| {cat} | [{meta.name}]({doc_link}) | {len(meta.steps)} | {meta.description} |"
            )
    lines += [
        "",
        "## Instalação",
        "",
        "```bash",
        "# em breve no PyPI",
        "# pip install flet-wizards",
        "```",
        "",
        "Por enquanto, clone o repo e use `uv sync` para instalar as dependências.",
        "",
        "## Uso rápido",
        "",
        "```python",
        "import flet as ft",
        "from wizards.auth.login import AuthLoginWizard",
        "",
        "async def main(page: ft.Page):",
        "    page.render(lambda: AuthLoginWizard(on_complete=lambda d: print(d)))",
        "",
        "ft.run(main)",
        "```",
        "",
        "## Gallery",
        "",
        "```powershell",
        "uv run flet run",
        "```",
        "",
        "Abre o showcase com sidebar por categoria, seletor de tema (4 paletas) e preview ao vivo de cada template.",
        "",
        "---",
        "",
        "_Documentação regenerada automaticamente por `pipeline/cocoindex_pipeline.py`._",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY não definida — abortando")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        logger.error(
            "openai não instalado — rode `uv sync --extra pipeline` ou adicione manualmente"
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    metas = all_wizards()
    logger.info("Encontrados {} wizards no registry", len(metas))

    regenerated = 0
    skipped = 0
    for meta in metas:
        path = _doc_path(meta)
        new_hash = _meta_hash(meta)
        if _existing_hash(path) == new_hash:
            logger.info("[skip] {} (hash inalterado)", meta.id)
            skipped += 1
            continue

        logger.info("[gen]  {} → {}", meta.id, path.relative_to(PROJECT_ROOT))
        content = _generate_doc(meta, client)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        regenerated += 1

    readme = _render_readme(metas)
    README_PATH.write_text(readme, encoding="utf-8")
    logger.info("README.md atualizado com {} wizards", len(metas))
    logger.info("Concluído: {} regenerado(s), {} ignorado(s)", regenerated, skipped)


if __name__ == "__main__":
    main()
