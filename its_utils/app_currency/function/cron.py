from its_utils.app_currency.models import ExchangeRate
from settings import ilogger


def load_exchange_rates():
    try:
        updated_date = ExchangeRate.fill_latest()

    except Exception as exc:
        ilogger.error('load_exchange_rates_error', str(exc))
        return 'Error! {}'.format(exc)

    return updated_date.isoformat() if updated_date else 'Nothing to update'
