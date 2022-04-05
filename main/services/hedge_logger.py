from main.models import HedgeLog, Preorder
from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR


class HedgeLogger:
    def __init__(self, preorder_id=None):
        self.preorder_id = preorder_id
        self.preorder_instance = self.instantiate()

    def instantiate(self):
        try:
            preorder_instance = Preorder.objects.get(id=self.preorder_id)
            return preorder_instance
        except:
            return None

    def log(self, origin: str, status: [STATUS_ERROR, STATUS_SUCCESS], text: str):
        log = HedgeLog(
            preorder=self.preorder_instance,
            origin=origin,
            status=status,
            text=text
        )
        log.save()
