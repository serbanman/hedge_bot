**AUTO-HEDGING BOT**

This piece of code provides ability to automatically open and close hedge 
positions of BTC-USDT pair on bybit based on preorder signals. 

This bot is able to adjust its order price accordingly to a BTCUSDT market price to make sure that
the order is going to be filled ASAP. To make it happen very quickly **there is 1$ SPREAD**, so if market rate is
40000 you are going to buy for 40001 and sell for 39999.

Also there is some basic API for market account data, providing ticker with current BTCUSDT rate, 
overall position value, position entry price, liquidation price, PNL, available leverage, wallet info and so on.

It lacks preorder handling module, 
so you can write your own, based on your specific preorder logic. 
Otherwise you can use it manually within your django-admin panel, by python shell or by web API.

Configuration instructions:
You would need a message broker (I prefer rabbitmq). Configure and start it as you please. Also you 
would need django-celery instance. If you would like to use periodic tasks (for example, for preorder parsing module (lacking in this realization)) 
you also would need django-celery-beat.

Make migrations -> `python3 manage.py makemigrations && python3 manage.py migrate`

Run Django as usual -> `python3 manage.py runserver`

Run Django-Celery as usual -> `python3 manage.py celery -A hedge worker -l info`

Run Django-Celery-Beat as usual -> `celery -A hedge beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler`

To use it automatically you should consider these APIs:

API instructions:

1. Using from django shell:
`python3 manage.py shell`

1.1 to manually open a hedge position ->   

`from main.tasks import open_position_handler_manual`
`open_position_handler_manual.delay(sum_btc: float)`

This will open a hedge position with given sum_btc.

1.2 to automatically open a hedge position ->

`from main.tasks import open_position_handler_auto`
`open_position_handler_auto.delay(preorder_id: str)`

This implementation requires having a preorder instance in db with sum_btc field filled. Auto mode is preferred, 
because hedge logs will be connected with specific preorder instance as well as order and positions instances via 
ForeignKey. So you can call position_instance.preorder.logs; position_instance.orders and so on.

1.3 to close a position ->
`from main.tasks import close_position_handler`
`close_position_handler.delay(position_id: str)`

Closing a position requires position instance id from db, so there will be no mistakes with account wallet. 
It uses all the data needed inside the script.
You can access db from within the shell doing this (bare example):

`from main.models import Position`
`position_instance = Position.objects.first()`

1.4. market data ->
`from main.services import HedgeMarketDataService`
`service = HedgeMarketDataService()`
`data = service.get_market_data()`

It will return a simple JSONable object, containing dict like this:
`{'rate': 46608.0, 'position_info': {'size': 0.154, 'position_value': 6532.47144525, 'leverage': 1, 
'entry_price': 42418.64574838, 'liq_price': 84625, 'unrealised_pnl': -643.37723475}, 'wallet_info': 
{'available_balance': 43507.15211119, 'wallet_balance': 50047.46252218}}`

2. Using by web API. All of these require admin cookies.

2.1 to manually open a hedge position ->   

Send a POST request to `{url}/main/position-actions/`

With JSON obj in the body: `{"action":"open", "sum_btc": 0.00}`

This will open a hedge position with given sum_btc.

2.2 to close a position ->

Send a POST request to `{url}/main/position-actions/`

With JSON obj in the body: `{"action":"close", "position_id": ""}`

2.3 market data -> 

Send a GET request to `{url}/main/market-data/`

2.4 data for the specific position

Send a GET request to `{url}/main/position-data/{id:pk}/`
Response will contain all the data about the position with this id. 
Example response for the manually made closed position:
`{
    "id": "4f8d0d92-5fdc-43c3-a926-ced0ad948486",
    "status": "closed",
    "comment": null,
    "order_in_data": {
        "id": "e1138547-6ff7-4c73-8247-448c4802e56f",
        "created_at": "2022-04-05T12:02:48.080996Z",
        "order_id": "8eeff9eb-d981-47b2-8843-68ae370dba2a",
        "type": "sell",
        "status": "Filled",
        "text": null,
        "sum_btc": "0.050000",
        "sum_usd": "2335.75",
        "price": "46714.00",
        "btc_rate": "46715.00",
        "usd_rate": null,
        "preorder": null,
        "position": "4f8d0d92-5fdc-43c3-a926-ced0ad948486"
    },
    "order_out_data": {
        "id": "d22be96e-d024-4df3-8ff2-339c4308cfc8",
        "created_at": "2022-04-05T12:03:25.156502Z",
        "order_id": "192431de-a181-4c50-bade-6c8c0ac475e8",
        "type": "buy",
        "status": "Filled",
        "text": null,
        "sum_btc": "0.050000",
        "sum_usd": "2335.62",
        "price": "46713.50",
        "btc_rate": "46712.50",
        "usd_rate": null,
        "preorder": null,
        "position": "4f8d0d92-5fdc-43c3-a926-ced0ad948486"
    },
    "analytics": {
        "position_margin": 0.5,
        "position_margin_str": "46714.00 - 46713.50 = 0.50"
    }
}`

2.5 list of all the positions (paginated and sortable) -> 

Send a GET request to `{url}/main/positions/`

2.6 list of all the preorders -> 

Send a GET request to `{url}/main/preorders/`


3. Using the django admin panel (periodic tasks)

You can register a periodic task using the task names from the 1. Django Shell and passing the arguments in below. 


