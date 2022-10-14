"""Shortcuts for Material Design Dashboards"""

from dash import html


def PageGrid(children, **kwargs):
    return html.Div(children, className="mdc-layout-grid vf-page__grid", **kwargs)


def InnerGrid(children, **kwargs):
    return html.Div(children, className="mdc-layout-grid__inner vf-page__grid-inner", **kwargs)


def InnerRow(children, **kwargs):
    return html.Div(children, className="mdc-layout-grid__inner vf-page__grid-inner", style={'margin-bottom': '20px'}, **kwargs)


def Span(children, desktop=12, tablet=8, mobile=4, **kwargs):
    class_name = (
        f"mdc-layout-grid__cell mdc-layout-grid__cell--span-{desktop}-desktop "
        f"mdc-layout-grid__cell--span-{tablet}-tablet mdc-layout-grid__cell--span-{mobile}-phone"
    )

    return html.Div(
        children=children,
        className=class_name,
        **kwargs
    )


def Span2(children, **kwargs):
    return Span(children, desktop=2, **kwargs)


def Span3(children, **kwargs):
    return Span(children, desktop=3, **kwargs)


def Span4(children, **kwargs):
    return Span(children, desktop=4, **kwargs)


def Span5(children, **kwargs):
    return Span(children, desktop=5, **kwargs)


def Span6(children, **kwargs):
    return Span(children, desktop=6, **kwargs)


def Span7(children, **kwargs):
    return Span(children, desktop=7, **kwargs)


def Span8(children, **kwargs):
    return Span(children, desktop=8, **kwargs)


def Span9(children, **kwargs):
    return Span(children, desktop=9, **kwargs)


def Span10(children, **kwargs):
    return Span(children, desktop=10, **kwargs)


def Span11(children, **kwargs):
    return Span(children, desktop=11, **kwargs)


def Span12(children, **kwargs):
    return Span(children, desktop=12, **kwargs)


def Card(value_id=None, title=None, icon=None, color=None):
    return html.Div([
        html.H6([
            html.I([icon], className="material-icons"),
            title,
        ], className="mdc-typography mdc-typography--headline6 vf-badge__header"),
        html.Span(className="mdc-typography vf-badge__value", id=value_id),
    ], className="mdc-card mdc-card--outlined vf-badge", style={'background-color': color})
