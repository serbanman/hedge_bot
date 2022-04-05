from celery import shared_task

from .close_position import close_position
from .create_position import create_position
from main.models.hedge_logs import STATUS_ERROR, STATUS_SUCCESS
from main.models import Position
from main.services import HedgeLogger
from main.models.positions import STATUS_CLOSED, STATUS_OPEN


@shared_task
def close_position_handler(position_id):
    position_instance = Position.objects.get(id=position_id)
    preorder_instance = position_instance.preorder
    if preorder_instance:
        preorder_id = preorder_instance.id
    else:
        preorder_id = None

    sum_btc = position_instance.sum_btc

    log = HedgeLogger(preorder_id)
    if position_instance.status == STATUS_CLOSED:
        log.log(
            origin="positions_handler START",
            status=STATUS_ERROR,
            text=f"Position already closed: position_id = {position_id}, status {position_instance.status}"
        )
        return

    log.log(
        origin="positions_handler START",
        status=STATUS_SUCCESS,
        text=f"Starting on: position_id = {position_id}, sum_btc {position_instance.sum_btc}"
    )

    close_position.delay(sum_btc=sum_btc, position_id=position_id, preorder_id=preorder_id)


@shared_task
def open_position_handler_auto(preorder_id: str):

    log = HedgeLogger(preorder_id)
    preorder_instance = log.instantiate()
    positions = preorder_instance.positions.filter(status=STATUS_OPEN)
    if positions:
        log.log(
            origin="positions_handler START",
            status=STATUS_ERROR,
            text=f"Starting on: preorder_id = {preorder_id}, open position exists: {positions}"
        )
    log.log(
        origin="positions_handler START",
        status=STATUS_SUCCESS,
        text=f"Starting on: preorder_id = {preorder_id}"
    )


    try:
        sum_btc = preorder_instance.sum_btc
        if sum_btc <= 0:
            raise ValueError(f'Ambiguous sum btc: {sum_btc}')
    except Exception as ex:
        log.log(
            origin="positions_handler instantiation",
            status=STATUS_ERROR,
            text=f"Error with instance: {ex}, preorder_id: {preorder_id}"
        )
        return

    create_position.delay(sum_btc=sum_btc, preorder_id=preorder_id)


@shared_task
def open_position_handler_manual(sum_btc, comment=None):
    log = HedgeLogger()
    if sum_btc > 0:
        log.log(
            origin="positions_handler_manual START",
            status=STATUS_SUCCESS,
            text=f"Starting on: btc_sum = {sum_btc}"
        )
    else:
        log.log(
            origin="positions_handler instantiation",
            status=STATUS_ERROR,
            text=f"Btc sum is incorrect: {sum_btc}"
            )

    create_position.delay(sum_btc=sum_btc, comment=comment)











