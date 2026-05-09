"""Registro central de metadados de flet_wizards.

`WizardMeta` é o contrato declarado por cada template no topo do seu módulo.
Serve como fonte de verdade para:

- o gallery, que lista templates por categoria e renderiza os cards
- o pipeline CocoIndex, que gera a documentação a partir dos campos

`register(meta)` adiciona a meta ao índice global; idempotente, repetir
chamadas com o mesmo `id` substitui a entrada anterior. Os helpers
`all_wizards`, `by_category` e `by_id` consultam esse índice.
"""

from dataclasses import dataclass, field

import flet as ft


@dataclass(frozen=True)
class WizardMeta:
    """Metadados públicos de um template de wizard."""

    id: str
    name: str
    category: str
    description: str
    steps: list[str]
    platforms: list[ft.PagePlatform]
    on_complete_schema: dict[str, str] = field(default_factory=dict)


_REGISTRY: dict[str, WizardMeta] = {}


def register(meta: WizardMeta) -> WizardMeta:
    """Adiciona/atualiza `meta` no índice global e devolve a própria instância."""
    _REGISTRY[meta.id] = meta
    return meta


def all_wizards() -> list[WizardMeta]:
    """Lista todas as metas registradas, ordenadas por id."""
    return sorted(_REGISTRY.values(), key=lambda m: m.id)


def by_category(category: str) -> list[WizardMeta]:
    """Filtra metas por categoria, preservando a ordenação por id."""
    return [m for m in all_wizards() if m.category == category]


def by_id(wizard_id: str) -> WizardMeta | None:
    """Devolve a meta correspondente ao id, ou None se não registrada."""
    return _REGISTRY.get(wizard_id)


def categories() -> list[str]:
    """Lista categorias únicas presentes no registro, em ordem alfabética."""
    return sorted({m.category for m in _REGISTRY.values()})
