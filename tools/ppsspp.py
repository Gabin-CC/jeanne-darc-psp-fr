"""Pilote PPSSPP via son debugger WebSocket (ws://127.0.0.1:45123/debugger).

Usage :
  ppsspp.py shot fichier.png             capture d'écran
  ppsspp.py press cross [n] [pause_s]    appuie n fois sur un bouton
  ppsspp.py seq "cross*3 start down cross" [pause_s]
Boutons : cross circle triangle square up down left right start select ltrigger rtrigger
"""
import asyncio
import base64
import json
import sys

import websockets

URL = 'ws://127.0.0.1:45123/debugger'


async def call(ws, event, **kw):
    await ws.send(json.dumps({'event': event, 'ticket': event, **kw}))
    while True:
        r = json.loads(await ws.recv())
        if r.get('ticket') == event or r.get('event') == 'error':
            return r


async def press(ws, button, pause):
    await call(ws, 'input.buttons.press', button=button, duration=6)
    await asyncio.sleep(pause)


async def main(argv):
    async with websockets.connect(URL, max_size=None) as ws:
        cmd = argv[0]
        if cmd == 'shot':
            await call(ws, 'cpu.stepping')
            r = await call(ws, 'gpu.buffer.screenshot', type='base64')
            await call(ws, 'cpu.resume')
            if 'base64' not in r:
                print(r)
                return
            open(argv[1], 'wb').write(base64.b64decode(r['base64']))
            print('ok', argv[1])
        elif cmd == 'press':
            n = int(argv[2]) if len(argv) > 2 else 1
            pause = float(argv[3]) if len(argv) > 3 else 0.4
            for _ in range(n):
                await press(ws, argv[1], pause)
        elif cmd == 'seq':
            pause = float(argv[2]) if len(argv) > 2 else 0.4
            for tok in argv[1].split():
                b, _, n = tok.partition('*')
                for _ in range(int(n or 1)):
                    await press(ws, b, pause)
        else:
            print(await call(ws, cmd, **json.loads(argv[1] if len(argv) > 1 else '{}')))


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
