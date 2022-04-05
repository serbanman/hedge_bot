from rest_framework import mixins, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from main.models import Preorder, Position
from main.serializers import PreorderSerializer, PositionSerializer, PositionDataSerializer
from main.services import HedgeMarketDataService
from main.tasks import close_position_handler, open_position_handler_manual


class MarketDataView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        service = HedgeMarketDataService()
        data = service.get_market_data()
        return Response(data)


class PreordersViewSet(GenericViewSet, mixins.ListModelMixin):
    queryset = Preorder.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = PreorderSerializer
    pagination_class = PageNumberPagination


class PositionsViewSet(GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Position.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = PositionSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = self.queryset
        status = self.request.query_params.get("status", None)
        if status is not None:
            qs = qs.filter(status=status)

        is_by_hand = self.request.query_params.get("is_by_hand", None)
        if is_by_hand is not None:
            if is_by_hand == 'true':
                qs = qs.filter(preorder=None)
            elif is_by_hand == 'false':
                qs = qs.exclude(preorder=None)

        is_preorder_garant = self.request.query_params.get("is_preorder_garant", None)
        if is_preorder_garant is not None:
            if is_preorder_garant == 'true':
                qs = qs.filter(preorder__is_garant=True)
            elif is_preorder_garant == 'false':
                qs = qs.filter(preorder__is_garant=False)

        sort_by = self.request.query_params.get("sortBy", None)
        sort_desc = self.request.query_params.get("sortDesc", None)
        if sort_by is not None and sort_desc is not None:
            operator = "-" if sort_desc == "true" else ""
            try:
                if sort_by not in [
                    'btc_price_in', 'btc_price_out', 'is_by_hand',
                    'h_preorder_id', 'preorder_sum_rub', 'is_preorder_garant'
                ]:
                    qs = qs.order_by(operator + sort_by)
            except Exception as ex:
                print(f'** Error in sorting: {ex} /// sort by: {sort_by}')

        return qs


class PositionDataViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Position.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = PositionDataSerializer
    pagination_class = PageNumberPagination


class PositionActionsView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        data = request.data
        position_id = data.get('position_id', None)
        sum_btc = data.get('sum_btc', None)
        action = data.get('action', None)
        comment = data.get('comment', None)
        if action == 'close' and position_id:
            close_position_handler.delay(position_id)
            return Response(status.HTTP_200_OK)
        elif action == 'open' and sum_btc:
            try:
                sum_btc = float(sum_btc)
                open_position_handler_manual.delay(sum_btc, comment)
                return Response(status.HTTP_200_OK)
            except:
                return Response(status.HTTP_400_BAD_REQUEST)
        return Response(status.HTTP_400_BAD_REQUEST)

