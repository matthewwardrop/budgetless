import numpy as np
import pandas as pd
import datetime

from ..util import get_date_range

def plot_spending(budget, start=None, end=None):
    # These are slow to import, so include them here, so that they are
    # only loaded if necessary.
    import plotly.graph_objs as go
    import plotly.offline as py

    df = budget.analysis.onbudget_transactions(start, end)

    if len(df) == 0:
        return

    amounts = df.groupby('date_ref').sum()['amount'].apply(lambda x: -float(x)/100)

    pamounts = df[df.pending == True].groupby('date_ref').sum()['amount'].apply(lambda x: -float(x)/100)

    min_date = min(amounts.index)
    max_date = max(amounts.index)

    daily_amount = budget.allocations.get_daily_surplus()

    dates = get_date_range(start_date=min_date, end_date=max_date, inclusive=True)
    famounts = [amounts[date] if date in amounts.index else 0 for date in dates]
    pamounts = [pamounts[date] if date in pamounts.index else 0 for date in dates]

    series = pd.Series(famounts, index=dates)
    pseries = pd.Series(pamounts, index=dates)
    if start is not None:
        series = series[series.index >= start]
        pseries = pseries[pseries.index >= start]
    if end is not None:
        series = series[series.index < end]
        pseries = pseries[pseries.index < end]

    drange = get_date_range(start, end)
    pad = [0] * (len(drange) - len(series))

    date_format = lambda ds: [d.strftime('%A') for d in ds]

    trend = (series.cumsum() / pd.Series(np.arange(1, len(series)+1), series.index))
    trace1 = go.Bar(
        x=drange,
        y=list(series-pseries)+pad,
        name='Daily Spending',
        text = date_format(drange)
    )
    trace15 = go.Bar(
        x=drange,
        y=list(pseries)+pad,
        name='Pending'
    )
    trace2 = go.Scatter(
        x=trend.index,
        y=trend,
        name='Average Daily Spending'
    )
    trace3 = go.Scatter(
        x=trend.index,
        y=[daily_amount]*len(trend),
        name='Available daily Income')
    data = [trace1, trace15, trace2, trace3]
    layout = go.Layout(
            margin=go.Margin(
                l=50,
                r=50,
                b=50,
                t=0,
                pad=0
            ),
            barmode='stack',
            legend=go.Legend(
                x=0,     # set legend x position in norm. plotting area coord.
                y=1,     # set legend y postion in " " " "
                yanchor='top',   # y position corresp. to middle of text
                bgcolor='rgba(255,255,255,0.7)',
            ),
        )
    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
    return plot_url
