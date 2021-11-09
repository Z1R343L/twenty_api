"""Application module."""

import sys
import logging
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, FastAPI
from os.path import exists

from libtwenty import Board

from .containers import Container
from .services import Redis

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()


def board_response(agent: str, board: Board) -> dict:
    fn = f"{board.state_string()}.png"
    fp = f"/static/board_images/{fn}"
    if not exists(fp):
        im = board.render()
        im.save(fp, 'PNG')
    if agent == 'discord':
        return {
            "score": int(board.score()),
            "possible_moves": board.possible_moves(),
            "image_path": fp
        }

    elif agent == 'revolt':
        return {
            "score": int(board.score()),
            "image_path": fp
        }
    else:
        return {"board": str(board.print_revolt()), "score": int(board.score())}

def keybuilder(prefix: str, agent: str, ID: str) -> str:
    return f"{prefix}_{agent}_{ID}"

async def update_score(score: int, key: str, redis) -> None:
    exists = await redis.exists(key)
    if exists:
        data = await redis.get(key)
        if score > data[list(data.keys())[0]]:
            await redis.set(key, {list(data.keys())[0]: score})
    else:
        name = await redis.get(key.replace("score", "name"))
        await redis.set(key, {name: score})
        
async def update_name(name: str, key: str, redis) -> None:
    exists = await redis.exists(key)
    if not exists:
        await redis.set(key=key, data=name)


@app.api_route("/twenty/scores")
@inject
async def twenty_scores(redis: Redis = Depends(Provide[Container.service])):
    response = {}
    scores = await redis.get_by_prefix(prefix='score_')
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    res, place = [], 1
    for score in sorted_scores:
        res.append(f'{place}: {score[0]} {score[1]}p')
        place += 1
        return response


@app.api_route("/twenty/new_game")
@inject
async def twenty_new(agent: str, ID: str, name: str, redis: Redis = Depends(Provide[Container.service])):
    board = Board()
    await redis.set(key=keybuilder(prefix='board', agent=agent, ID=ID), data=board.dump())
    await update_name(name=name, key=keybuilder(prefix='name', agent=agent, ID=ID), redis=redis))
    await update_score(score=int(board.score()), key=keybuilder(prefix='score', agent=agent, ID=ID), redis=redis)
    return board_response(agent=agent, board=board)

@app.api_route("/twenty/data")
@inject
async def twenty_data(
    agent: str, ID: int, name: str, redis: Redis = Depends(Provide[Container.service])
):
    board = Board()
    board_key = keybuilder(prefix='board', agent=agent, ID=ID)
    can_continue = await redis.exists(key=board_key)
    if can_continue:
        board.load(data=await redis.get(key=board_key))
    else:
        await redis.set(key=board_key, data=board.dump())
        await update_name(name=name, key=keybuilder(prefix='name', agent=agent, ID=ID), redis=redis)
        await update_score(score=int(board.score()), key=keybuilder(prefix='score', agent=agent, ID=ID), redis=redis)
    response = board_response(agent=agent, board=board)
    response['can_continue'] = can_continue
    return response


@app.api_route("/twenty/move")
@inject
async def twenty_move(
    agent: str, ID: str, action: str, redis: Redis = Depends(Provide[Container.service])
):
    board = Board()
    board_key = keybuilder(prefix='board', agent=agent, ID=ID)
    board.load(data=await redis.get(key=board_key))
    board.move(action=action)
    await redis.set(key=board_key, data=board.dump())
    await update_score(score=board.score(), key=keybuilder(prefix='score', agent=agent, ID=ID), redis=redis)
    return board_response(agent=agent, board=board)

@app.api_route("/twenty/set")
@inject
async def twenty_set(
    agent: str, ID: str, data: str, prefix:str, redis: Redis = Depends(Provide[Container.service])
):
    key = keybuilder(prefix=prefix, agent=agent, ID=ID)
    old_exits = await redis.exists(key)
    old_data = await redis.get(key) if old_exits else {}
    await redis.set(key=key, data=data)
    return {'old_exists': old_exits, 'old_data': old_data}


container = Container()
container.config.redis_host.from_env("REDIS_HOST", "localhost")
container.config.redis_password.from_env("REDIS_PASSWORD", "password")
container.wire(modules=[sys.modules[__name__]])
