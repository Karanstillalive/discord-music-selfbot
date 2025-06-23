import os 
import discord
from discord.ext import commands
import colorama
from colorama import Fore
import wavelink
import platform
import psutil
import datetime
import asyncio

# Initialize colors and constants
colorama.init(autoreset=True)
Flame = Fore.RED       # for banner, etc.
Hate = Fore.MAGENTA    # for shell command prompts and help
PREFIX = ">"

intents = discord.Intents.default()
intents.messages = True  

client = commands.Bot(command_prefix=[PREFIX], intents=intents, self_bot=True)

# Command descriptions for help
command_descriptions = {
    "help": "Gives Help Menu",
    "play": "Plays whatever music you like",
    "pause": "Pauses the music",
    "resume": "Resumes the song",
    "stop": "Stops the Music",
    "volume": "Sets the Volume (between 0-40000)",
    "volget": "Gets the current volume",
    "seek": "Seeks to a specific position in the song",
    "loop": "Loops the song",
    "join": "Joins the specified voice channel",
    "leave": "Leaves the current voice channel"
}

loop_status = {}

# If any command is sent via a Discord text channel (selfbot message),
# simply print the command details in shell format and ignore it.
@client.event
async def on_message(message):
    if message.author == client.user and isinstance(message.channel, discord.TextChannel):
        if message.content.startswith(PREFIX):
            parts = message.content.split()
            if parts:
                cmd = parts[0][len(PREFIX):]
                desc = command_descriptions.get(cmd, "No description provided")
                print(f"{Hate}{PREFIX}{cmd} - {desc}")
            return
    await client.process_commands(message)

# If the bot is moved (or region changes), reconnect and resume playback
@client.event
async def on_voice_state_update(member, before, after):
    if member.id == client.user.id:
        if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            vc = member.guild.voice_client
            if vc and vc.is_playing() and vc.current is not None:
                current_track = vc.current
                current_position = vc.position
                current_volume = vc.volume
                try:
                    await vc.disconnect()
                    new_vc = await after.channel.connect(cls=wavelink.Player)
                    await new_vc.set_volume(current_volume)
                    await new_vc.play(current_track)
                    await new_vc.seek(current_position)
                    print(f"Reconnected to voice channel {after.channel.name} and resumed playback.")
                except Exception as e:
                    print(f"Error reconnecting after voice channel change: {e}")

# When the bot is ready, display a banner and start the shell command loop.
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="LuciPlayZ"))
    await wavelink.NodePool.create_node(
        bot=client,
        host="lava-v3.ajieblogs.eu.org",
        port=80,
        password="https://dsc.gg/ajidevserver",
        https=False
    )
    client.load_extension("jishaku")
    os.system("clear")
    print(Flame + r"""
┏━┓︱︱︱︱︱︱︱︱︱︱︱︱︱︱
┃━┫┏┓︱┏━┓︱┏━━┓┏━┓
┃┏┛┃┗┓┃╋┗┓┃┃┃┃┃┻┫
┗┛︱┗━┛┗━━┛┗┻┻┛┗━┛
    """)
    print(f"{Flame}Logged In As {client.user.name}\nID - {client.user.id}")
    print(f"{Flame}Total servers ~ {len(client.guilds)}")
    print(f"{Flame}Total Users ~ {len(client.users)}")
    print(f"{Flame}Made by DereK ! ")
    if not hasattr(client, 'shell_loop_started'):
         client.shell_loop_started = True
         asyncio.create_task(shell_command_loop())

#
# Shell command functions (these work without a Discord context)
#
async def shell_help():
    for cmd, desc in command_descriptions.items():
        print(f"{Hate}{PREFIX}{cmd} - {desc}")

async def shell_join(vc_id: int):
    channel = client.get_channel(vc_id)
    if channel is None or not isinstance(channel, discord.VoiceChannel):
         print("Invalid voice channel ID provided.")
         return
    # Disconnect from any existing voice channels
    if client.voice_clients:
         for vc in client.voice_clients:
              await vc.disconnect()
    try:
         vc = await channel.connect(cls=wavelink.Player)
         print(f"Joined voice channel: {channel.name}")
    except Exception as e:
         print(f"Error joining voice channel: {e}")

