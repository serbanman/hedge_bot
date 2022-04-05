from celery import shared_task

from main.models.positions import STATUS_OPEN
from main.models.hedge_logs import STATUS_ERROR, STATUS_SUCCESS
from main.services import HedgeOrdersService
from main.models import Order, Position
from main.models.orders import STATUS_FILLED, STATUS_NEW
import time


@shared_task
def create_position(sum_btc, preorder_id: str = None, comment=None):
    SLEEP_ITERATION = 10
    service = HedgeOrdersService(preorder_id)
    service.log(
        origin="create_position START",
        status=STATUS_SUCCESS,
        text=f"Starting on preorder_id: {preorder_id}"
    )

    try:
        # for some reason sum_btc becomes str, json?
        sum_btc = float(sum_btc)
    except:
        return

    order_id = service.create_order(sum_btc=sum_btc, sell=True)
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
                    origin="create_position task",
                    status=STATUS_SUCCESS,
                    text=f"Inside loop got order filled."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                break
            if counter == RETRY_COUNT:
                service.log(
                    origin="create_position task",
                    status=STATUS_ERROR,
                    text=f"Inside loop exceeded counter."
                         f"Counter {counter}; order_instance.id: {order_instance.id}"
                )
                return
            service.order_price_handler(order_instance.order_id)
            counter += 1
        try:
            order_instance.refresh_from_db()
            preorder_instance = service.instantiate()
            new_position = Position(
                preorder=preorder_instance,
                status=STATUS_OPEN,
                sum_btc=order_instance.sum_btc,
                comment=comment,
            )
            new_position.save()
            order_instance.position = new_position
            order_instance.save()
            service.log(
                origin="create_position instance creation FINISH",
                status=STATUS_SUCCESS,
                text=f"Created position instance"
                     f"Position id: {new_position.id}; order_instance.id: {order_instance.id}"
            )
        except Exception as ex:
            service.log(
                origin="create_position task FINISH",
                status=STATUS_ERROR,
                text=f"Error in creating position instance"
                     f"Exception: {ex}; order_instance.id: {order_instance.id}"
            )