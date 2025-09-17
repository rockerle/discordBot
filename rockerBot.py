import asyncio
import subprocess
import logging
import os
import re
import discord
import yt_dlp
from ascii import convert
from discord.ext import commands

# Global dictionaries for managing connections and queues
vc_connections = {}
waiting_queues = {}
ffmpegOptions = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -http_persistent 0',
    'options': '-vn -filter:a "volume=0.5"'  # Added volume filter to prevent audio issues
}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)


def is_rockerle(id):
    return str(id) == "433921875832340480"


def com_is_rockerle():
    async def predicate(ctx):
        return str(ctx.user.id) == "433921875832340480"

    return predicate


async def cleanup_voice_connection(guild_id):
    """Clean up voice connection and queue for a guild"""
    if guild_id in waiting_queues:
        waiting_queues[guild_id].clear()
    if guild_id in vc_connections:
        del vc_connections[guild_id]


async def set_false_again(voice_client, guild_id):
    """Handle what happens after a song finishes"""
    print("Song finished, checking queue...")

    try:
        if guild_id in waiting_queues and len(waiting_queues[guild_id]) > 0:
            print("Playing next song in queue")
            next_song = waiting_queues[guild_id].pop(0)
            print(f"Next: {next_song[0]}")
            await play_audio(next_song[0], next_song[1], voice_client, guild_id)
        else:
            print("No more songs in queue, disconnecting...")
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
            await cleanup_voice_connection(guild_id)
    except Exception as e:
        print(f"Error in set_false_again: {e}")
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        await cleanup_voice_connection(guild_id)


async def play_audio(title, url, voice_client, guild_id):
    """Play audio with better error handling"""
    try:
        print(f"Starting playback: {title}")

        if not voice_client or not voice_client.is_connected():
            print("Voice client not connected")
            return

        def after_playing(error):
            if error:
                print(f"Player error: {error}")

            # Schedule the cleanup coroutine
            coro = set_false_again(voice_client, guild_id)
            future = asyncio.run_coroutine_threadsafe(coro, voice_client.loop)
            try:
                future.result(timeout=5)  # Wait max 5 seconds
            except Exception as e:
                print(f"Error scheduling next song: {e}")

        audio_source = discord.FFmpegPCMAudio(url, **ffmpegOptions)
        voice_client.play(audio_source, after=after_playing)

    except Exception as e:
        print(f"Error in play_audio: {e}")


@bot.tree.command(name="test", description="test command for testing tests")
@commands.check(com_is_rockerle())
async def test(inter: discord.Interaction, text: str):
    await inter.response.send_message(text)


@bot.tree.command(name="sync", description="owner only")
@commands.check(com_is_rockerle())
async def sync(inter: discord.Interaction):
    await bot.tree.sync()
    await inter.response.send_message("Synchronized command tree")


# Replace your play_song command with this improved version

