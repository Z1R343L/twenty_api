"""Application module."""
import os
import sys
import logging
from time import time
from typing import List
import srsly

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, FastAPI, BackgroundTasks


from libtwenty import Board
from .containers import Container
from .services import Redis
from odmantic import AIOEngine, Model
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.DEBUG)

if not os.path.exists("/static/board_images"):
    os.mkdir("/static/board_images")

class User(Model):
    user_id: str
    user_name: str
    platform: str
    score: int
    score_epoch: float
    board: bytes

app = FastAPI()
engine = AIOEngine(AsyncIOMotorClient("mongodb://mongodb:27017"))

async def get_user(user_id: str):
    user = await engine.find_one(User, User.user_id == user_id)
    if not user:
        user = User(user_id=user_id, user_name="", platform="", score=0, score_epoch=time(), board=srsly.msgpack_dumps(None))
    return user

@app.put("/users/", response_model=User)
async def create_user(user: User):                          
    await engine.save(user)
    return user

@app.get("/users/", response_model=List[User])
async def get_users():
    users = await engine.find(User, sort=User.score)
    return users

@app.get("/users/count", response_model=int)
async def get_users_count():
    users = await engine.count(User)
    return users

@app.get("/users/{user_id}}", response_model=User)
async def get_user_by_id(user_id: str):
    users = await engine.find(User, User.user_id == user_id)
    return users


def board_response(agent: str, board: Board) -> dict:
    fn = f"{board.state_string()}.png"
    fp = f"/static/board_images/{fn}"
    if not os.path.exists(fp):
        im = board.render()
        im.save(fp, 'PNG')
    if agent == 'discord':
        return {
            "score": int(board.score),
            "possible_moves": board.possible_moves,
            "image_path": fp
        }

    elif agent == 'revolt':
        return {
            "score": int(board.score),
            "image_path": fp
        }

@app.api_route("/twenty/new_game")
@inject
async def twenty_new(agent: str, ID: str, name: str, redis: Redis = Depends(Provide[Container.service])):
    user = await get_user(ID)
    board = Board()
    user.board = srsly.msgpack_dumps(board.dump())
    user.user_name = name
    user.platform = agent
    if board.score > user.score:
        user.score = board.score
        user.score_epoch = time()
    await engine.save(user)
    return board_response(agent=agent, board=board)

@app.api_route("/twenty/data")
@inject
async def twenty_data(agent: str, ID: str, name: str, redis: Redis = Depends(Provide[Container.service])):
    user = await get_user(ID)
    board = Board()
    if user.board !=  srsly.msgpack_dumps(None):
        board.load(data=srsly.msgpack_loads(user.board))
        can_continue = True
    else:
        user.board = srsly.msgpack_dumps(board.dump())
        can_continue = False
    user.user_name = name
    await engine.save(user)
    response = board_response(agent=agent, board=board)
    response['can_continue'] = can_continue
    return response


@app.api_route("/twenty/move")
@inject
async def twenty_move(agent: str, ID: str, action: str, redis: Redis = Depends(Provide[Container.service])):
    user = await get_user(ID)
    board = Board()
    board.load(data=srsly.msgpack_loads(user.board))
    board.move(action=action)
    user.board = srsly.msgpack_dumps(board.dump())
    user.score = board.score
    await engine.save(user)
    return board_response(agent=agent, board=board)

@app.api_route("/twenty/set")
@inject
async def twenty_set(
    agent: str, ID: str, data: str, prefix:str, redis: Redis = Depends(Provide[Container.service])
):
    key = f"{prefix}_{agent}_{ID}"
    old_exits = await redis.exists(key)
    old_data = await redis.get(key) if old_exits else {}
    await redis.set(key=key, data=data)
    return {'old_exists': old_exits, 'old_data': old_data}

@app.api_route("/twenty/get")
@inject
async def twenty_get(agent: str, ID: str, prefix:str, redis: Redis = Depends(Provide[Container.service])):
    key = f"{prefix}_{agent}_{ID}"
    if await redis.exists(key=key):
        data = await redis.get(key=key)
        return {'success': True, 'data': data}
    else:
        return {'success': False, 'data': None}


container = Container()
container.config.redis_host.from_env("REDIS_HOST", "localhost")
container.config.redis_password.from_env("REDIS_PASSWORD", "password")
container.wire(modules=[sys.modules[__name__]])
