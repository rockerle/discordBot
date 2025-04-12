import asyncio
import os
import re
import discord
import yt_dlp
from discord.ext import commands

vc_connections = {}
waiting_queues = {}
queue = []
ffmpegOptions = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                 'options': '-vn'}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)


def is_rockerle(id):
    return id == "433921875832340480"


def com_is_rockerle(inter):
    return inter.user.id == "433921875832340480"


async def set_false_again(channel, guild):
    print("set false again called")
    if len(waiting_queues[guild]) > 0:
        print("playing next song in queue")
        nextsong = waiting_queues[guild].pop(0)
        print(nextsong[0])
        play(nextsong[0], nextsong[1], channel, guild)
    else:
        print("No more songs in queue")
        await channel.disconnect()
        print("done playing music")


def play(title, url, vc, guild):
    print("playing now: " + title)
    vc.play(discord.FFmpegPCMAudio(url, **ffmpegOptions),
            after=lambda _: asyncio.run_coroutine_threadsafe(
                coro=set_false_again(vc, guild),
                loop=vc.loop
            ))


@bot.tree.command(name="test", description="test command for testing tests")
@commands.check(com_is_rockerle)
async def test(inter: discord.Interaction, text: str):
    await inter.response.send_message(text)
    # if is_rockerle(inter.user.id):
    #     print(text)
    #     await inter.response.send_message(text)
    # else:
    #     print("Wait a second....")
    #     await inter.response.send_message("You're not rockerle!")


@bot.tree.command(name="sync", description="owner only")
@commands.check(com_is_rockerle)
async def sync(inter: discord.Interaction):
    await bot.tree.sync()
    await inter.response.send_message("Synchronized command tree")


@bot.tree.command(name="play", description="play a song from youtube")
async def play_song(ctx, url: str):
    try:
        if ctx.guild.voice_client is None:
            await ctx.user.voice.channel.connect()
            vc_connections[ctx.guild.id] = ctx.guild.voice_client
        await ctx.response.send_message("Processing provided link ... ")
        ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                song_info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError:
                await ctx.edit_original_response(content="Not a valid YouTube URL")
                return
        if not ctx.guild.voice_client.is_playing():
            title = "Now playing " + song_info['title']
            print("Now playing: "+title)
            waiting_queues.update({ctx.guild.id: []})
            play(song_info['title'], song_info['url'], ctx.guild.voice_client, ctx.guild.id)
            await ctx.edit_original_response(content=title)
        else:
            toQueue = (song_info['title'], song_info['url'])
            waiting_queues[ctx.guild.id].append(toQueue)
            responsetext = "Queued "+toQueue[0]
            await ctx.edit_original_response(content=responsetext)
    except discord.app_commands.errors.CommandInvokeError:
        await ctx.edit_original_response(content="Couldn't process request")


@bot.tree.command(name="pause", description="pause or continue the currently played song")
async def pause_song(ctx):
    if ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.pause()
        await ctx.response.send_message("Paused playing songs")
    else:
        ctx.guild.voice_client.resume()
        await ctx.response.send_message("Continued playing songs")


@bot.tree.command(name="skip", description="skips to the next song")
async def skip_song(ctx):
    if ctx.guild.voice_client is None:
        await ctx.response.send_message("Not playing anything now")
        return
    vc = ctx.guild.voice_client
    if vc.is_playing() or vc.is_paused():
        vc.stop()
        await ctx.response.send_message("skipping songs")
    await ctx.edit_original_response(content="Skipped playing songs")


@bot.tree.command(name="post", description="posting a song")
async def post_song(ctx, url: str):
    await ctx.response.defer()
    await ctx.edit_original_response(content="processing link to download")
    try:
        meta_infos = yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True}).extract_info(url, download=False)
    except yt_dlp.utils.DownloadError:
        await ctx.channel.send("Not a valid YouTube URL")
        return
    video_titel = meta_infos['title']  # .replace('|', '-')
    song_name = re.sub(r'[\\|:]', '-', video_titel)
    format = meta_infos['format']
    print('Downloaded in format: ' + format)
    ydl_opts = {'outtmpl': 'downloads/{0}.mp3'.format(song_name), 'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            meta_infos = ydl.extract_info(url)
        except yt_dlp.utils.DownloadError:
            await ctx.channel.send("Error while downloading")
            return
    await ctx.channel.send(file=discord.File("downloads/{0}.mp3".format(song_name)))
    os.remove("downloads/{0}.mp3".format(song_name))
    await ctx.edit_original_response(content="Downloaded {0}".format(song_name))


@bot.event
async def on_voice_state_update(member, before, after):
    if member==bot.user and after.channel is None:
        if not waiting_queues[member.guild.id] is None:
            waiting_queues[member.guild.id].clear()


@bot.event
async def on_ready():
    print("bot ready")

bot.run(os.environ['BOT_TOKEN'])
