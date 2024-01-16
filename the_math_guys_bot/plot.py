from sympy.plotting import plot
from sympy.parsing.latex import parse_latex
from io import BytesIO


def plot_expression(
    latex_str: str,
    x_range: tuple = (-10, 10),
    y_range: tuple = (-10, 10),
    color: str = 'blue',
    variable: str = 'x',
    f_label: str = 'f'
) -> BytesIO:
    """
    Plot an expression in the given range.

    :param latex_str: The latex string of the expression to plot.
    :param x_range: The x range to plot the expression in.
    :param y_range: The y range to plot the expression in.
    :return: The path to the image of the plot.
    """
    try:
        p = plot(
            parse_latex(latex_str),
            xlim=x_range,
            ylim=y_range,
            show=False,
            legend=True,
            line_color=color,
            title=f"Plot of $\displaystyle {latex_str}$",
            xlabel='x',
            ylabel=f'{f_label}({variable})'
        )
    except Exception as e:
        return e
    img = BytesIO()
    p.save(img, format='png')
    img.seek(0)
    return img
