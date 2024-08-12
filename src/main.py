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

    async def load_extensions(self):
        print('Loading extensions...')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

    async def setup_hook(self):
        await self.load_extensions()

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
