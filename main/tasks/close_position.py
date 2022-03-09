import time

from celery import shared_task

from ..models import HedgeLog, Preorder, Order
from ..models.orders import STATUS_NEW, STATUS_FILLED
from ..models.positions import STATUS_CLOSED
from ..models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from ..services import OperationsService


@shared_task
def close_position(preorder_id: str):
    SLEEP_ITERATION = 10
    log = HedgeLog(
        origin="close_position START",
        status=STATUS_SUCCESS,
        text=f"Starting on preorder_id: {preorder_id}"
    )
    log.save()

    service = OperationsService(preorder_id)
    preorder_instance = Preorder.objects.get(id=preorder_id)
    position_instance = preorder_instance.positions.first()
    order_id = service.create_buy_order(preorder_id=preorder_id, position_id=position_instance.id)
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
                    origin="close_position task",
                    status=STATUS_SUCCESS,
                    text=f"Inside loop got order filled."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                log.save()
                break
            if counter == RETRY_COUNT:
                log = HedgeLog(
                    preorder=preorder_instance,
                    origin="close_position task",
                    status=STATUS_ERROR,
                    text=f"Inside loop exceeded counter."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                log.save()
                return
            service.order_price_handler(order_instance.order_id, 'buy')
            counter += 1
        try:
            order_instance.refresh_from_db()
            position_instance.status = STATUS_CLOSED
            position_instance.order_out = order_instance
            position_instance.btc_price_out = order_instance.price
            position_instance.save()
            log = HedgeLog(
                preorder=preorder_instance,
                origin="close_position task FINISH",
                status=STATUS_SUCCESS,
                text=f"All good"
                     f"Position id: {position_instance.id} order_instance.id: {order_instance.id}"
            )
            log.save()
        except Exception as ex:
            log = HedgeLog(
                preorder=preorder_instance,
                origin="close_position task",
                status=STATUS_ERROR,
                text=f"Error in editing position instance"
                     f"Ex: {ex} order_instance.id: {order_instance.id}"
            )
            log.save()
