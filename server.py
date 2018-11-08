import asyncio
import json
import re
import requests
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import configparser

import aiohttp

from popemessages import MESSAGES_FROM_GOD

COMMANDS_LIST = {
	"weather": {
		"format": "weather <place>",
		"desc": "Displays the Weather for defined places",
		"args": {
			"rvk": {
				"name": "Reykjavík",
				"desc": "Get weather for Reykjavík",
				"url": "https://www.yr.no/place/Iceland/Capital_Region/Reykjavik/"
			},
			"sko": {
				"name": "Skövde",
				"desc": "Get weather for Skövde",
				"url": "https://www.yr.no/place/Sweden/V%C3%A4stra_G%C3%B6taland/Sk%C3%B6vde/"
			}
		}
	},
	"pope": {
		"format": "Just write pope",
		"desc": "Get a message from da pope!"
	}
}

config = configparser.RawConfigParser()

def init_env():
	config.read('.env')
	print(config.get('BOT', 'TOKEN'))

def get_env(var):
	return config.get('BOT', var)

async def api_call(endpoint, method="GET", **kwargs):
	token = get_env('TOKEN')
	headers = {
		"headers": {
			"Authorization": f"Bot {token}",
			"User-Agent": "herraBot (https://nozagleh.com/@herrabot, 0.1)"
		}
	}
	kwargs = dict(headers, **kwargs)
	path = get_env('DISCORD_ENDPOINT') + endpoint
	async with aiohttp.ClientSession() as session:
		async with session.request(method, path, **kwargs) as response:
			assert 200 == response.status, response.reason
			return await response.json()

async def send_message(reciever, content, isprivate = False):
	channelid = reciever
	if isprivate:
		channel = await api_call('/users/@me/channels', 'POST', json={"recipient_id": reciever})
		channelid = channel['id']
	
	return await api_call(f"/channels/{channelid}/messages", "POST", json={"content": content})

def clean_command(command):
	command = command.strip(' 1234567890;-.<>@')
	args = command.split(None, 1)
	return args[0], args[1:]

async def show_command_help(cmd, args, channel):
	if cmd == "help":
		pass
	
	if "help" in args:
		print('asking for help')
		info = COMMANDS_LIST[cmd]
		helptext = f"Usage:\n{info['format']}"
		for arg, val in info['args'].items():
			helptext += f"\n- {val['name']}: {val['desc']}\n"
		
		await send_message(channel, helptext)


async def weather(channel, args):
	cmd = "weather"

	datestr = '%Y-%m-%dT%H:%M:%S'
	hourmin = '%H:%M'

	timenow = datetime.now()
	for code, val in COMMANDS_LIST[cmd]['args'].items():
		if code not in args:
			continue

		place = val['name']
		url = val['url']
		placeurl = url + 'forecast.xml'
		reqdata = requests.get(placeurl)
		xmldata = ET.fromstring(reqdata.text)
		
		dataextract = ''
		location = xmldata.find('location')
		timezone = location.find('timezone')
		tzone = timezone.attrib
		tfrom = ''
		tto = ''

		timenow = timenow + timedelta(minutes = int(tzone['utcoffsetMinutes']))
		for timedata in xmldata.iter('time'):
			attr = timedata.attrib
			tfrom = datetime.strptime(attr['from'], datestr)
			tto = datetime.strptime(attr['to'], datestr)
			if timenow >= tfrom and timenow <= tto:
				dataextract = timedata
				break

		wind = dataextract.find('windSpeed').attrib
		winddir = dataextract.find('windDirection').attrib
		temp = dataextract.find('temperature').attrib
		rain = dataextract.find('precipitation').attrib
		sun = xmldata.find('sun').attrib
		sunrise = datetime.strptime(sun['rise'], datestr)
		sunset = datetime.strptime(sun['set'], datestr)
		hoursofsun = sunset - sunrise
		datastring = f":microphone2:¡Weather Update!:microphone2: - {place}\nValid: {tfrom.strftime(hourmin)}-{tto.strftime(hourmin)}\n\n:wind_blowing_face: {winddir['name']} {wind['mps']} m/s\n\n:thermometer: {temp['value']}°\n\n:cloud_rain: {rain['value']} mm\n\n:sunrise: {sunrise.strftime(hourmin)} :city_sunset: {sunset.strftime(hourmin)}\n\nSee more at: {url} \n\n"
		
		await send_message(channel, datastring)
	pass

async def pope(channel):
	selected_message = MESSAGES_FROM_GOD[random.randint(0, len(MESSAGES_FROM_GOD) - 1)]

	await send_message(channel, selected_message)


async def commands(channel, command):
	responses = []
	cleancommand, args = clean_command(command)
	print(cleancommand, args)

	await show_command_help(cleancommand, args, channel)

	if "help" in args and cleancommand != "help":
		return False
	else:
		if cleancommand == "weather":
			if len(args) < 1:
				args.append('help')
			await weather(channel, args)
		if cleancommand == "pope":
			await pope(channel)
		elif cleancommand == "help":
			helpstr = ''
			for cmd, val in COMMANDS_LIST.items():
				helpstr += f"\n- {cmd}: {val['desc']}\n"

			await send_message(channel, f"Available commands:\n{helpstr}")
		else:
			pass

	return False

async def process_data(type, data):
	if type == "MESSAGE_CREATE":
		msg = f"{data['author']['username']} said:\n{data['content']}"
		print(msg)

		if len(data['mentions']) > 0:
			for member in data['mentions']:
				if member['id'] == get_env('CLIENT_ID'):
					await commands(data['channel_id'], data['content'])
					#return await send_message(data['channel_id'], "HELLO")
				else:
					print('Nobody mentioned me :(')
		# print(data)
		# if "herra" in data['content']
		#return await send_message(data['channel_id'], "HELLO")
	pass

async def start(url):
	async with aiohttp.ClientSession() as session:
		async with session.ws_connect(
			f"{url}?v=6&encoding=json") as ws:
			async for msg in ws:
				data = json.loads(msg.data)
				lastseq = ''

				if data["op"] == 10: # OP - Hello
					token = get_env('TOKEN')
					asyncio.ensure_future(heartbeat(
						ws,
						data['d']['heartbeat_interval'],
						lastseq
					))

					await ws.send_json({
						"op": 2, # OP - Ident.
						"d": {
							"token": token,
							"properties": {},
							"compress": False,
							"large_threshold": 250
						}
					})
				elif data["op"] == 11: # OP - Heartbeat ACK
					lastseq = data
				elif data["op"] == 0: # OP - Dispath
					await process_data(data['t'], data['d'])
					#print(data['t'], data['d'])
				else:
					print(data)

async def heartbeat(ws, interval, lastseq):
	while True:
		await asyncio.sleep(interval / 1000) # Sleep for interval time
		print('Sending ACK')
		await ws.send_json({
			"op": 1, # OP - Heartbeat
			"d": lastseq
		})

async def main():
	init_env()
	response = await api_call('/gateway')
	await start(response['url'])

init_env()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()