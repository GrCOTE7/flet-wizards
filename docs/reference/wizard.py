"""
Flet Multi-Step Wizard — Template de portfólio
===============================================
Um template moderno de wizard multi-step em Python com Flet,
demonstrando estado reativo, async e UI profissional.

Padrões técnicos centrais:
  - @ft.observable + @dataclass como store reativo (sem page.update() manual)
  - ft.use_state para estado local de componente
  - Padrão híbrido: estado local sincronizado com estado global
  - AnimatedSwitcher + key=str(state.step) para transições corretas

Estrutura:
  1. Tema e paleta de cores (THEMES)
  2. AppState — store reativo central
  3. Utilitários de UI
  4. Componentes: Sidebar, Steps, NavBar, StepSuccess
  5. Wizard — orquestrador principal
  6. Entrypoint
"""

from dataclasses import dataclass
import asyncio
import flet as ft

# ── Constantes de layout ──────────────────────────────────────────────────────

WIN_W = 1040
WIN_H = 660
SIDE_W = 272

# ── Sistema de temas ──────────────────────────────────────────────────────────

THEMES: dict[str, dict[str, str]] = {
    "Slate": {
        "primary": "#7C6EF6",
        "secondary": "#A89EFA",
        "accent": "#38BDF8",
        "bg": "#0B0B0F",
        "surface": "#111118",
        "card": "#17171F",
        "panel": "#141420",
        "border": "#222230",
        "text": "#F0EEF8",
        "sub": "#6B6880",
    },
    "Emerald": {
        "primary": "#34D399",
        "secondary": "#6EE7B7",
        "accent": "#60A5FA",
        "bg": "#090E0C",
        "surface": "#0E1610",
        "card": "#121C14",
        "panel": "#101810",
        "border": "#1C2E1E",
        "text": "#ECFDF5",
        "sub": "#4A7060",
    },
    "Rose": {
        "primary": "#F472B6",
        "secondary": "#FBCFE8",
        "accent": "#FB923C",
        "bg": "#0E090C",
        "surface": "#170E12",
        "card": "#1C1016",
        "panel": "#180E14",
        "border": "#2C1820",
        "text": "#FDF2F8",
        "sub": "#7A3C58",
    },
    "Azure": {
        "primary": "#60A5FA",
        "secondary": "#93C5FD",
        "accent": "#A78BFA",
        "bg": "#080B10",
        "surface": "#0D1018",
        "card": "#12161E",
        "panel": "#0F1420",
        "border": "#1C2236",
        "text": "#EFF6FF",
        "sub": "#3C5070",
    },
}

# ── Store reativo ─────────────────────────────────────────────────────────────


@ft.observable
@dataclass
class AppState:
    """
    Store reativo central do wizard.

    @ft.observable transforma esta dataclass em um publisher: qualquer
    componente que receba `state` como argumento é automaticamente
    re-renderizado quando um campo muda — sem page.update() manual.

    Campos de navegação (step, loading) são separados dos dados do formulário
    (name, description, theme, project_type) para deixar claro o que é
    fluxo de controle e o que é conteúdo do usuário.
    """

    step: int = 0
    loading: bool = False

    name: str = ""
    description: str = ""
    theme: str = "Slate"
    project_type: str = "Analytics"

    def go_next(self) -> None:
        if self.step < 3:
            self.step += 1

    def go_back(self) -> None:
        if self.step > 0:
            self.step -= 1

    def reset(self) -> None:
        self.step = 0
        self.loading = False
        self.name = ""
        self.description = ""
        self.theme = "Slate"
        self.project_type = "Analytics"

    def t(self) -> dict[str, str]:
        return THEMES.get(self.theme, THEMES["Slate"])

    def primary(self) -> str:
        return self.t()["primary"]

    def secondary(self) -> str:
        return self.t()["secondary"]

    def accent(self) -> str:
        return self.t()["accent"]

    def bg(self) -> str:
        return self.t()["bg"]

    def surface(self) -> str:
        return self.t()["surface"]

    def card(self) -> str:
        return self.t()["card"]

    def panel(self) -> str:
        return self.t()["panel"]

    def border(self) -> str:
        return self.t()["border"]

    def text(self) -> str:
        return self.t()["text"]

    def sub(self) -> str:
        return self.t()["sub"]


