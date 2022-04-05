from django.conf.urls import url
from rest_framework import routers

from main.views import MarketDataView, \
    PreordersViewSet, PositionsViewSet, PositionDataViewSet, PositionActionsView

router = routers.DefaultRouter()

router.register("preorders", PreordersViewSet)
router.register("positions", PositionsViewSet)
router.register("position-data", PositionDataViewSet)

urlpatterns = [
    url("market-data/", MarketDataView.as_view()),
    url("position-actions/", PositionActionsView.as_view())
]
urlpatterns += router.urls
