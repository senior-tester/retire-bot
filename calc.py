from inflation import get_total_inflation_rate


def calculate(start_age, retire_age, invest_start, annual_invest, annual_retired_expenses, risk_level):
    profit_percent = 10 if risk_level == 'Высокий 10%' else 7.5 if risk_level == 'Средний 7.5%' else 5 if risk_level == 'Низкий 5%' else 1
    max_years = 100
    inflation = get_total_inflation_rate(days=365)
    invest_account = 0 + invest_start
    profit = profit_percent / 100
    loss = inflation / 100
    empty = ' '

    lines = ['=' * 39, '| Лет |   на счету    |     траты     |', '=' * 39]
    for year in range(start_age, retire_age):
        invest_account_str = f'{round(invest_account):,}'
        lines.append(f'| <b>{year:3}</b> | {"$" + invest_account_str:13} | {empty:13} |')
        invest_account += annual_invest + (invest_account * profit) - (invest_account * loss)

    for year in range(retire_age, max_years):
        invest_account += (invest_account * profit) - (invest_account * loss) - annual_retired_expenses
        invest_account_str = f'{round(invest_account):,}'
        annual_retired_expenses_str = f'{round(annual_retired_expenses):,}'
        lines.append(f'| {year:3} | {"$" + invest_account_str:13} | {"$" + annual_retired_expenses_str:13} |')
        annual_retired_expenses += annual_retired_expenses * loss

    lines.append('=' * 39)
    return lines



