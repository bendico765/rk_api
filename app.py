import rk_api
import os
from flask import Flask, abort
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()
rk_account_username = os.getenv('LOGIN_USERNAME')
rk_account_password = os.getenv('LOGIN_PASSWORD')


@app.route("/player/<string:username>/position/<int:number_of_sightings>")
async def get_player_sightings(username: str, number_of_sightings: int):
	try:
		return await rk_api.position.get_player_sightings(username, number_of_sightings)
	except KeyError as e:
		abort(404)
	except Exception as e:
		abort(500)


@app.route("/player/<string:username>/stats")
async def get_player_stats(username: str):
	try:
		return await rk_api.stats.get_player_stats(rk_account_username, rk_account_password, username)
	except KeyError as e:
		abort(404)
	except Exception as e:
		abort(500)


@app.route("/player/<string:username>/img")
async def get_player_img(username: str):
	try:
		return await rk_api.img.get_player_img(rk_account_username, rk_account_password, username)
	except KeyError as e:
		abort(404)
	except Exception as e:
		abort(500)