@bot.tree.command(name="play", description="play a song from youtube")
async def play_song(ctx, url: str):
    # Immediately defer the response to avoid timeout
    await ctx.response.defer()

    try:
        # Check if user is in a voice channel
        if not ctx.user.voice or not ctx.user.voice.channel:
            await ctx.followup.send("You need to be in a voice channel to use this command!")
            return

        user_channel = ctx.user.voice.channel
        guild_id = ctx.guild.id

        # Initialize guild queue if it doesn't exist
        if guild_id not in waiting_queues:
            waiting_queues[guild_id] = []

        await ctx.followup.send("Processing your request...")

        # Extract video info
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    await ctx.edit_original_response(content="Could not extract video information")
                    return

                title = info.get('title', 'Unknown Title')
                stream_url = info.get('url')

                if not stream_url:
                    await ctx.edit_original_response(content="Could not get audio stream from this video")
                    return

        except Exception as e:
            await ctx.edit_original_response(content=f"Error processing URL: {str(e)}")
            return

        # Handle voice connection with improved error handling
        voice_client = ctx.guild.voice_client

        if not voice_client:
            try:
                await ctx.edit_original_response(content=f"Connecting to {user_channel.name}...")

                # Clean up any existing connections first
                if guild_id in vc_connections:
                    try:
                        old_vc = vc_connections[guild_id]
                        if old_vc.is_connected():
                            await old_vc.disconnect()
                    except:
                        pass
                    del vc_connections[guild_id]
                    # Wait longer for cleanup
                    await asyncio.sleep(3)

                # Multiple connection attempts with increasing delays
                connection_attempts = 0
                max_attempts = 3

                while connection_attempts < max_attempts:
                    try:
                        connection_attempts += 1
                        await ctx.edit_original_response(
                            content=f"Connecting to {user_channel.name}... (Attempt {connection_attempts})")

                        # Try connecting with longer timeout
                        voice_client = await user_channel.connect(timeout=30.0, reconnect=True)
                        vc_connections[guild_id] = voice_client

                        # Wait longer for connection to stabilize
                        await asyncio.sleep(5)

                        if voice_client.is_connected():
                            print(f"Successfully connected to {user_channel.name} on attempt {connection_attempts}")
                            break
                        else:
                            print(f"Connection failed on attempt {connection_attempts}")
                            if connection_attempts < max_attempts:
                                await asyncio.sleep(5)  # Wait before retry
                                continue
                            else:
                                raise Exception("Failed to establish stable connection")

                    except asyncio.TimeoutError:
                        print(f"Connection timeout on attempt {connection_attempts}")
                        if connection_attempts < max_attempts:
                            await asyncio.sleep(10)  # Wait longer before retry
                            continue
                        else:
                            await ctx.edit_original_response(
                                content="Voice connection timed out after multiple attempts. Please try again later.")
                            return
                    except Exception as e:
                        print(f"Connection error on attempt {connection_attempts}: {e}")
                        if connection_attempts < max_attempts:
                            await asyncio.sleep(10)  # Wait longer before retry
                            continue
                        else:
                            await ctx.edit_original_response(
                                content=f"Failed to connect after {max_attempts} attempts: {str(e)}")
                            return

                if not voice_client or not voice_client.is_connected():
                    await ctx.edit_original_response(
                        content="Failed to establish voice connection after multiple attempts")
                    return

            except Exception as e:
                await ctx.edit_original_response(content=f"Unexpected connection error: {str(e)}")
                return

        elif voice_client.channel != user_channel:
            try:
                await voice_client.move_to(user_channel)
                await asyncio.sleep(2)  # Wait for move to complete
            except Exception as e:
                await ctx.edit_original_response(content=f"Failed to move to your channel: {str(e)}")
                return

        # Check if something is already playing
        if voice_client.is_playing() or voice_client.is_paused():
            # Add to queue
            waiting_queues[guild_id].append((title, stream_url))
            position = len(waiting_queues[guild_id])
            await ctx.edit_original_response(content=f"Queued: **{title}** (Position: {position})")
        else:
            # Play immediately
            await play_audio(title, stream_url, voice_client, guild_id)
            await ctx.edit_original_response(content=f"Now playing: **{title}**")

    except Exception as e:
        print(f"Unexpected error in play_song: {e}")
        try:
            await ctx.edit_original_response(content="An error occurred. Please try again.")
        except:
            try:
                await ctx.followup.send("An error occurred. Please try again.")
            except:
                pass


# Also add this improved cleanup function
async def cleanup_voice_connection(guild_id):
    """Enhanced cleanup with better error handling"""
    try:
        if guild_id in waiting_queues:
            waiting_queues[guild_id].clear()
        if guild_id in vc_connections:
            vc = vc_connections[guild_id]
            try:
                if vc and vc.is_connected():
                    await vc.disconnect()
            except Exception as e:
                print(f"Error disconnecting voice client: {e}")
            finally:
                del vc_connections[guild_id]
    except Exception as e:
        print(f"Error in cleanup_voice_connection: {e}")


# Add this event handler to better handle disconnections
@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        if after.channel is None and before.channel is not None:
            # Bot was disconnected
            guild_id = before.channel.guild.id
            print(f"Bot disconnected from voice in guild {guild_id}")
            await cleanup_voice_connection(guild_id)
        elif after.channel is not None and before.channel != after.channel:
            # Bot was moved
            print(f"Bot moved to {after.channel.name}")

    # Also check if bot is alone in channel
    if before.channel and bot.user in before.channel.members:
        if len([m for m in before.channel.members if not m.bot]) == 0:
            # Only bots left in channel
            voice_client = before.channel.guild.voice_client
            if voice_client:
                print("No users left in voice channel, disconnecting")
                await voice_client.disconnect()
                await cleanup_voice_connection(before.channel.guild.id)


@play_song.error
async def play_song_error(ctx, error):
    print(f"Error in play_song: {error}")


@bot.tree.command(name="pause", description="pause or resume the currently played song")
async def pause_song(ctx):
    if not ctx.guild.voice_client:
        await ctx.response.send_message("Not connected to a voice channel")
        return

    vc = ctx.guild.voice_client
    if vc.is_playing():
        vc.pause()
        await ctx.response.send_message("Paused")
    elif vc.is_paused():
        vc.resume()
        await ctx.response.send_message("Resumed")
    else:
        await ctx.response.send_message("Nothing is playing")


@bot.tree.command(name="skip", description="skips to the next song")
async def skip_song(ctx):
    if not ctx.guild.voice_client:
        await ctx.response.send_message("Not connected to a voice channel")
        return

    vc = ctx.guild.voice_client
    if vc.is_playing() or vc.is_paused():
        vc.stop()  # This will trigger the after callback to play next song
        await ctx.response.send_message("Skipped")
    else:
        await ctx.response.send_message("Nothing to skip")


@bot.tree.command(name="stop", description="stops playing and disconnects")
async def stop_song(ctx):
    if not ctx.guild.voice_client:
        await ctx.response.send_message("Not connected to a voice channel")
        return

    vc = ctx.guild.voice_client

    # Clear queue and stop
    if ctx.guild.id in waiting_queues:
        waiting_queues[ctx.guild.id].clear()

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    await vc.disconnect()
    await cleanup_voice_connection(ctx.guild.id)
    await ctx.response.send_message("Stopped and disconnected")


