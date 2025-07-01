import discord
from discord.ext import commands, tasks
import asyncio
from aiohttp import web
import psutil
import os
import json
from datetime import datetime
import time
import aiohttp
import re
from aiohttp import WSMsgType
from modules.globalvars import VERSION_URL
import sys
import subprocess

class GooberWeb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.last_command = "No commands executed yet"
        self.last_command_time = "Never"
        self.start_time = time.time()
        self.websockets = set()
        
        self.app.add_routes([
            web.get('/', self.handle_index),
            web.get('/changesong', self.handle_changesong),
            web.get('/stats', self.handle_stats),
            web.get('/data', self.handle_json_data),
            web.get('/ws', self.handle_websocket),
            web.get('/styles.css', self.handle_css),
            web.get('/settings', self.handle_settings),
            web.post('/update_settings', self.handle_update_settings),
            web.post('/restart_bot', self.handle_restart_bot),
        ])

        self.bot.loop.create_task(self.start_web_server())
        self.update_clients.start()

    async def restart_bot(self):
        await asyncio.sleep(1)
        python = sys.executable
        os.execl(python, python, *sys.argv)

    async def handle_restart_bot(self, request):
        asyncio.create_task(self.restart_bot())
        return web.Response(text="Bot is restarting...")

    async def get_blacklisted_users(self):
        blacklisted_ids = os.getenv("BLACKLISTED_USERS", "").split(",")
        blacklisted_users = []
        
        for user_id in blacklisted_ids:
            if not user_id.strip():
                continue
                
            try:
                user = await self.bot.fetch_user(int(user_id))
                blacklisted_users.append({
                    "name": f"{user.name}#{user.discriminator}",
                    "avatar_url": str(user.avatar.url) if user.avatar else str(user.default_avatar.url),
                    "id": user.id
                })
            except discord.NotFound:
                blacklisted_users.append({
                    "name": f"Unknown User ({user_id})",
                    "avatar_url": "",
                    "id": user_id
                })
            except discord.HTTPException as e:
                print(f"Error fetching user {user_id}: {e}")
                continue
                
        return blacklisted_users
        
    async def get_enhanced_guild_info(self):
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        guild_info = []
        
        for guild in guilds:
            icon_url = str(guild.icon.url) if guild.icon else ""
            guild_info.append({
                "name": guild.name,
                "member_count": guild.member_count,
                "icon_url": icon_url,
                "id": guild.id
            })
            
        return guild_info
        
    async def start_web_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)
        await self.site.start()
        print("Goober web server started on port 8080")
    
    async def stop_web_server(self):
        await self.site.stop()
        await self.runner.cleanup()
        print("Web server stopped")
    
    def cog_unload(self):
        self.update_clients.cancel()
        self.bot.loop.create_task(self.stop_web_server())
    
    @tasks.loop(seconds=5)
    async def update_clients(self):
        if not self.websockets:
            return
            
        stats = await self.get_bot_stats()
        message = json.dumps(stats)
        
        for ws in set(self.websockets):
            try:
                await ws.send_str(message)
            except ConnectionResetError:
                self.websockets.remove(ws)
            except Exception as e:
                print(f"Error sending to websocket: {e}")
                self.websockets.remove(ws)
    
    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            self.websockets.remove(ws)
            
        return ws
    
    async def handle_css(self, request):
        css_path = os.path.join(os.path.dirname(__file__), 'styles.css')
        if os.path.exists(css_path):
            return web.FileResponse(css_path)
        return web.Response(text="CSS file not found", status=404)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        ctx = await self.bot.get_context(message)
        if ctx.valid and ctx.command:
            self._update_command_stats(ctx.command.name, ctx.author)
    
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        self._update_command_stats(command.name, interaction.user)
    
    def _update_command_stats(self, command_name, user):
        self.last_command = f"{command_name} (by {user.name}#{user.discriminator})"
        self.last_command_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.websockets:
            asyncio.create_task(self.update_clients())
    
    async def get_bot_stats(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_full_info()
        cpu_percent = psutil.cpu_percent()
        process_cpu = process.cpu_percent()
        
        memory_json_size = "N/A"
        if os.path.exists("memory.json"):
            memory_json_size = f"{os.path.getsize('memory.json') / 1024:.2f} KB"
        
        guild_info = await self.get_enhanced_guild_info()
        blacklisted_users = await self.get_blacklisted_users()
        
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
        
        return {
            "ram_usage": f"{mem_info.rss / 1024 / 1024:.2f} MB",
            "cpu_usage": f"{process_cpu}%",
            "system_cpu": f"{cpu_percent}%",
            "memory_json_size": memory_json_size,
            "guild_count": len(guild_info),
            "bl_count": len(blacklisted_users),
            "guilds": guild_info,
            "blacklisted_users": blacklisted_users,
            "last_command": self.last_command,
            "last_command_time": self.last_command_time,
            "bot_uptime": uptime_str,
            "latency": f"{self.bot.latency * 1000:.2f} ms",
            "bot_name": self.bot.user.name,
            "bot_avatar_url": str(self.bot.user.avatar.url) if self.bot.user.avatar else "",
            "authenticated": os.getenv("gooberauthenticated"),
            "lastmsg": os.getenv("gooberlatestgen"),
            "localversion": os.getenv("gooberlocal_version"),
            "latestversion": os.getenv("gooberlatest_version"),
            "owner": os.getenv("ownerid")
        }
    
    async def handle_update(self, request):
        if os.path.exists("goob/update.py"):
            return web.FileResponse("goob/update.py")
        return web.Response(text="Update file not found", status=404)

    async def handle_changesong(self, request):
        song = request.query.get('song', '')
        if song:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song))
            return web.Response(text=f"Changed song to: {song}")
        return web.Response(text="Please provide a song parameter", status=400)

    async def handle_changes(self, request):
        if os.path.exists("goob/changes.txt"):
            return web.FileResponse("goob/changes.txt")
        return web.Response(text="Changelog not found", status=404)

    async def read_env_file(self):
        env_vars = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    if key in ['splashtext', 'DISCORD_BOT_TOKEN']:
                        continue

                    env_vars[key] = value.strip('"\'')
        except FileNotFoundError:
            print(".env file not found")
        return env_vars

    
    async def handle_settings(self, request):
        env_vars = await self.read_env_file()
        
        # Get config.py variables
        config_vars = {}
        try:
            with open('config.py', 'r') as f:
                for line in f:
                    if line.startswith('VERSION_URL'):
                        config_vars['VERSION_URL'] = line.split('=', 1)[1].strip().strip('"')
        except FileNotFoundError:
            pass
        
        settings_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Goober Settings</title>
            <style>
                body { background-color: #121212; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
                h1 { color: #ff5555; text-align: center; }
                .settings-container { max-width: 800px; margin: auto; background-color: #1e1e1e; padding: 20px; border-radius: 8px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; color: #ff9999; }
                input { width: 100%; padding: 8px; background-color: #252525; color: white; border: 1px solid #444; border-radius: 4px; }
                button { background-color: #5f1b1b; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #7a2323; }
            </style>
        </head>
        <body>
            <div class='settings-container'>
                <h1>Goober Settings</h1>
                <form id='settingsForm' action='/update_settings' method='post'>
        """
        
        for key, value in env_vars.items():
            settings_html += f"""
            <div class='form-group'>
                <label for='{key}'>{key}</label>
                <input type='text' id='{key}' name='{key}' value='{value}'>
            </div>
            """
        
        for key, value in config_vars.items():
            settings_html += f"""
            <div class='form-group'>
                <label for='{key}'>{key}</label>
                <input type='text' id='{key}' name='{key}' value='{value}'>
            </div>
            """
        
        settings_html += """
                <button type='submit'>Save Settings</button>
                </form>
                <form action="/restart_bot" method="POST">
                    <button type="submit">Restart</button>
                </form>
            </div>
        </body>
        </html>
        """
        
        return web.Response(text=settings_html, content_type='text/html')
    
    async def handle_update_settings(self, request):
        data = await request.post()
        env_text = ""

        try:
            with open('.env', 'r') as f:
                env_text = f.read()
        except FileNotFoundError:
            pass

        def replace_match(match):
            key = match.group(1)
            value = match.group(2)
            if key in ['splashtext', 'DISCORD_BOT_TOKEN']:
                return match.group(0)
            if key in data:
                new_value = data[key]
                if not (new_value.startswith('"') and new_value.endswith('"')):
                    new_value = f'"{new_value}"'
                return f'{key}={new_value}'
            return match.group(0)

        env_text = re.sub(r'^(\w+)=([\s\S]+?)(?=\n\w+=|\Z)', replace_match, env_text, flags=re.MULTILINE)

        with open('.env', 'w') as f:
            f.write(env_text.strip() + '\n')

        if 'VERSION_URL' in data:
            config_text = ""
            try:
                with open('config.py', 'r') as f:
                    config_text = f.read()
            except FileNotFoundError:
                pass

            config_text = re.sub(r'^(VERSION_URL\s*=\s*").+?"', f'\\1{data["VERSION_URL"]}"', config_text, flags=re.MULTILINE)

            with open('config.py', 'w') as f:
                f.write(config_text.strip() + '\n')

        return aiohttp.web.Response(text="Settings updated successfully!")

    async def handle_index(self, request):
        stats = await self.get_bot_stats()

        guild_list_html = ""
        for guild in stats['guilds']:
            icon_html = f'<img src="{guild["icon_url"]}" alt="guild icon" class="guild-icon">' if guild["icon_url"] else '<div class="guild-icon-placeholder"></div>'
            guild_list_html += f"""
            <div class="guild-item">
                {icon_html}
                <div class="guild-info">
                    <div class="guild-name">{guild["name"]}</div>
                    <div class="guild-members">{guild["member_count"]} members</div>
                </div>
            </div>
            """
        blacklisted_users_html = ""
        for user in stats['blacklisted_users']:
            avatar_html = f'<img src="{user["avatar_url"]}" alt="user avatar" class="user-avatar">' if user["avatar_url"] else '<div class="user-avatar-placeholder"></div>'
            blacklisted_users_html += f"""
            <div class="blacklisted-user">
                {avatar_html}
                <div class="user-info">
                    <div class="user-name">{user["name"]}</div>
                    <div class="user-id">ID: {user["id"]}</div>
                </div>
            </div>
            """

        owner_id = stats.get('owner')
        owner = None
        owner_username = "Owner"
        owner_pfp = ""
        
        if owner_id:
            try:
                owner = await self.bot.fetch_user(int(owner_id))
                owner_username = f"{owner.name}#{owner.discriminator}"
                owner_pfp = str(owner.avatar.url) if owner and owner.avatar else ""
            except:
                pass


        html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>goobs central</title>
                <style>
                    #loading-screen {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: #000;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        z-index: 9999;
                        transition: opacity 1.5s ease-out;
                    }}
                    
                    #loading-screen.fade-out {{
                        opacity: 0;
                        pointer-events: none;
                    }}
                    
                    #welcome-message {{
                        color: #fff;
                        font-size: 2em;
                        margin-bottom: 20px;
                        text-align: center;
                        text-shadow: 0 0 10px #ff5555;
                    }}
                    
                    #owner-avatar {{
                        width: 100px;
                        height: 100px;
                        border-radius: 50%;
                        object-fit: cover;
                        border: 3px solid #5f1b1b;
                        box-shadow: 0 0 20px #ff5555;
                    }}
                    body {{
                        background-color: #121212;
                        color: #ffffff;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        line-height: 1.6;
                    }}
                    
                    .topnav {{
                        background-color: #2a0a0a;
                        overflow: hidden;
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: center;
                        padding: 10px;
                        gap: 15px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
                    }}
                    
                    .stat-item {{
                        gap: 5px;
                        color: white;
                        font-size: 14px;
                        background-color: #1a1a1a;
                        padding: 8px 15px;
                        border-radius: 6px;
                        align-items: center;
                        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
                        position: relative;
                        transition: all 0.3s ease;
                    }}
                    
                    .stat-item:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
                    }}
                    
                    .stat-item::after {{
                        content: '';
                        position: absolute;
                        bottom: -5px;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 60%;
                        height: 3px;
                        background: linear-gradient(90deg, transparent, #ff5555, transparent);
                        opacity: 0;
                        transition: opacity 0.3s ease;
                    }}
                    
                    .stat-item:hover::after {{
                        opacity: 1;
                    }}
                    
                    .stat-title {{
                        font-weight: bold;
                        color: #ff9999;
                    }}
                    
                    .stat-item span:not(.stat-title) {{
                        font-weight: bold;
                        color: #ffffff;
                    }}
                    
                    .center {{
                        text-align: center;
                        max-width: 800px;
                        margin: 20px auto;
                        padding: 0 20px;
                    }}
                    
                    .bot-info {{
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 15px;
                        margin-bottom: 10px;
                    }}
                    
                    .bot-avatar {{
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        border: 3px solid #5f1b1b;
                        object-fit: cover;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
                    }}
                    
                    hr {{
                        border: 0;
                        height: 1px;
                        background-image: linear-gradient(to right, transparent, #5f1b1b, transparent);
                        margin: 20px 0;
                    }}
                    
                    .stat-container-row {{
                        display: flex;
                        justify-content: space-between;
                        gap: 30px;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 0 20px;
                    }}
                    
                    .stat-container {{
                        flex: 1;
                        background-color: #1e1e1e;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                        min-width: 0;
                    }}
                    
                    .stat-title {{
                        color: #ff5555;
                        font-size: 1.1em;
                        margin-bottom: 10px;
                        border-bottom: 1px solid #333;
                        padding-bottom: 5px;
                    }}
                    
                    .guild-item {{
                        display: flex;
                        align-items: center;
                        gap: 15px;
                        padding: 10px;
                        margin: 5px 0;
                        background-color: #252525;
                        border-radius: 5px;
                        transition: background-color 0.2s;
                    }}
                    
                    .guild-item:hover {{
                        background-color: #333;
                    }}
                    
                    .guild-icon {{
                        width: 48px;
                        height: 48px;
                        border-radius: 50%;
                        object-fit: cover;
                    }}
                    
                    .guild-icon-placeholder {{
                        width: 48px;
                        height: 48px;
                        border-radius: 50%;
                        background-color: #7289da;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .guild-info {{
                        display: flex;
                        flex-direction: column;
                        flex-grow: 1;
                        min-width: 0;
                    }}
                    
                    .guild-name {{
                        font-weight: bold;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }}
                    
                    .guild-members {{
                        font-size: 0.8em;
                        color: #99aab5;
                    }}
                    
                    .blacklisted-user {{
                        display: flex;
                        align-items: center;
                        gap: 15px;
                        padding: 10px;
                        margin: 5px 0;
                        background-color: #2a1a1a;
                        border-radius: 5px;
                        border-left: 3px solid #ff5555;
                    }}
                    
                    .user-avatar {{
                        width: 48px;
                        height: 48px;
                        border-radius: 50%;
                        object-fit: cover;
                    }}
                    
                    .user-avatar-placeholder {{
                        width: 48px;
                        height: 48px;
                        border-radius: 50%;
                        background-color: #7289da;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .user-info {{
                        display: flex;
                        flex-direction: column;
                    }}
                    
                    .user-name {{
                        font-weight: bold;
                        color: #ff5555;
                    }}
                    
                    .user-id {{
                        font-size: 0.8em;
                        color: #99aab5;
                    }}
                    
                    input[type="text"] {{
                        background-color: #252525;
                        color: white;
                        border: 1px solid #444;
                        padding: 8px;
                        border-radius: 4px;
                        width: 200px;
                        margin-right: 10px;
                    }}
                    
                    button {{
                        background-color: #5f1b1b;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                        cursor: pointer;
                        transition: background-color 0.2s;
                    }}
                    
                    button:hover {{
                        background-color: #7a2323;
                    }}
                    
                    #guild-list, #blacklisted-users {{
                        max-height: 400px;
                        overflow-y: auto;
                        padding-right: 5px;
                    }}
                    
                    #guild-list::-webkit-scrollbar, #blacklisted-users::-webkit-scrollbar {{
                        width: 6px;
                    }}
                    
                    #guild-list::-webkit-scrollbar-track, #blacklisted-users::-webkit-scrollbar-track {{
                        background: #1a1a1a;
                    }}
                    
                    #guild-list::-webkit-scrollbar-thumb, #blacklisted-users::-webkit-scrollbar-thumb {{
                        background-color: #5f1b1b;
                        border-radius: 3px;
                    }}
                    
                    @media (max-width: 768px) {{
                        .stat-container-row {{
                            flex-direction: column;
                        }}
                        
                        .topnav {{
                            gap: 10px;
                            padding: 10px 5px;
                        }}
                        
                        .stat-item {{
                            font-size: 12px;
                            padding: 8px 12px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div id="loading-screen">
                    <img id="owner-avatar" src="{owner_pfp}" onerror="this.style.display='none'">
                    <div id="welcome-message"><b>Welcome, {owner_username}</b></div>
                </div>
                <div class="topnav">
                    <div class="stat-item" id="ram-usage">
                        <span class="stat-title">RAM:</span>
                        <span>{stats['ram_usage']}</span>
                    </div>
                    <div class="stat-item" id="system-cpu">
                        <span class="stat-title">CPU:</span>
                        <span>{stats['system_cpu']}</span>
                    </div>
                    <div class="stat-item" id="latency">
                        <span class="stat-title">Latency:</span>
                        <span>{stats['latency']}</span>
                    </div>
                    <div class="stat-item" id="json-size">
                        <span class="stat-title">JSON Size:</span>
                        <span>{stats['memory_json_size']}</span>
                    </div>
                    <div class="stat-item" id="uptime">
                        <span class="stat-title">Uptime:</span>
                        <span>{stats['bot_uptime']}</span>
                    </div>
                </div>

                <div class="center">
                    <div class="bot-info">
                        <img src="{stats['bot_avatar_url']}" alt="botvatar" class="bot-avatar" id="bot-avatar">
                        <h1 id="bot-name">{stats['bot_name']}</h1>
                    </div>
                    <hr>
                    <p>your stupid little goober that learns off other people's messages</p>
                </div>

                <div class="stat-container-row">
                    <div class="stat-container">
                        <div class="stat-title">Last Command</div>
                        <div id="last-command">{stats['last_command']}</div>
                        <div style="font-size: 0.9em; color: #999;" id="last-command-time">at {stats['last_command_time']}</div>
                        <br>
                        <div class="stat-title">Logged into goober central</div>
                        <div id="last-command">{stats['authenticated']}</div>
                        <br>
                        <div class="stat-title">Last generated message</div>
                        <div id="last-command">{stats['lastmsg']}</div>
                        <br>
                        <div class="stat-title">Version</div>
                        <div id="last-command">Installed Version: {stats['localversion']}</div>
                        <div id="last-command">Latest Version: {stats['latestversion']}</div>
                        <br>
                        <div class="stat-title">goober-central URL</div>
                        <div id="last-command">{VERSION_URL}</div>
                        <br>
                        <div class="stat-title">Change song</div>
                        <form action="/changesong" method="get">
                            <input type="text" name="song" placeholder="Enter song name...">
                            <button type="submit">
                                change song
                            </button>
                        </form>
                    </div>

                    <div class="stat-container">
                        <div class="stat-title">Servers (<span id="guild-count">{stats['guild_count']}</span>)</div>
                        <div id="guild-list">
                            {guild_list_html}
                        </div>
                        <br>
                        <div class="stat-title">Blacklisted Users (<span id="guild-count">{stats['bl_count']})</div>
                        <div id="blacklisted-users">
                            {blacklisted_users_html if stats['blacklisted_users'] else "<div>No blacklisted users</div>"}
                        </div>
                    </div>
                </div>
                <script>
                    window.addEventListener('load', function() {{
                        setTimeout(function() {{
                            const loadingScreen = document.getElementById('loading-screen');
                            loadingScreen.classList.add('fade-out');
                            setTimeout(function() {{
                                loadingScreen.remove();
                            }}, 1500);
                        }}, 1500);
                    }});
                    const ws = new WebSocket('ws://' + window.location.host + '/ws');
                    
                    ws.onmessage = function(event) {{
                        const data = JSON.parse(event.data);

                        document.getElementById('ram-usage').innerHTML = `<span class="stat-title">RAM:</span> <span>${{data.ram_usage}}</span>`;
                        document.getElementById('cpu-usage').innerHTML = `<span class="stat-title">CPU:</span> <span>${{data.cpu_usage}}</span>`;
                        document.getElementById('system-cpu').innerHTML = `<span class="stat-title">System CPU:</span> <span>${{data.system_cpu}}</span>`;
                        document.getElementById('latency').innerHTML = `<span class="stat-title">Latency:</span> <span>${{data.latency}}</span>`;
                        document.getElementById('json-size').innerHTML = `<span class="stat-title">JSON Size:</span> <span>${{data.memory_json_size}}</span>`;
                        document.getElementById('uptime').innerHTML = `<span class="stat-title">Uptime:</span> <span>${{data.bot_uptime}}</span>`;
                        
                        document.getElementById('bot-name').textContent = data.bot_name;
                        const botAvatar = document.getElementById('bot-avatar');
                        if (botAvatar.src !== data.bot_avatar_url) {{
                            botAvatar.src = data.bot_avatar_url;
                        }}
                        

                        document.getElementById('last-command').textContent = data.last_command;
                        document.getElementById('last-command-time').textContent = `at ${{data.last_command_time}}`;
                        
                        document.getElementById('guild-count').textContent = data.guild_count;
                        

                        let guildListHtml = '';
                        data.guilds.forEach(guild => {{
                            const iconHtml = guild.icon_url 
                                ? `<img src="${{guild.icon_url}}" alt="guild icon" class="guild-icon">` 
                                : '<div class="guild-icon-placeholder"></div>';
                            guildListHtml += `
                                <div class="guild-item">
                                    ${{iconHtml}}
                                    <div class="guild-info">
                                        <div class="guild-name">${{guild.name}}</div>
                                        <div class="guild-members">${{guild.member_count}} members</div>
                                    </div>
                                </div>
                            `;
                        }});
                        document.getElementById('guild-list').innerHTML = guildListHtml;
                        
                        let blacklistedUsersHtml = '';
                        if (data.blacklisted_users && data.blacklisted_users.length > 0) {{
                            data.blacklisted_users.forEach(user => {{
                                const avatarHtml = user.avatar_url 
                                    ? `<img src="${{user.avatar_url}}" alt="user avatar" class="user-avatar">` 
                                    : '<div class="user-avatar-placeholder"></div>';
                                blacklistedUsersHtml += `
                                    <div class="blacklisted-user">
                                        ${{avatarHtml}}
                                        <div class="user-info">
                                            <div class="user-name">${{user.name}}</div>
                                            <div class="user-id">ID: ${{user.id}}</div>
                                        </div>
                                    </div>
                                `;
                            }});
                        }} else {{
                            blacklistedUsersHtml = '<div>No blacklisted users</div>';
                        }}
                        document.getElementById('blacklisted-users').innerHTML = blacklistedUsersHtml;
                    }};
                    
                    ws.onclose = function() {{
                        console.log('WebSocket disconnected');
                    }};
                </script>
            </body>
            </html>
        """
        
        return web.Response(text=html_content, content_type='text/html')
    
    async def handle_stats(self, request):
        return await self.handle_index(request)
    
    async def handle_json_data(self, request):
        stats = await self.get_bot_stats()
        return web.json_response(stats)

async def setup(bot):
    await bot.add_cog(GooberWeb(bot))