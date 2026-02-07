from __future__ import annotations

import warnings
from logging import DEBUG, getLogger
from os import getenv
from typing import Any

import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from mafic import NodePool
from utils.player import MusicPlayer
from utils.bot_guard import check_credits, alterar_descricao_bot

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*UnknownVersionWarning.*")

load_dotenv()
getLogger("mafic").setLevel(DEBUG)

check_credits()

TOKEN = getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("[ERROR] ❌ Token não encontrado! Configure DISCORD_TOKEN no .env")


class Bot(commands.InteractionBot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.ready_ran = False
        self.pool = NodePool(self)

    async def on_ready(self):
        if self.ready_ran:
            return

        await self.pool.create_node(
            host="lavalinkv3.serenetia.com", # lavalink público que achei na net ai (para os curiosos esse é o site deles: https://freelavalink.serenetia.com/)
            port=80,
            label="PRINCIPAL",
            password="https://dsc.gg/ajidevserver",
            player_cls=MusicPlayer,
        )

        self.loop.create_task(alterar_descricao_bot(self, TOKEN))

        print("[SUCCESS] ✅ Bot online e conectado ao Lavalink")
        self.ready_ran = True


bot = Bot(intents=disnake.Intents.all())
bot.load_extensions("commands")

if __name__ == "__main__":
    bot.run(TOKEN)