async def shell_play(query: str):
    if not client.voice_clients:
         print("Not connected to any voice channel. Use join command first.")
         return
    vc = client.voice_clients[0]
    if not wavelink.NodePool.get_node():
         print("No nodes are connected. Please try again later.")
         return
    try:
         tracks = await wavelink.YouTubeTrack.search(query)
         if not tracks:
              print("No results found.")
              return
         track = tracks[0]
         await vc.play(track)
         print(f"Now playing {track.title}")
    except Exception as e:
         print(f"Error: {e}")

async def shell_pause():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    if vc.is_playing():
         await vc.pause()
         print("Paused the music.")
    else:
         print("There's nothing playing to pause.")

async def shell_resume():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    if vc.is_paused():
         await vc.resume()
         print("Resumed the music.")
    else:
         print("There's nothing paused to resume.")

async def shell_stop():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    if vc.is_playing():
         await vc.stop()
         print("Stopped the music.")
    else:
         print("There's nothing playing to stop.")
    await vc.disconnect()

async def shell_volume(level: int):
    if not 0 <= level <= 40000:
         print("Volume level must be between 0 and 40000.")
         return
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    await vc.set_volume(level)
    print(f"Volume set to {level}%")

async def shell_volget():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    print(f"Current volume is {vc.volume}%")

async def shell_seek(position: int):
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    if vc.is_playing():
         await vc.seek(position * 1000)
         print(f"Seeked the song to {position} seconds.")
    else:
         print("There's no music playing to seek.")

async def shell_loop():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    channel_id = str(vc.channel.id)
    if vc.is_playing():
         if channel_id in loop_status:
              loop_status[channel_id] = not loop_status[channel_id]
              status = "enabled" if loop_status[channel_id] else "disabled"
              print(f"Looping {status}.")
         else:
              loop_status[channel_id] = True
              print("Looping has been enabled.")
    else:
         print("There's no music playing to loop.")

async def shell_leave():
    if not client.voice_clients:
         print("Not connected to any voice channel.")
         return
    vc = client.voice_clients[0]
    await vc.disconnect()
    print("Left the voice channel.")

#
# Shell command loop: reads input from your terminal and processes it.
#
async def shell_command_loop():
    loop = asyncio.get_running_loop()
    while True:
         # Read command from shell asynchronously
         command_line = await loop.run_in_executor(None, input, f"{Hate}Shell Command > ")
         if not command_line.strip():
              continue
         parts = command_line.strip().split()
         cmd = parts[0]
         args = parts[1:]
         if cmd in [f"{PREFIX}help", "help"]:
              await shell_help()
         elif cmd in [f"{PREFIX}join", "join"]:
              if args:
                   try:
                        vc_id = int(args[0])
                   except:
                        print("Invalid voice channel id")
                        continue
                   await shell_join(vc_id)
              else:
                   print("Usage: join <vc id>")
         elif cmd in [f"{PREFIX}play", "play"]:
              if args:
                   query = " ".join(args)
                   await shell_play(query)
              else:
                   print("Usage: play <query>")
         elif cmd in [f"{PREFIX}pause", "pause"]:
              await shell_pause()
         elif cmd in [f"{PREFIX}resume", "resume"]:
              await shell_resume()
         elif cmd in [f"{PREFIX}stop", "stop"]:
              await shell_stop()
         elif cmd in [f"{PREFIX}volume", "volume"]:
              if args:
                   try:
                        level = int(args[0])
                   except:
                        print("Invalid volume level")
                        continue
                   await shell_volume(level)
              else:
                   print("Usage: volume <level>")
         elif cmd in [f"{PREFIX}volget", "volget"]:
              await shell_volget()
         elif cmd in [f"{PREFIX}seek", "seek"]:
              if args:
                   try:
                        pos = int(args[0])
                   except:
                        print("Invalid position")
                        continue
                   await shell_seek(pos)
              else:
                   print("Usage: seek <position in seconds>")
         elif cmd in [f"{PREFIX}loop", "loop"]:
              await shell_loop()
         elif cmd in [f"{PREFIX}leave", "leave"]:
              await shell_leave()
         else:
              print("Unknown command")

client.run("Token_here", bot=False)
