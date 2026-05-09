"""Estado reativo base compartilhado por todos os flet_wizards.

`BaseWizardState` é uma dataclass observável que centraliza:

- navegação (`step`, `loading`) e métodos `go_next` / `go_back` / `reset`
- tema atual (`theme: WizardTheme`) com acessores curtos no estilo do
  `docs/reference/wizard.py` (`state.primary()`, `state.text()`, …)
- contagem de steps via `TOTAL_STEPS: ClassVar[int]`, sobrescrita por
  cada subclasse de wizard

O índice `step == TOTAL_STEPS` é convencionado como step de conclusão
(success). O renderizador do wizard decide o que mostrar nesse índice;
o estado apenas garante que `go_next` permite alcançá-lo.

Subclasses devem ser decoradas novamente com `@ft.observable @dataclass`
e podem sobrescrever `reset()` chamando `super().reset()` para também
zerar seus campos próprios.
"""

from dataclasses import dataclass, field
from typing import ClassVar

import flet as ft

from .theme import DEFAULT_THEME, WizardTheme


@ft.observable
@dataclass
class BaseWizardState:
    """Store reativo central de um wizard."""

    TOTAL_STEPS: ClassVar[int] = 1

    step: int = 0
    loading: bool = False
    theme: WizardTheme = field(default_factory=lambda: DEFAULT_THEME)

    def go_next(self) -> None:
        """Avança um step, permitindo alcançar o índice de sucesso."""
        if self.step < self.TOTAL_STEPS:
            self.step += 1

    def go_back(self) -> None:
        """Volta um step até o limite inferior 0."""
        if self.step > 0:
            self.step -= 1

    def reset(self) -> None:
        """Zera navegação e loading. Subclasses devem chamar super().reset()."""
        self.step = 0
        self.loading = False

    def is_done(self) -> bool:
        """True quando o wizard está no step de conclusão."""
        return self.step >= self.TOTAL_STEPS

    def set_theme(self, theme: WizardTheme) -> None:
        """Atualiza o tema corrente — observável reativa todos os componentes."""
        self.theme = theme

    def primary(self) -> str:
        return self.theme.primary

    def secondary(self) -> str:
        return self.theme.secondary

    def accent(self) -> str:
        return self.theme.accent

    def bg(self) -> str:
        return self.theme.bg

    def surface(self) -> str:
        return self.theme.surface

    def card(self) -> str:
        return self.theme.card

    def panel(self) -> str:
        return self.theme.panel

    def border(self) -> str:
        return self.theme.border

    def text(self) -> str:
        return self.theme.text

    def sub(self) -> str:
        return self.theme.sub
