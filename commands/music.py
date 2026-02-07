from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands
from mafic import Playlist, Track

from utils.player import MusicPlayer

if TYPE_CHECKING:
    from main import Bot

EMOJIS = json.loads(Path("database/emojis.json").read_text(encoding="utf-8"))


class MusicCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(contexts=disnake.InteractionContextTypes.guild)
    async def play(self, inter: disnake.GuildCommandInteraction, busca: str):
        """Toca uma música ou playlist no canal de voz.

        Parameters
        ----------
        busca: Nome ou link da música/playlist
        """

        if not inter.author.voice or not inter.author.voice.channel:
            return await inter.response.send_message(
                f"{EMOJIS['error']} Você precisa estar em um canal de voz.", ephemeral=True
            )

        await inter.response.defer()

        player: MusicPlayer | None = inter.guild.voice_client

        if not player:
            channel = inter.author.voice.channel
            player = await channel.connect(cls=MusicPlayer)

        tracks = await player.fetch_tracks(busca)

        if not tracks:
            return await inter.edit_original_response(
                content=f"{EMOJIS['error']} Nenhuma música encontrada."
            )

        if isinstance(tracks, Playlist):
            track = tracks.tracks[0]
            if len(tracks.tracks) > 1:
                player.queue.extend(tracks.tracks[1:])
                adicionadas = len(tracks.tracks) - 1
        else:
            track = tracks[0]
            adicionadas = 0

        if not player.current:
            await player.play(track)
        else:
            player.queue.append(track)

        titulo = f"{EMOJIS['music']} Tocando agora"
        info_musica = (
            f"-# **[{track.title}]({track.uri})**\n"
            f"-# {EMOJIS['user']} Autor: `{track.author}`\n"
            f"-# {EMOJIS['time']} Duração: `{self._formatar_duracao(track.length)}`"
        )

        if adicionadas > 0:
            info_musica += f"\n-# {EMOJIS['add']} **{adicionadas}** músicas adicionadas à fila"

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(titulo),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(info_musica),
            accent_colour=disnake.Color.green(),
        )

        await inter.edit_original_response(components=[container])

    @commands.slash_command(contexts=disnake.InteractionContextTypes.guild)
    async def stop(self, inter: disnake.GuildCommandInteraction):
        """Para a música atual e limpa a fila."""

        player: MusicPlayer | None = inter.guild.voice_client

        if not player:
            return await inter.send(
                f"{EMOJIS['error']} Não estou tocando nada no momento.", ephemeral=True
            )

        player.queue.clear()
        await player.stop()

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['stop']} Música parada"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay("-# A fila foi limpa e a reprodução foi interrompida."),
            accent_colour=disnake.Color.orange(),
        )

        await inter.send(components=[container])

    @commands.slash_command(contexts=disnake.InteractionContextTypes.guild)
    async def leave(self, inter: disnake.GuildCommandInteraction):
        """Desconecta o bot do canal de voz."""

        player: MusicPlayer | None = inter.guild.voice_client

        if not player:
            return await inter.send(
                f"{EMOJIS['error']} Não estou em nenhum canal de voz.", ephemeral=True
            )

        await player.disconnect()

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['leave']} Desconectado"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay("-# Saí do canal de voz com sucesso."),
            accent_colour=disnake.Color.red(),
        )

        await inter.send(components=[container])

    @commands.slash_command(contexts=disnake.InteractionContextTypes.guild)
    async def queue(self, inter: disnake.GuildCommandInteraction):
        """Mostra as músicas na fila atual."""

        player: MusicPlayer | None = inter.guild.voice_client

        if not player or not player.current:
            return await inter.send(
                f"{EMOJIS['error']} Não há nada tocando no momento.", ephemeral=True
            )

        atual = player.current
        fila_texto = f"-# **Tocando agora:**\n-# {EMOJIS['music']} [{atual.title}]({atual.uri})\n\n"

        if player.queue:
            fila_texto += "-# **Próximas músicas:**\n"
            for idx, track in enumerate(player.queue[:10], 1):
                fila_texto += f"-# `{idx}.` [{track.title}]({track.uri})\n"

            if len(player.queue) > 10:
                fila_texto += f"\n-# *...e mais {len(player.queue) - 10} músicas*"
        else:
            fila_texto += "-# *Nenhuma música na fila*"

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['queue']} Fila de Reprodução"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(fila_texto),
            accent_colour=disnake.Color.blue(),
        )

        await inter.send(components=[container])

    @staticmethod
    def _formatar_duracao(ms: int) -> str:
        segundos = ms // 1000
        minutos = segundos // 60
        segundos = segundos % 60
        return f"{minutos:02d}:{segundos:02d}"


def setup(bot: Bot):
    bot.add_cog(MusicCommands(bot))