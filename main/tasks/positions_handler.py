from celery import shared_task

from .close_position import close_position
from .create_position import create_position
from ..models.hedge_logs import STATUS_ERROR, STATUS_SUCCESS
from ..models import HedgeLog, Position, Preorder


@shared_task
def positions_handler(
        sell: bool = True,
        buy: bool = False,
        auto: bool = True,
        preorder_id=None,
        position_id=None,
        manual_sum_btc=None,
):
    if preorder_id is not None:
        preorder_instance = Preorder.objects.get(id=preorder_id)
    else:
        preorder_instance = None
    log = HedgeLog(
        preorder=preorder_instance,
        origin="positions_handler START",
        status=STATUS_SUCCESS,
        text=f"Starting on: sell = {sell}, buy = {buy}, "
             f"auto = {auto}, preorder_id = {preorder_id}, "
             f"position_id = {position_id}, manual_sum_btc = {manual_sum_btc}"
    )
    log.save()

    def exit_log():
        log = HedgeLog(
            preorder=preorder_instance,
            origin="positions_handler START",
            status=STATUS_ERROR,
            text=f"Couln't start with those args"
        )
        log.save()

    if buy is True and position_id is None or \
            auto is False and sell is True and manual_sum_btc is None or \
            auto is True and preorder_id is None or \
            buy == sell:
        exit_log()
        return
    if auto is True:
        sum_btc = preorder_instance.sum_btc
        if sell is True and buy is False:
            create_position.delay(sum_btc=sum_btc, preorder_id=preorder_id)
        elif buy is True and sell is False and position_id is not None:
            close_position.delay(sum_btc=sum_btc, position_id=position_id, preorder_id=preorder_id)
        else:
            exit_log()
    elif auto is False:
        if sell is True and buy is False:
            create_position.delay(sum_btc=manual_sum_btc)
        elif buy is True and sell is False and position_id is not None:
            sum_btc = Position.objects.get(id=position_id).btc_quantity
            close_position.delay(sum_btc=sum_btc, position_id=position_id)
        else:
            exit_log()
    else:
        exit_log()
