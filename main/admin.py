from django.contrib import admin
from .models import Preorder, Position, Order, HedgeLog, PreorderStage

admin.site.register(Preorder)
admin.site.register(Position)
admin.site.register(Order)
admin.site.register(HedgeLog)
admin.site.register(PreorderStage)
