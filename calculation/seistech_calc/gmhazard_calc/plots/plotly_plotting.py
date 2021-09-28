from typing import Dict, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as io


def plot_hazard(
    hazard_df: pd.DataFrame,
    title: str,
    im: str,
    nz_code_hazard: pd.Series = None,
    branch_hazard: Dict[str, pd.DataFrame] = None,
    save_file: str = None,
    output_format: str = "show",
    **kwargs,
) -> Union[None, str]:
    """
    Plots the hazard curves for the specified data

    Parameters
    ----------
    hazard_df: pd.DataFrame
        Hazard data to plot
        format: index = IM Values, columns = [fault, ds, total]
    title: str
        Title of the plot
    im: str
        IM this hazard data/plot is for
    nz_code_hazard: pd.Series, optional
        The corresponding NZ code hazard data
        format: index = exceedance values, values = IM values
    branch_hazard: dict, optional
        If the main hazard (i.e. hazard_df) is ensemble hazard, then this
        option can be used to also plot all the branches hazard in the same
        plot. If one just wants to plot the hazard for a single branch, then
        this should parameter should be None, and the dataframe passed in using
        the hazard_df parameter
        The keys of the dictionary are expected to be the branches names, and the
        values pd.Dataframe of format: index = IM values, columns = [fault, ds, total]
    save_file: str, optional
        If specified, and output format is either "html" or "png" then
        the plot is saved at the specified file location,
        otherwise setting this argument will not do anything
    output_format: str, optional
        Possible values are "show", "html", "div", "png", where:
            - "show": Displays the graph in the default browser
            - "div": Returns the plot html as a div element
            - "png": Returns the plot as a png byte string
            - "html_file": If save_file is specified, saves the plot
                as an .html file
            - "png_file": If save_file is specified, saves the plot
                as a .png file
    kwargs: dict
        Keywoard arguments for the output function
    """
    im_values = hazard_df.index.values
    data = [
        go.Scatter(
            x=im_values,
            y=hazard_df.total.values,
            name="Total",
            mode="lines",
            line=go.scatter.Line(color="blue"),
        ),
        go.Scatter(
            x=im_values,
            y=hazard_df.fault.values,
            name="Fault",
            mode="lines",
            line=go.scatter.Line(color="red"),
        ),
        go.Scatter(
            x=im_values,
            y=hazard_df.ds.values,
            name="Distributed",
            mode="lines",
            line=go.scatter.Line(color="green"),
        ),
    ]

    if nz_code_hazard is not None:
        data.append(
            go.Scatter(
                x=nz_code_hazard.values,
                y=nz_code_hazard.index.values,
                mode="lines+markers",
                name="NZ code",
                marker=go.scatter.Marker(symbol="triangle-up"),
                line=go.scatter.Line(color="black", dash="dot"),
            )
        )

    if branch_hazard is not None:
        dash_styles = ["dot", "dash", "longdash", "dashdot", "longdashdot"]
        for ix, (branch_name, branch_df) in enumerate(branch_hazard.items()):
            assert np.all(np.isclose(branch_df.index.values, im_values))
            data.extend(
                [
                    go.Scatter(
                        x=im_values,
                        y=branch_df.total.values,
                        name=f"{branch_name} - Total",
                        mode="lines",
                        visible="legendonly",
                        line=go.scatter.Line(color="blue", dash=dash_styles[ix % 5]),
                    ),
                    go.Scatter(
                        x=im_values,
                        y=branch_df.fault.values,
                        name=f"{branch_name} - Fault",
                        mode="lines",
                        visible="legendonly",
                        line=go.scatter.Line(color="red", dash=dash_styles[ix % 5]),
                    ),
                    go.Scatter(
                        x=im_values,
                        y=branch_df.ds.values,
                        name=f"{branch_name} - Distributed",
                        mode="lines",
                        visible="legendonly",
                        line=go.scatter.Line(color="green", dash=dash_styles[ix % 5]),
                    ),
                ]
            )

    fig = go.Figure(
        data=data,
        layout_title_text=title,
        layout=go.Layout(
            xaxis=go.layout.XAxis(
                type="log",
                title_text=im,
                showexponent="first",
                exponentformat="power",
                range=[np.log10(im_values.min()), np.log10(im_values.max())],
            ),
            yaxis=go.layout.YAxis(
                type="log",
                title_text="Annual rate of exceedance",
                showexponent="first",
                exponentformat="power",
                range=[np.log10(1e-5), np.log10(1)],
            ),
        ),
    )

    return _save_fig(fig, output_format, save_file, **kwargs)


