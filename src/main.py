import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.polls = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            sync_command=True,
            application_id=APPLICATION_ID
        )

        self.initial_extension = ["cogs.Ping"]

    async def setup_hook(self):
        for ext in self.initial_extension:
            await self.load_extension(ext)

        # await bot.tree.sync(guild=discord.Object(id=tokens.guild_id))
        await bot.tree.sync()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("=================")
        game = discord.Game("...")
        await self.change_presence(status=discord.Status.online, activity=game)


bot = MyBot()
bot.run(DISCORD_TOKEN)
