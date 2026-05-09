"""Sistema de temas dos flet_wizards.

Define `WizardTheme` como dataclass imutável com a paleta completa exigida
por todos os componentes (`primary`, `secondary`, `accent`, `bg`, `surface`,
`card`, `panel`, `border`, `text`, `sub`).

Os built-ins (`SLATE`, `EMERALD`, `ROSE`, `AZURE`) são instâncias anexadas
à própria classe e usam exatamente os valores hex do `docs/reference/wizard.py`.
`THEMES_BY_NAME` expõe o mesmo conjunto indexado pelo nome capitalizado,
útil para seletores de tema baseados em string.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WizardTheme:
    """Paleta de cores aplicada a um wizard."""

    primary: str
    secondary: str
    accent: str
    bg: str
    surface: str
    card: str
    panel: str
    border: str
    text: str
    sub: str


WizardTheme.SLATE = WizardTheme(
    primary="#7C6EF6",
    secondary="#A89EFA",
    accent="#38BDF8",
    bg="#0B0B0F",
    surface="#111118",
    card="#17171F",
    panel="#141420",
    border="#222230",
    text="#F0EEF8",
    sub="#6B6880",
)

WizardTheme.EMERALD = WizardTheme(
    primary="#34D399",
    secondary="#6EE7B7",
    accent="#60A5FA",
    bg="#090E0C",
    surface="#0E1610",
    card="#121C14",
    panel="#101810",
    border="#1C2E1E",
    text="#ECFDF5",
    sub="#4A7060",
)

WizardTheme.ROSE = WizardTheme(
    primary="#F472B6",
    secondary="#FBCFE8",
    accent="#FB923C",
    bg="#0E090C",
    surface="#170E12",
    card="#1C1016",
    panel="#180E14",
    border="#2C1820",
    text="#FDF2F8",
    sub="#7A3C58",
)

WizardTheme.AZURE = WizardTheme(
    primary="#60A5FA",
    secondary="#93C5FD",
    accent="#A78BFA",
    bg="#080B10",
    surface="#0D1018",
    card="#12161E",
    panel="#0F1420",
    border="#1C2236",
    text="#EFF6FF",
    sub="#3C5070",
)


THEMES_BY_NAME: dict[str, WizardTheme] = {
    "Slate": WizardTheme.SLATE,
    "Emerald": WizardTheme.EMERALD,
    "Rose": WizardTheme.ROSE,
    "Azure": WizardTheme.AZURE,
}


DEFAULT_THEME: WizardTheme = WizardTheme.SLATE
