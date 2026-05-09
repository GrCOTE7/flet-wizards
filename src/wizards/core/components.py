"""Primitivas de UI compartilhadas por todos os wizards.

Funções puras que recebem cores de tema e devolvem controles Flet.
Não dependem de estado observável — quem renderiza decide quando
recriar essas primitivas em resposta a mudanças.

Mantém as assinaturas e o visual idênticos aos do `docs/reference/wizard.py`,
exceto por:
- `primary_button` agora aceita `loading_label` configurável
  (o reference tinha "Criando..." hardcoded, inadequado para uma lib).
"""

from typing import Callable

import flet as ft


def divider(color: str) -> ft.Container:
    """Linha horizontal de 1px na cor informada."""
    return ft.Container(height=1, bgcolor=color)


def ghost_button(
    label: str,
    on_tap: Callable,
    color: str,
    border: str,
) -> ft.GestureDetector:
    """Botão secundário com borda — usado em ações neutras (Voltar, Cancelar)."""
    return ft.GestureDetector(
        on_tap=on_tap,
        content=ft.Container(
            content=ft.Text(label, size=13, color=color, weight=ft.FontWeight.W_500),
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border_radius=8,
            border=ft.Border.all(1, border),
        ),
    )


def primary_button(
    label: str,
    on_tap: Callable,
    color: str,
    loading: bool = False,
    loading_label: str = "Carregando...",
) -> ft.GestureDetector:
    """Botão primário com estado opcional de loading (ProgressRing + label)."""
    content = (
        ft.Row(
            [
                ft.ProgressRing(width=13, height=13, stroke_width=2, color="#FFFFFF"),
                ft.Container(width=8),
                ft.Text(
                    loading_label,
                    size=13,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=0,
            tight=True,
        )
        if loading
        else ft.Text(label, size=13, color="#FFFFFF", weight=ft.FontWeight.BOLD)
    )
    return ft.GestureDetector(
        on_tap=on_tap,
        content=ft.Container(
            content=content,
            bgcolor=color,
            padding=ft.Padding.symmetric(horizontal=24, vertical=10),
            border_radius=8,
            opacity=0.65 if loading else 1.0,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT_CUBIC),
        ),
    )


def form_field(
    label: str,
    value: str,
    on_change: Callable,
    hint: str,
    primary: str,
    text: str,
    sub: str,
    card: str,
    border: str,
    multiline: bool = False,
    password: bool = False,
    can_reveal_password: bool = False,
) -> ft.Column:
    """Campo de formulário com label em caps + TextField estilizado.

    Parâmetros `password` e `can_reveal_password` adicionados para suportar
    wizards de auth sem precisar duplicar a estrutura visual.
    """
    return ft.Column(
        [
            ft.Text(
                label,
                size=11,
                color=sub,
                weight=ft.FontWeight.W_500,
                style=ft.TextStyle(letter_spacing=0.8),
            ),
            ft.Container(height=6),
            ft.TextField(
                value=value,
                on_change=on_change,
                border_color=border,
                focused_border_color=primary,
                color=text,
                bgcolor=card,
                border_radius=8,
                multiline=multiline,
                min_lines=3 if multiline else 1,
                max_lines=4 if multiline else 1,
                height=None if multiline else 44,
                content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                hint_text=hint,
                hint_style=ft.TextStyle(color=sub, size=13),
                text_size=14,
                cursor_color=primary,
                password=password,
                can_reveal_password=can_reveal_password,
            ),
        ],
        spacing=0,
    )
