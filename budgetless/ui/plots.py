import numpy as np
import pandas as pd
import datetime

from ..util import get_date_range, current_datetime

def plot_spending(budget, start=None, end=None):
    # These are slow to import, so include them here, so that they are
    # only loaded if necessary.

    import plotly.graph_objs as go
    import plotly.offline as py

    df = budget.analysis.daily_stats(start, end)

    if len(df) == 0:
        return "No data."

    amounts = -df['onbudget_net']
    pamounts = -df['onbudget_pending']
    daily_amount = df['available']

    drange = get_date_range(start, end, inclusive=True)
    dfinerange = get_date_range(start, end, step=datetime.timedelta(hours=1), inclusive=True)
    min_date = min(amounts.index)
    max_date = max(amounts.index)

    date_mask = 0 # (end - budget.config.get('last_sync', current_datetime()).date()).days

    dates = get_date_range(start_date=start, end_date=end, inclusive=True)
    daily_amount = [budget.allocations.get_daily_surplus(date) for date in dates]
    famounts = [amounts[date] if date in amounts.index else 0 for date in dates]
    pamounts = [pamounts[date] if date in pamounts.index else 0 for date in dates]

    series = pd.Series(famounts, index=dates)
    pseries = pd.Series(pamounts, index=dates)

    pad = [0] * (len(drange) - len(series))
    date_format = lambda ds: [d.strftime('%A') for d in ds]
    print(series.cumsum())
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
        y=daily_amount,#[:-(1+date_mask)],
        name='Available Daily Income')

    yguides = np.linspace(0, max(max(daily_amount), max(series)))
    print(daily_amount)
    print (sum(daily_amount))
    contour_gap = 50
    guides = go.Contour(
        x = trend.index,
        y = yguides,
        z = np.outer(yguides, np.arange(len(trend.index))+1),
        autocontour=False,
        contours=dict(
            start= - (sum(daily_amount) % contour_gap),
            end=sum(daily_amount),
            size=contour_gap,
            coloring='lines'
        ),
        showscale=False,
        hoverinfo='none'
    )
    data = [trace1, trace15, trace2, trace3, guides]
    #data = [guides]
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
