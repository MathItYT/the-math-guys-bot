from sympy.plotting import (
    plot,
    plot_parametric,
    plot_implicit,
    plot3d,
    plot3d_parametric_line,
    plot3d_parametric_surface
)
from sympy.plotting.plot import Plot
from sympy import Expr
from sympy.parsing.latex import parse_latex
from typing import Optional
from io import BytesIO


def simplify_expr(expr: Expr) -> Expr:
    """
    Simplify an expression.

    :param expr: The expression to simplify.
    :return: The simplified expression.
    """
    return expr.doit()


def make_single_plot(
    expr: Expr,
    xlim: tuple = (-10, 10),
    ylim: tuple = (-10, 10),
    line_color: str = "blue",
    show: bool = True,
    legend: bool = False
) -> Plot:
    """
    Make a single plot of an expression.

    :param expr: The expression to plot.
    :param xlim: The x range to plot the expression in.
    :param ylim: The y range to plot the expression in.
    :param line_color: The color of the line to plot.
    :param show: Whether to show the plot or not.
    :param legend: Whether to show the legend or not.
    :return: The path to the image of the plot.
    """
    expr = simplify_expr(expr)
    if list(map(str, expr.free_symbols)) == ["x"]:
        return plot(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    if list(map(str, expr.free_symbols)) == ["x", "y"] and expr.is_Equality:
        return plot_implicit(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    if list(map(str, expr.free_symbols)) == ["u"] and expr.is_Vector and len(expr.components) == 2:
        return plot_parametric(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    if list(map(str, expr.free_symbols)) == ["x", "y"]:
        return plot3d(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    if list(map(str, expr.free_symbols)) == ["u"] and expr.is_Vector and len(expr.components) == 3:
        return plot3d_parametric_line(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    if list(map(str, expr.free_symbols)) == ["u", "v"] and expr.is_Vector and len(expr.components) == 3:
        return plot3d_parametric_surface(
            expr,
            xlim=xlim,
            ylim=ylim,
            line_color=line_color,
            show=show,
            legend=legend
        )
    raise ValueError("No se pudo graficar la función.")


def plot_expression(
    *latex_strings: str,
    x_range: tuple = (-10, 10),
    y_range: tuple = (-10, 10),
    colors: Optional[list[str]] = None,
) -> BytesIO:
    """
    Plot an expression in the given range.

    :param latex_str: The latex string of the expression to plot.
    :param x_range: The x range to plot the expression in.
    :param y_range: The y range to plot the expression in.
    :return: The path to the image of the plot.
    """
    try:
        colors = colors or len(latex_strings) * ("blue",)
        p = make_single_plot(
            parse_latex(latex_strings[0]),
            xlim=x_range,
            ylim=y_range,
            line_color=colors[0],
            show=False,
            legend=True
        )
        for expr, color in zip(latex_strings[1:], colors[1:]):
            p.append(
                make_single_plot(
                    parse_latex(expr),
                    xlim=x_range,
                    ylim=y_range,
                    line_color=color,
                    show=False,
                    legend=True
                )[0]
            )

    except Exception as e:
        return e

    img = BytesIO()
    p.save(img)
    img.seek(0)
    return img
