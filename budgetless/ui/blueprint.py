import sqlite3
from flask import Flask, Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app

import datetime
from .plots import plot_spending
from ..util import current_date

blueprint = Blueprint('simple_page', __name__, template_folder='templates')

@blueprint.route('/ajax/set_transaction_props', methods=['POST'])
def transaction_props():
    id = int(request.form['id'])

    d = {}
    if 'onbudget' in request.form:
        onbudget = request.form['onbudget']
        if onbudget == 'true':
            d['onbudget'] = 1
        elif onbudget == 'reset':
            d['onbudget'] = None
        else:
            d['onbudget'] = 0
    if 'notes' in request.form:
        d['notes'] = request.form['notes']
    if 'category' in request.form:
        d['category'] = request.form['category']
    current_app.config['budget'].transactions.update_transaction(id, **d)
    return ''

@blueprint.route('/ajax/sync_status', methods=['GET', 'POST'])
def sync():
    if request.method == 'POST':
        current_app.config['budget'].sync(force=True)

    return render_template('panel/sync_status.html',
                           sync_last=get_offset_time(current_app.config['budget'].config.get('sync.last'),  int(request.args.get('tzoffset', 0)))
                           )

@blueprint.route('/ajax/categories')
def categories():
    budget = current_app.config['budget']
    categories = budget.transactions.retrieve_categories()

    return '[' + ','.join(['{"name":"%s"}' % category.replace('"', '\\"') for category in categories if category is not None]) + ']'

def get_offset_time(dt, tzoffset):
    return dt - datetime.timedelta(minutes=tzoffset)

@blueprint.route('/panel/week_list/<year>')
def panel_week_list(year):

    budget = current_app.config['budget']
    year = int(year)

    status = {}
    month_surplus = {}

    now = current_date()

    for week, stats in budget.analysis.yearly_week_stats(year):
        if len(stats) == 0:
            status[week.month] = status.get(week.month,[]) + \
                [{
                    'count': 0,
                    'surplus': 0,
                    'past': now > week,
                    'start': week
                }]

            month_surplus[week.month] = month_surplus.get(week.month,0)
        else:
            status[week.month] = status.get(week.month,[]) + \
                [{
                    'count': stats['count'],
                    'surplus': stats['surplus'],
                    'past': now > week,
                    'start': week
                }]

            month_surplus[week.month] = month_surplus.get(week.month,0) + stats.surplus.sum()

    return render_template(
        'panel/weeklist.html',
        year=year,
        months=budget.MONTHS,
        month_surplus=month_surplus,
        week_status=status
        )

@blueprint.route('/panel/week_chart/<date>')
def panel_week_chart(date):
    budget = current_app.config['budget']
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    return plot_spending(budget, start=date.date(), end=(date+datetime.timedelta(7)).date())

@blueprint.route('/panel/transactions/<date>')
def panel_transactions(date):
    budget = current_app.config['budget']
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    df = budget.analysis.transactions(start_date=date, end_date=date, date_seen=True)
    if len(df) > 0:
        df['onbudget_nondefault'] = ~df['onbudget'].isnull()

    return render_template('panel/transactions.html', df=df, date=date)

@blueprint.route('/', defaults={'date': None, 'weekstart': 2})
@blueprint.route('/chart/<date>', defaults={'weekstart': 2})
@blueprint.route('/chart/<date>/<int:weekstart>')
def main(date, weekstart):

    budget = current_app.config['budget']

    if date is None:
        date = datetime.datetime.utcnow()
    else:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    # shift date to nearest week
    date -= datetime.timedelta((date.weekday() - weekstart) % 7)

    return render_template(
        'main.html',
        js_week_start=(budget.config.get('week_start', budget.DEFAULT_WEEK_START)+1)%7,
        date=date.date(),
        year=date.year)
