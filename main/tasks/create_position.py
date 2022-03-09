from celery import shared_task

from ..models.positions import STATUS_OPEN
from ..models.hedge_logs import STATUS_ERROR, STATUS_SUCCESS
from ..services import OperationsService
from ..models import Order, HedgeLog, Position, Preorder
from ..models.orders import STATUS_FILLED, STATUS_NEW
import time


@shared_task
def create_position(preorder_id: str):
    SLEEP_ITERATION = 10
    preorder_instance = Preorder.objects.get(id=preorder_id)
    log = HedgeLog(
        preorder=preorder_instance,
        origin="create_position START",
        status=STATUS_SUCCESS,
        text=f"Starting on preorder_id: {preorder_id}"
    )
    log.save()
    service = OperationsService(preorder_id)

    order_id = service.create_sell_order(sum_rub=preorder_instance.sum_rub, preorder_id=preorder_id)
    if order_id is not None:
        order_instance = Order.objects.get(id=order_id)
        service.is_order_filled(order_instance.order_id)
        order_instance.refresh_from_db()
        if order_instance.status == STATUS_NEW:
            time.sleep(SLEEP_ITERATION)
        RETRY_COUNT = 20
        counter = 0
        while order_instance.status != STATUS_FILLED:
            time.sleep(SLEEP_ITERATION)
            if service.is_order_filled(order_instance.order_id):
                log = HedgeLog(
                    preorder=preorder_instance,
                    origin="create_position task",
                    status=STATUS_SUCCESS,
                    text=f"Inside loop got order filled."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                log.save()
                break
            if counter == RETRY_COUNT:
                log = HedgeLog(
                    preorder=preorder_instance,
                    origin="create_position task",
                    status=STATUS_ERROR,
                    text=f"Inside loop exceeded counter."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                log.save()
                return
            service.order_price_handler(order_instance.order_id, 'sell')
            counter += 1
        try:
            order_instance.refresh_from_db()
            new_position = Position(
                preorder=preorder_instance,
                status=STATUS_OPEN,
                order_in=order_instance,
                btc_price_in=order_instance.price,
                order_out=None,
                btc_price_out=None,
                btc_quantity=order_instance.btc_quantity,
                )
            new_position.save()
            log = HedgeLog(
                preorder=preorder_instance,
                origin="create_position instance creation FINISH",
                status=STATUS_SUCCESS,
                text=f"Created position instance"
                     f"Position id: {new_position.id}; order_instance.id: {order_instance.id}"
            )
            log.save()
        except Exception as ex:
            log = HedgeLog(
                preorder=preorder_instance,
                origin="create_position task FINISH",
                status=STATUS_ERROR,
                text=f"Error in creating position instance"
                     f"Exception: {ex}; order_instance.id: {order_instance.id}"
            )
            log.save()

