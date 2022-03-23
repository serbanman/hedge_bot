import time

from celery import shared_task

from main.models import Order, Position
from main.models.orders import STATUS_NEW, STATUS_FILLED
from main.models.positions import STATUS_CLOSED
from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from main.services import HedgeOrdersService


@shared_task
def close_position(sum_btc: float, position_id: str, preorder_id: str = None):
    SLEEP_ITERATION = 10

    service = HedgeOrdersService(preorder_id)
    service.log(
        origin="close_position START",
        status=STATUS_SUCCESS,
        text=f"Starting on preorder_id: {preorder_id}"
    )

    try:
        # for some reason sum_btc becomes str, json?
        sum_btc = float(sum_btc)
    except:
        return

    order_id = service.create_order(sum_btc=sum_btc, buy=True)
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
                service.log(
                    origin="close_position task",
                    status=STATUS_SUCCESS,
                    text=f"Inside loop got order filled."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                break
            if counter == RETRY_COUNT:
                service.log(
                    origin="close_position task",
                    status=STATUS_ERROR,
                    text=f"Inside loop exceeded counter."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                return
            service.order_price_handler(order_instance.order_id)
            counter += 1
        try:
            position_instance = Position.objects.get(id=position_id)
            order_instance.refresh_from_db()
            position_instance.status = STATUS_CLOSED
            position_instance.order_out = order_instance
            position_instance.btc_price_out = order_instance.price
            position_instance.save()

            service.log(
                origin="close_position task FINISH",
                status=STATUS_SUCCESS,
                text=f"All good"
                     f"Position id: {position_instance.id} order_instance.id: {order_instance.id}"
            )
        except Exception as ex:
            service.log(
                origin="close_position task",
                status=STATUS_ERROR,
                text=f"Error in editing position instance"
                     f"Ex: {ex} order_instance.id: {order_instance.id}"
            )
