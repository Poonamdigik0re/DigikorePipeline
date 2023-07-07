import asyncio
import json
import signal

import websockets

ALL_USERS = {}


async def wss_publish(websocket, data):
    users = ALL_USERS[websocket.path]
    users.remove(websocket)

    if users:
        message = json.dumps(data)
        await asyncio.wait([user.send(message) for user in users])


async def register(websocket):
    path = websocket.path

    if path not in ALL_USERS:
        ALL_USERS[path] = set()

    ALL_USERS[path].add(websocket)


async def unregister(websocket):
    path = websocket.path

    if websocket in ALL_USERS[path]:
        ALL_USERS[path].remove(websocket)


async def startup(websocket, path):
    await register(websocket)
    try:
        async for msg in websocket:
            message = json.loads(msg)
            func = message['func']
            data = message['data']
            await globals()[func](websocket, data)

    finally:
        await unregister(websocket)


async def start_server(stop):
    async with websockets.serve(startup, '127.0.0.1', 8101):
        await stop
        print('Shutting down websocket server..')


# setup loop and stop event
loop = asyncio.get_event_loop()
stop = asyncio.Future()

# add event handler
loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
# start the event loop
loop.run_until_complete(start_server(stop))