@bot.tree.command(name="queue", description="shows the current queue")
async def show_queue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in waiting_queues or len(waiting_queues[guild_id]) == 0:
        await ctx.response.send_message("The queue is empty")
        return

    queue_list = waiting_queues[guild_id]
    queue_text = "Current Queue:\n"

    for i, (title, _) in enumerate(queue_list[:10]):
        queue_text += f"{i + 1}. {title}\n"

    if len(queue_list) > 10:
        queue_text += f"... and {len(queue_list) - 10} more songs"

    await ctx.response.send_message(queue_text)


@bot.tree.command(name="clear", description="clears the music queue")
async def clear_queue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in waiting_queues:
        waiting_queues[guild_id] = []

    queue_size = len(waiting_queues[guild_id])
    waiting_queues[guild_id].clear()

    if queue_size > 0:
        await ctx.response.send_message(f"Cleared {queue_size} songs from the queue")
    else:
        await ctx.response.send_message("Queue was already empty")


@bot.tree.command(name="post", description="download and post a song file")
async def post_song(ctx, url: str):
    await ctx.response.defer()

    try:
        # Check if downloads directory exists
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        await ctx.edit_original_response(content="Processing download...")

        meta_infos = yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True}).extract_info(url, download=False)
        video_title = meta_infos['title']
        song_name = re.sub(r'[\\|:"/]', '-', video_title)[:50]  # Limit filename length and fix regex

        ydl_opts = {
            'outtmpl': f'downloads/{song_name}.%(ext)s',
            'format': 'bestaudio/best',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        downloaded_file = None
        for file in os.listdir('downloads'):
            if file.startswith(song_name):
                downloaded_file = f'downloads/{file}'
                break

        if not downloaded_file:
            await ctx.edit_original_response(content="Download completed but file not found")
            return

        await ctx.edit_original_response(content="Converting to MP3...")

        # Convert to MP3 using ffmpeg
        output_file = f'downloads/{song_name}.mp3'

        # Use ffmpeg to convert to MP3
        ffmpeg_cmd = [
            'ffmpeg', '-i', downloaded_file,
            '-acodec', 'libmp3lame',
            '-ab', '192k',  # 192kbps bitrate for good quality
            '-y',  # Overwrite output file if it exists
            output_file
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            await ctx.edit_original_response(content="Audio conversion failed")
            # Clean up original file
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            return

        # Remove the original downloaded file
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)

        # Check file size
        file_size = os.path.getsize(output_file)
        if file_size > 10 * 1024 * 1024:  # 10MB Discord limit
            await ctx.edit_original_response(content="File too large for Discord (max 10MB): your file: "+str(file_size))
            os.remove(output_file)
            return

        # Send the MP3 file
        await ctx.channel.send(file=discord.File(output_file))
        os.remove(output_file)
        await ctx.edit_original_response(content=f"Downloaded: {video_title}")

    except Exception as e:
        print(f"Error in post_song: {e}")
        await ctx.edit_original_response(content="Download failed")

        # Clean up any leftover files
        for file in os.listdir('downloads'):
            if file.startswith(song_name):
                try:
                    os.remove(f'downloads/{file}')
                except:
                    pass


@bot.tree.command(name="ascii", description="make ascii art")
async def ascii_art(ctx, src: str, width: int = 30, threshold: int = 128, invert: bool = False, top: str = "",
                    bottom: str = "", invtext: bool = False):
    try:
        await ctx.response.send_message("Processing...")
        res = await convert.convert(src, width, threshold, invert, invtext, top, bottom)
        if len(res) < 2000:
            await ctx.edit_original_response(content=f"```\n{res}\n```")
        else:
            await ctx.edit_original_response(content="ASCII art too large for Discord!")
    except Exception as e:
        print(f"Error in ascii_art: {e}")
        await ctx.edit_original_response(content="Failed to create ASCII art")


@bot.event
async def on_message(message):
    if message.author.bot or "bot" not in message.channel.name:
        return

    command = message.content.split(' ')
    if len(command) >= 2 and command[0] == '$ascii':
        try:
            result = convert.convert(command[1], 30, 128, True)
            await message.channel.send(f"```\n{result}\n```")
        except:
            await message.channel.send("ASCII conversion failed")


# @bot.event
# async def on_voice_state_update(member, before, after):
#     if member == bot.user:
#         if after.channel is None and before.channel is not None:
#             # Bot was disconnected
#             guild_id = before.channel.guild.id
#             print(f"Bot disconnected from voice in guild {guild_id}")
#             await cleanup_voice_connection(guild_id)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"Bot ready! Logged in as {bot.user}")


# Run the bot
if __name__ == "__main__":
    bot.run(os.environ['BOT_TOKEN'], log_level=logging.INFO)