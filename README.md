# Discord Bot
My Discord utility bot based on the discord.py python library

## Bot Slash Commands

| Command   | Description                                   | Parameters & Usage                                                             | Notes                        |
|-----------|-----------------------------------------------|--------------------------------------------------------------------------------|------------------------------|
| `/play`   | Play a song from YouTube                      | `url` (YouTube link)<br> `/play https://youtube.com/watch?v=xxxxxx`            | Must be in a voice channel   |
| `/pause`  | Pause or resume the currently played song     | (none)                                                                         |                              |
| `/skip`   | Skip to the next song                         | (none)                                                                         |                              |
| `/stop`   | Stop playing and disconnect from voice        | (none)                                                                         | Clears queue                 |
| `/queue`  | Show the current song queue                   | (none)                                                                         | Shows up to 10 items         |
| `/clear`  | Clears the music queue                        | (none)                                                                         |                              |
| `/post`   | Download and post a song file                 | `url` (YouTube link)<br> `/post https://youtube.com/watch?v=xxxxxx`            | Discord file size limit: 10MB|
| `/ascii`  | Make ASCII art                                | `src` (image/file URL), `width`, `threshold`, `invert`, `top`, `bottom`, `invtext` (all optional except `src`)<br> `/ascii https://m.media-amazon.com/images/I/71I9bVulvgL.png width=25 invert=True top="ASCII" bottom="FROG"` |      https://imgur.com/zAAWH4z                        |
| `/test`   | Echo command for testing                      | `text` (string)<br> `/test hello world`                                        | Owner only                   |
| `/sync`   | Sync command tree (owner only)                | (none)                                                                         | Owner only                   |

