"""Helpers de feedback visual via `ft.SnackBar` portado por `ft.use_dialog()`.

API imperativa (`show_success`, `show_error`, `show_info`) que atualiza
um controller observável global. O `SnackHost` (também daqui) deve ser
montado uma única vez no topo do app — ele lê o controller e portala
o snack ativo via `ft.use_dialog()` reativamente.

Por que o controller intermediário: `ft.use_dialog` é hook, só roda
dentro de `@ft.component`. Sem o controller, chamadas vindas de
handlers async, callbacks de wizard ou código fora de componentes
não conseguiriam disparar feedback. O controller observável faz a
ponte: `show_*` atualiza estado, `SnackHost` reage e portala.

Divergência vs CLAUDE.md: os helpers NÃO recebem `page` — `ft.use_dialog`
do `SnackHost` já portala para o overlay da página corrente.
"""

from dataclasses import dataclass

import flet as ft

_BG: dict[str, str] = {
    "success": "#22C55E",
    "error": "#EF4444",
    "info": "#3B82F6",
}


@ft.observable
@dataclass
class _SnackController:
    """Store reativo do snack atualmente exibido."""

    message: str = ""
    kind: str = "info"
    nonce: int = 0

    def show(self, message: str, kind: str) -> None:
        self.message = message
        self.kind = kind
        self.nonce += 1

    def clear(self) -> None:
        self.message = ""


_controller = _SnackController()


def show_success(message: str) -> None:
    """Mostra snack verde de sucesso."""
    _controller.show(message, "success")


def show_error(message: str) -> None:
    """Mostra snack vermelho de erro."""
    _controller.show(message, "error")


def show_info(message: str) -> None:
    """Mostra snack azul informativo."""
    _controller.show(message, "info")


@ft.component
def SnackHost() -> ft.Control:
    """Mount-once host que portala o snack ativo via `ft.use_dialog()`.

    Reativo ao `_controller`: cada `show_*` dispara re-render aqui,
    que então portala um novo `SnackBar` ao overlay da página.
    `nonce` garante re-render mesmo quando a mensagem é repetida.
    """

    msg = _controller.message
    kind = _controller.kind
    _ = _controller.nonce

    if msg:
        snack = ft.SnackBar(
            content=ft.Text(
                msg,
                color="#FFFFFF",
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=_BG.get(kind, _BG["info"]),
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
            close_icon_color="#FFFFFF",
            on_dismiss=lambda _e: _controller.clear(),
        )
        ft.use_dialog(snack)
    else:
        ft.use_dialog(None)

    return ft.Container(width=0, height=0)