def plot_uhs(
    uhs_df: pd.DataFrame,
    nz_code_uhs: pd.DataFrame = None,
    title: str = None,
    legend_excd_prob: bool = False,
    save_file: str = None,
    output_format: str = "show",
    **kwargs,
):
    """Plots the different uniform hazard spectra, also saves the
    plot if a save file is specified

    Parameters
    ----------
    uhs_df: pd.DataFrame
        The SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    nz_code_uhs: pd.DataFrame
        The NZ code SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    title: str, optional
        Title of the plot
    legend_excd_prob: bool, optional
        If set then the legend labels the lines in terms of
        exceedance probability instead of return period
    save_file: str, optional
        If specified, and output format is either "html" or "png" then
        the plot is saved at the specified file location,
        otherwise setting this argument will not do anything
    output_format: str, optional
        Possible values are "show", "html", "div", "png", where:
            - "show": Displays the graph in the default browser
            - "div": Returns the plot html as a div element
            - "png": Returns the plot as a png byte string
            - "html_file": If save_file is specified, saves the plot
                as an .html file
            - "png_file": If save_file is specified, saves the plot
                as a .png file
    kwargs: dict
        Keywoard arguments for the output function
    """

    def get_legend_label(excd_str):
        return (
            f"{float(excd_str):.4f}"
            if legend_excd_prob
            else f"{int(np.round(1 / float(excd_str)))}"
        )

    data = []
    for col_ix, col in enumerate(uhs_df.columns.values):
        data.append(
            go.Scatter(
                x=uhs_df.index.values,
                y=uhs_df.iloc[:, col_ix].values,
                name=get_legend_label(col),
                mode="lines",
            )
        )

    if nz_code_uhs is not None:
        for col_ix, col in enumerate(nz_code_uhs.columns.values):
            # Check that there are non-nan entries
            if np.count_nonzero(~np.isnan(nz_code_uhs.iloc[:, col_ix].values)) > 0:
                data.append(
                    go.Scatter(
                        x=nz_code_uhs.index.values,
                        y=nz_code_uhs.iloc[:, col_ix].values,
                        name=f"NZ code - {get_legend_label(col)}",
                        line=go.scatter.Line(color="black"),
                    )
                )

    fig = go.Figure(
        data=data,
        layout_title_text=title,
        layout=go.Layout(
            xaxis=go.layout.XAxis(title_text="Period (s)"),
            yaxis=go.layout.YAxis(title_text="SA (g)"),
        ),
    )

    return _save_fig(fig, output_format, save_file, **kwargs)


def _save_fig(fig: go.Figure, output_format: str, save_file: str, **kwargs):
    output_format = output_format.lower()
    if output_format == "div":
        return io.to_html(fig, full_html=False, include_mathjax=False, **kwargs)
    elif output_format == "png":
        return fig.to_image(format="png", **kwargs)
    elif output_format == "html_file" or output_format == "png_file":
        if save_file is None:
            raise Exception(
                f"For output format '{output_format}' the save_file "
                f"parameter has to specified."
            )

        if output_format == "png_file":
            io.write_image(fig, save_file, **kwargs)
        else:
            io.write_html(fig, save_file, **kwargs)
    else:
        fig.show(renderer="browser")
