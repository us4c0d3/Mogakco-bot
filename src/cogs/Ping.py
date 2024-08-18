import logging

import discord
from discord import app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('Ping.py is ready')

    # 봇의 핑을 pong! 이라는 메세지와 함께 전송한다. latency는 일정 시간마다 측정됨에 따라 정확하지 않을 수 있다.
    @app_commands.command(name="ping", description="봇의 핑을 확인합니다.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'pong! {round(round(self.bot.latency, 4) * 1000)}ms')


async def setup(bot) -> None:
    await bot.add_cog(Ping(bot))
