import sqlite3
from flask import Flask, Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app

import datetime
from ..budget import Budget, \
    get_weeks_status, MONTHS

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
    current_app.config['budget'].transactions.update_transaction(id, **d)
    return ''

@blueprint.route('/ajax/sync_status', methods=['GET', 'POST'])
def sync():
    if request.method == 'POST':
        current_app.config['budget'].sync(force=True)

    ds_sync = current_app.config['budget'].config.get('sync.last')
    delta = datetime.timedelta(minutes=int(request.args.get('offset', 0)))

    return render_template('panel/sync_status.html',
                           sync_last=ds_sync - delta
                           )

@blueprint.route('/panel/<panel>')
def panel(panel):
    if panel == 'week_list':
        year = int(request.args.get('year', datetime.datetime.now().year))
        week_status = get_weeks_status(year, 2)
        return render_template(
            'panel/weeklist.html',
            year=year,
            months=MONTHS,
            week_status=week_status
            )
    if panel == 'week_chart':
        date = datetime.datetime.strptime(request.args.get('date'), '%Y-%m-%d')
        return current_app.config['budget'].plot_new(start=date, end=date+datetime.timedelta(7))
    if panel == 'day_transactions':

        date = datetime.datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()

        df = current_app.config['budget'].transactions.retrieve_df(start_date=date, end_date=date)
        if len(df) > 0:
            df['onbudget_nondefault'] = ~df['onbudget'].isnull()
            df['onbudget'] = Budget().onbudget(df)

        return render_template('panel/transactions.html', df=df, date=date)


@blueprint.route('/', defaults={'date': None, 'weekstart': 2})
@blueprint.route('/chart/<date>', defaults={'weekstart': 2})
@blueprint.route('/chart/<date>/<int:weekstart>')
def main(date, weekstart):

    if date is None:
        date = datetime.datetime.now().date()
        date = datetime.datetime.combine(date, datetime.time())

    else:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    # shift date to nearest week
    date -= datetime.timedelta((date.weekday() - weekstart) % 7)

    return render_template(
        'main.html',
        date=date.date(),
        year=date.year)