# ── Utilitários de UI ─────────────────────────────────────────────────────────


def divider(color: str) -> ft.Container:
    return ft.Container(height=1, bgcolor=color)


def ghost_button(label: str, on_tap, color: str, border: str) -> ft.GestureDetector:
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
    on_tap,
    color: str,
    loading: bool = False,
) -> ft.GestureDetector:
    content = (
        ft.Row(
            [
                ft.ProgressRing(width=13, height=13, stroke_width=2, color="#FFFFFF"),
                ft.Container(width=8),
                ft.Text(
                    "Criando...", size=13, color="#FFFFFF", weight=ft.FontWeight.BOLD
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
    on_change,
    hint: str,
    primary: str,
    text: str,
    sub: str,
    card: str,
    border: str,
    multiline: bool = False,
) -> ft.Column:
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
            ),
        ],
        spacing=0,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────


@ft.component
def Sidebar(state: AppState) -> ft.Control:
    """
    Sidebar fixa com navegação visual dos steps.

    O indicador lateral (barra vertical colorida) usa animate_opacity
    em vez de visibilidade booleana — evita saltos de layout.
    O conector entre steps muda de cor conforme o progresso avança,
    usando animate para transição suave.
    """

    P = state.primary()
    T = state.text()
    S = state.sub()
    B = state.border()

    is_done = state.step == 3

    STEPS = [
        ("Projeto", "Nome e descrição"),
        ("Aparência", "Tema e cores"),
        ("Confirmar", "Revisar e criar"),
    ]

    def step_row(i: int, title: str, hint: str) -> ft.Column:
        done = state.step > i
        active = state.step == i and not is_done

        circle = ft.Container(
            content=ft.Text(
                "✓" if done else str(i + 1),
                size=10,
                color="#FFFFFF" if (done or active) else S,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            width=28,
            height=28,
            border_radius=14,
            bgcolor=P if (done or active) else "transparent",
            border=ft.Border.all(1, P if (done or active) else B),
            alignment=ft.Alignment(0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        indicator = ft.Container(
            width=3,
            height=32,
            bgcolor=P,
            border_radius=2,
            opacity=1.0 if active else 0.0,
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        labels = ft.Column(
            [
                ft.Text(
                    title,
                    size=13,
                    color=T if active else (state.secondary() if done else S),
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                ),
                ft.Text(hint, size=11, color=S),
            ],
            spacing=1,
        )

        connector = (
            ft.Container(
                margin=ft.Margin(17, 0, 0, 0),
                width=1,
                height=24,
                bgcolor=P if done else B,
                animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT_CUBIC),
            )
            if i < len(STEPS) - 1
            else ft.Container(height=0)
        )

        return ft.Column(
            [
                ft.Row(
                    [
                        indicator,
                        ft.Container(width=10),
                        circle,
                        ft.Container(width=12),
                        labels,
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                connector,
            ],
            spacing=0,
        )

    pct = 100 if is_done else int((state.step / 2) * 100)
    bar_w = SIDE_W - 48

    logo = ft.Container(
        content=ft.Image(
            src="logo.png",
            fit=ft.BoxFit.CONTAIN,
            width=120,
        ),
        alignment=ft.Alignment.CENTER,
    )
    
    progress_bar = ft.Container(
        height=3,
        bgcolor=B,
        border_radius=2,
        content=ft.Container(
            width=max(4, bar_w * pct / 100),
            height=3,
            bgcolor=P,
            border_radius=2,
            animate=ft.Animation(450, ft.AnimationCurve.EASE_OUT_CUBIC),
        ),
        alignment=ft.Alignment(-1, 0),
    )

    return ft.Container(
        width=SIDE_W,
        bgcolor=state.panel(),
        padding=ft.Padding.symmetric(horizontal=24, vertical=28),
        border_radius=ft.BorderRadius.only(top_left=12, bottom_left=12),
        content=ft.Column(
            [
                logo,
                ft.Container(height=36),
                *[step_row(i, t, h) for i, (t, h) in enumerate(STEPS)],
                ft.Container(expand=1),
                divider(B),
                ft.Container(height=14),
                ft.Row(
                    [
                        ft.Text("Progresso", size=10, color=S),
                        ft.Container(expand=1),
                        ft.Text(f"{pct}%", size=10, color=P, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Container(height=6),
                progress_bar,
                ft.Container(height=16),
            ],
            spacing=0,
            expand=True,
        ),
    )


# ── Step 1 — Informações do projeto ──────────────────────────────────────────


@ft.component
def Step1(state: AppState) -> ft.Control:
    """
    Formulário de configuração inicial do projeto.

    Demonstra o padrão híbrido de estado:
      - ft.use_state controla o valor local do campo (re-renderiza o TextField)
      - state.name sincroniza o valor global (persiste entre steps)

    Sem os dois juntos, ou o campo não atualiza visualmente,
    ou o valor se perde ao navegar para outro step.
    """

    P = state.primary()
    T = state.text()
    S = state.sub()
    B = state.border()
    C = state.card()

    name_v, set_name = ft.use_state(state.name)
    desc_v, set_desc = ft.use_state(state.description)
    type_v, set_type = ft.use_state(state.project_type)

    def on_name(e):
        set_name(e.control.value)
        state.name = e.control.value

    def on_desc(e):
        set_desc(e.control.value)
        state.description = e.control.value

    def pick_type(label: str):
        set_type(label)
        state.project_type = label

    TYPES = [
        ("📊", "Analytics"),
        ("💸", "Financeiro"),
        ("🛒", "E-commerce"),
        ("👥", "CRM"),
        ("📦", "Operações"),
        ("🔐", "Segurança"),
    ]

    def type_chip(icon: str, label: str) -> ft.GestureDetector:
        sel = type_v == label
        return ft.GestureDetector(
            on_tap=lambda _, l=label: pick_type(l),
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Text(icon, size=12),
                        ft.Text(
                            label,
                            size=12,
                            color="#FFFFFF" if sel else S,
                            weight=ft.FontWeight.W_600 if sel else ft.FontWeight.W_400,
                        ),
                    ],
                    spacing=6,
                    tight=True,
                ),
                bgcolor=P if sel else C,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                border_radius=20,
                border=ft.Border.all(1, P if sel else B),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT_CUBIC),
            ),
        )

    chip_rows = [TYPES[:3], TYPES[3:]]
    shared = dict(primary=P, text=T, sub=S, card=C, border=B)

    return ft.Column(
        [
            ft.Text(
                "Configure seu projeto", size=22, weight=ft.FontWeight.BOLD, color=T
            ),
            ft.Container(height=4),
            ft.Text(
                "Preencha as informações base. Você pode editar depois.",
                size=13,
                color=S,
            ),
            ft.Container(height=28),
            form_field(
                "NOME DO PROJETO", name_v, on_name, "Ex: Analytics Pro", **shared
            ),
            ft.Container(height=18),
            form_field(
                "DESCRIÇÃO",
                desc_v,
                on_desc,
                "Qual o objetivo principal deste projeto?",
                multiline=True,
                **shared,
            ),
            ft.Container(height=22),
            ft.Text(
                "TIPO",
                size=11,
                color=S,
                weight=ft.FontWeight.W_500,
                style=ft.TextStyle(letter_spacing=0.8),
            ),
            ft.Container(height=10),
            *[
                ft.Column(
                    [
                        ft.Row([type_chip(i, l) for i, l in row], spacing=8),
                        ft.Container(height=8),
                    ],
                    spacing=0,
                )
                for row in chip_rows
            ],
        ],
        spacing=0,
    )


# ── Step 2 — Identidade visual ────────────────────────────────────────────────


@ft.component
def Step2(state: AppState) -> ft.Control:
    """Seleção de tema com preview visual de cada paleta."""

    T = state.text()
    S = state.sub()
    B = state.border()
    C = state.card()

    def pick_theme(name: str):
        state.theme = name

    def theme_card(name: str) -> ft.GestureDetector:
        t = THEMES[name]
        sel = state.theme == name
        P = t["primary"]

        color_dots = ft.Row(
            [
                ft.Container(width=8, height=8, bgcolor=t["primary"], border_radius=4),
                ft.Container(
                    width=8, height=8, bgcolor=t["secondary"], border_radius=4
                ),
                ft.Container(width=8, height=8, bgcolor=t["accent"], border_radius=4),
                ft.Container(expand=1),
                ft.Container(
                    content=ft.Text(
                        "✓", size=9, color="#FFF", weight=ft.FontWeight.BOLD
                    ),
                    width=18,
                    height=18,
                    border_radius=9,
                    bgcolor=P,
                    alignment=ft.Alignment(0, 0),
                    animate_scale=ft.Animation(250, ft.AnimationCurve.BOUNCE_OUT),
                    scale=1.0 if sel else 0.0,
                ),
            ],
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        mini_bars = ft.Row(
            [
                ft.Container(
                    width=7,
                    height=h,
                    bgcolor=P if j % 2 == 0 else t["secondary"],
                    border_radius=ft.BorderRadius.only(top_left=3, top_right=3),
                )
                for j, h in enumerate([12, 20, 15, 26, 19, 24])
            ],
            spacing=3,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        preview = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(width=4, height=4, bgcolor=P, border_radius=2),
                            ft.Container(
                                width=16, height=3, bgcolor=P + "50", border_radius=2
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        [
                            ft.Container(
                                bgcolor=t["card"],
                                padding=ft.Padding.all(4),
                                border_radius=4,
                                expand=1,
                                content=ft.Container(
                                    height=4, bgcolor=P, border_radius=2
                                ),
                            ),
                            ft.Container(
                                bgcolor=t["card"],
                                padding=ft.Padding.all(4),
                                border_radius=4,
                                expand=1,
                                content=ft.Container(
                                    height=4, bgcolor=t["secondary"], border_radius=2
                                ),
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Container(height=6),
                    mini_bars,
                ],
                spacing=0,
            ),
            bgcolor=t["surface"],
            padding=ft.Padding.all(10),
            border_radius=8,
            height=80,
        )

        return ft.GestureDetector(
            on_tap=lambda _, n=name: pick_theme(n),
            content=ft.Container(
                content=ft.Column(
                    [
                        preview,
                        ft.Container(height=10),
                        color_dots,
                        ft.Container(height=8),
                        ft.Text(
                            name,
                            size=13,
                            color=T,
                            weight=ft.FontWeight.W_600 if sel else ft.FontWeight.W_400,
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=C,
                padding=ft.Padding.all(12),
                border_radius=10,
                border=ft.Border.all(2 if sel else 1, state.primary() if sel else B),
                animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT_CUBIC),
            ),
        )

    names = list(THEMES.keys())

    return ft.Column(
        [
            ft.Text("Identidade visual", size=22, weight=ft.FontWeight.BOLD, color=T),
            ft.Container(height=4),
            ft.Text("O tema define a paleta de todo o projeto.", size=13, color=S),
            ft.Container(height=24),
            ft.Row(
                [
                    ft.Column(
                        [
                            theme_card(names[0]),
                            ft.Container(height=12),
                            theme_card(names[2]),
                        ],
                        expand=1,
                        spacing=0,
                    ),
                    ft.Column(
                        [
                            theme_card(names[1]),
                            ft.Container(height=12),
                            theme_card(names[3]),
                        ],
                        expand=1,
                        spacing=0,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=0,
    )


# ── Step 3 — Revisão ──────────────────────────────────────────────────────────


@ft.component
def Step3(state: AppState) -> ft.Control:
    """Preview do projeto configurado antes da criação."""

    P = state.primary()
    T = state.text()
    S = state.sub()
    B = state.border()
    C = state.card()
    SX = state.surface()
    AC = state.accent()

    METRICS = [
        ("Usuários", "18.4k", "▲ 12%", "#22C55E"),
        ("Receita", "$94k", "▲  8%", "#22C55E"),
        ("Conversão", "3.2%", "▲ 0.4", "#22C55E"),
        ("Churn", "1.1%", "▼ 0.2", "#F87171"),
    ]

    BAR_DATA = [42, 68, 55, 88, 63, 45, 76]
    DAYS = ["S", "M", "T", "W", "T", "F", "S"]
    BAR_MAX = max(BAR_DATA)

    def metric_card(label: str, val: str, delta: str, dcolor: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=10, color=S),
                    ft.Text(val, size=18, weight=ft.FontWeight.BOLD, color=T),
                    ft.Text(delta, size=10, color=dcolor, weight=ft.FontWeight.W_600),
                ],
                spacing=3,
            ),
            bgcolor=C,
            padding=ft.Padding.all(14),
            border_radius=8,
            border=ft.Border.all(1, B),
            expand=1,
        )

    def bar_column(value: int, day: str) -> ft.Column:
        return ft.Column(
            [
                ft.Container(
                    content=ft.Container(
                        height=(value / BAR_MAX) * 56,
                        bgcolor=P,
                        border_radius=ft.BorderRadius.only(top_left=3, top_right=3),
                        animate=ft.Animation(500, ft.AnimationCurve.EASE_OUT_CUBIC),
                    ),
                    height=56,
                    alignment=ft.Alignment(0, 1),
                    width=20,
                ),
                ft.Text(day, size=9, color=S, text_align=ft.TextAlign.CENTER),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    type_badge = ft.Container(
        content=ft.Text(
            state.project_type, size=10, color=AC, weight=ft.FontWeight.W_600
        ),
        border=ft.Border.all(1, AC + "60"),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )

    theme_badge = ft.Container(
        content=ft.Text(state.theme, size=10, color="#FFF", weight=ft.FontWeight.BOLD),
        bgcolor=P,
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text(
                        state.name or "Sem nome",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=T,
                    ),
                    ft.Text(state.description or "Sem descrição", size=12, color=S),
                ],
                spacing=3,
                expand=1,
            ),
            ft.Row([theme_badge, type_badge], spacing=6),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    chart = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Atividade semanal",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=T,
                        ),
                        ft.Container(expand=1),
                        ft.Text("7 dias", size=10, color=S),
                    ],
                ),
                ft.Container(height=10),
                ft.Row(
                    [bar_column(v, d) for v, d in zip(BAR_DATA, DAYS)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    expand=True,
                ),
            ],
            spacing=0,
        ),
        bgcolor=SX,
        padding=ft.Padding.all(14),
        border_radius=8,
        border=ft.Border.all(1, B),
        expand=2,
    )

    integrations = ft.Container(
        content=ft.Column(
            [
                ft.Text("Integrações", size=11, weight=ft.FontWeight.W_600, color=T),
                ft.Container(height=10),
                *[
                    ft.Row(
                        [
                            ft.Container(
                                width=6, height=6, bgcolor="#22C55E", border_radius=3
                            ),
                            ft.Container(width=8),
                            ft.Text(svc, size=12, color=T),
                            ft.Container(expand=1),
                            ft.Text("Ativo", size=10, color="#22C55E"),
                        ],
                        spacing=0,
                    )
                    for svc in ["API REST", "Webhooks", "OAuth 2.0"]
                ],
            ],
            spacing=8,
        ),
        bgcolor=SX,
        padding=ft.Padding.all(14),
        border_radius=8,
        border=ft.Border.all(1, B),
        expand=1,
    )

    return ft.Column(
        [
            ft.Text("Revisar e confirmar", size=22, weight=ft.FontWeight.BOLD, color=T),
            ft.Container(height=4),
            ft.Text(
                "Confira os dados e confirme para criar o projeto.", size=13, color=S
            ),
            ft.Container(height=18),
            ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Container(height=14),
                        divider(B),
                        ft.Container(height=14),
                        ft.Row([metric_card(*m) for m in METRICS], spacing=8),
                        ft.Container(height=12),
                        ft.Row(
                            [chart, integrations],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=SX,
                padding=ft.Padding.all(18),
                border_radius=10,
                border=ft.Border.all(1, B),
            ),
        ],
        spacing=0,
    )


# ── StepSuccess ───────────────────────────────────────────────────────────────


@ft.component
def StepSuccess(state: AppState) -> ft.Control:
    """Tela de conclusão — minimalista e direta."""

    P = state.primary()
    T = state.text()
    S = state.sub()

    logo = ft.Container(
        content=ft.Image(
            src="logo.png",
            fit=ft.BoxFit.CONTAIN,
            width=180,
        ),
        alignment=ft.Alignment(0, 0),
    )
    
    return ft.Column(
        [
            ft.Container(expand=1),
            ft.Column(
                [
                    logo,
                    ft.Container(height=32),
                    ft.Text(
                        "Projeto criado com sucesso. Seu dashboard já está pronto.",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=T,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=32),
                    primary_button("Acessar dashboard", lambda _: state.reset(), P),
                    ft.Container(height=14),
                    ft.GestureDetector(
                        on_tap=lambda _: state.reset(),
                        content=ft.Text(
                            "Criar outro projeto",
                            size=13,
                            color=S,
                            weight=ft.FontWeight.W_500,
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            ft.Container(expand=1),
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )


# ── NavBar ────────────────────────────────────────────────────────────────────


@ft.component
def NavBar(state: AppState) -> ft.Control:
    """
    Barra de navegação inferior com botões Voltar e Continuar/Criar.

    O handler on_next é async para permitir a simulação de loading
    sem bloquear a UI — o ProgressRing roda enquanto o await acontece.
    Em produção, substituir asyncio.sleep pela chamada real à API.
    """

    if state.step == 3:
        return ft.Container(height=0)

    P = state.primary()
    T = state.text()
    B = state.border()
    is_last = state.step == 2

    back = (
        ghost_button("← Voltar", lambda _: state.go_back(), T, B)
        if state.step > 0
        else ft.Container()
    )

    async def on_next(_):
        if is_last:
            if state.loading:
                return
            state.loading = True
            await asyncio.sleep(1.8)
            state.loading = False
            state.step = 3
        else:
            state.go_next()

    next_label = "Criar projeto" if is_last else "Continuar →"
    nxt = primary_button(next_label, on_next, P, loading=state.loading and is_last)

    return ft.Row(
        [back, ft.Container(expand=1), nxt],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


# ── Wizard — orquestrador ─────────────────────────────────────────────────────


@ft.component
def Wizard() -> ft.Control:
    """
    Orquestrador principal do wizard.

    AnimatedSwitcher requer key=str(state.step) para funcionar corretamente.
    Sem a key, o Flet reutiliza o mesmo container entre steps e não dispara
    a animação — ele vê dados novos no mesmo elemento, não um elemento novo.
    Com a key, cada step é tratado como um componente distinto e a transição
    é executada na troca.
    """

    state, _ = ft.use_state(AppState())

    B = state.border()
    C = state.card()

    STEPS = [Step1, Step2, Step3, StepSuccess]
    Current = STEPS[min(state.step, len(STEPS) - 1)]

    show_nav = state.step < 3

    content_area = ft.AnimatedSwitcher(
        content=ft.Container(
            key=str(state.step),
            content=Current(state),
            expand=True,
        ),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=260,
        switch_in_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        switch_out_curve=ft.AnimationCurve.EASE_IN_CUBIC,
        expand=True,
    )

    panel_children = [
        ft.Container(
            content=content_area, expand=1, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
        ),
    ]

    if show_nav:
        panel_children += [
            ft.Container(height=20),
            divider(B),
            ft.Container(height=16),
            NavBar(state),
        ]

    main_panel = ft.Container(
        expand=1,
        bgcolor=C,
        padding=ft.Padding.only(left=40, right=40, top=32, bottom=28),
        border_radius=ft.BorderRadius.only(top_right=12, bottom_right=12),
        content=ft.Column(panel_children, spacing=0, expand=True),
    )

    frame = ft.Container(
        expand=True,
        border_radius=12,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, B),
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT_CUBIC),
        content=ft.Row(
            [
                Sidebar(state),
                ft.Container(width=1, bgcolor=B),
                main_panel,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        ),
    )

    return ft.Container(
        expand=True,
        bgcolor=state.bg(),
        padding=ft.Padding.symmetric(horizontal=40, vertical=32),
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT_CUBIC),
        content=frame,
    )


# ── Entrypoint ────────────────────────────────────────────────────────────────


async def main(page: ft.Page) -> None:
    page.title = "Multi-Step Wizard — Flet Template"
    page.padding = 0
    page.bgcolor = "#050508"
    page.window.width = WIN_W
    page.window.height = WIN_H
    page.window.resizable = False
    page.render(Wizard)


ft.run(main)
