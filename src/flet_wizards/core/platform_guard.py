"""Guard de compatibilidade de plataforma.

`PlatformGuard` envolve a UI de um wizard e checa `page.platform` contra a
lista `supported_platforms`. Se a plataforma corrente não estiver na lista,
portala um `ft.AlertDialog` modal via `ft.use_dialog()` com botão
"Continuar mesmo assim". Por trás do dialog, renderiza um placeholder
vazio na cor de fundo do tema — o `build()` do wizard só é chamado quando
suportado ou após o bypass, evitando inicializar APIs que poderiam quebrar
em plataformas não previstas.

Sobre o uso de `ft.use_state`: ele permanece para memorizar o bypass —
`ft.use_dialog` é hook de portalização, não de estado. O que mudou vs
versão anterior: a tela de bloqueio deixou de ser um `return` inline
(takeover de tela inteira) e virou um modal portado por use_dialog.

Todos os wizards da versão inicial suportam todas as plataformas; este
guard existe para templates futuros mobile-only.
"""

from typing import Callable

import flet as ft

from .components import ghost_button
from .theme import WizardTheme

PLATFORM_LABELS: dict[ft.PagePlatform, str] = {
    ft.PagePlatform.WINDOWS: "Windows",
    ft.PagePlatform.MACOS: "macOS",
    ft.PagePlatform.LINUX: "Linux",
    ft.PagePlatform.ANDROID: "Android",
    ft.PagePlatform.ANDROID_TV: "Android TV",
    ft.PagePlatform.IOS: "iOS",
}


def _format_platforms(platforms: list[ft.PagePlatform]) -> str:
    """Devolve nomes amigáveis em sequência: 'Windows, macOS e Linux'."""
    names = [PLATFORM_LABELS.get(p, str(p)) for p in platforms]
    if len(names) <= 1:
        return names[0] if names else ""
    return ", ".join(names[:-1]) + " e " + names[-1]


def _incompatible_dialog(
    supported: list[ft.PagePlatform],
    theme: WizardTheme,
    on_bypass: Callable,
) -> ft.AlertDialog:
    """Modal de bloqueio com ícone, título, descrição e botão de bypass."""
    return ft.AlertDialog(
        modal=True,
        bgcolor=theme.surface,
        icon=ft.Text("📱", size=48, text_align=ft.TextAlign.CENTER),
        title=ft.Text(
            "Template não compatível",
            color=theme.text,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Text(
            f"Este template foi desenhado para {_format_platforms(supported)}.",
            size=13,
            color=theme.sub,
            text_align=ft.TextAlign.CENTER,
        ),
        actions=[
            ghost_button(
                "Continuar mesmo assim",
                on_bypass,
                theme.text,
                theme.border,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )


@ft.component
def PlatformGuard(
    page: ft.Page,
    supported_platforms: list[ft.PagePlatform],
    theme: WizardTheme,
    build: Callable[[], ft.Control],
) -> ft.Control:
    """Portala o modal de bloqueio se a plataforma não é suportada; senão chama `build()`."""

    bypassed, set_bypassed = ft.use_state(False)
    supported = page.platform in supported_platforms

    if supported or bypassed:
        ft.use_dialog(None)
        return build()

    dialog = _incompatible_dialog(
        supported_platforms,
        theme,
        on_bypass=lambda _e: set_bypassed(True),
    )
    ft.use_dialog(dialog)

    return ft.Container(expand=True, bgcolor=theme.bg)
