from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

from utils.player import MusicPlayer

if TYPE_CHECKING:
    from main import Bot

EMOJIS = json.loads(Path("database/emojis.json").read_text(encoding="utf-8"))
PLAYLISTS_FILE = Path("database/playlists.json")


class PlaylistCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self._ensure_database()

    def _ensure_database(self):
        if not PLAYLISTS_FILE.exists():
            PLAYLISTS_FILE.write_text("{}", encoding="utf-8")

    def _load_playlists(self) -> dict:
        return json.loads(PLAYLISTS_FILE.read_text(encoding="utf-8"))

    def _save_playlists(self, data: dict):
        PLAYLISTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @commands.slash_command(contexts=disnake.InteractionContextTypes.guild)
    async def playlist(self, inter: disnake.GuildCommandInteraction):
        """Comandos de playlist."""
        pass

    @playlist.sub_command()
    async def create(self, inter: disnake.GuildCommandInteraction, nome: str):
        """Cria uma nova playlist pessoal.

        Parameters
        ----------
        nome: Nome da playlist
        """

        playlists = self._load_playlists()
        user_id = str(inter.author.id)

        if user_id not in playlists:
            playlists[user_id] = {}

        if nome in playlists[user_id]:
            return await inter.send(
                f"{EMOJIS['error']} Você já tem uma playlist com esse nome.", ephemeral=True
            )

        playlists[user_id][nome] = []
        self._save_playlists(playlists)

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['success']} Playlist criada"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(f"-# A playlist **{nome}** foi criada com sucesso!"),
            accent_colour=disnake.Color.green(),
        )

        await inter.send(components=[container])

    @playlist.sub_command()
    async def add(self, inter: disnake.GuildCommandInteraction, nome: str):
        """Adiciona a música atual à playlist.

        Parameters
        ----------
        nome: Nome da playlist
        """

        player: MusicPlayer | None = inter.guild.voice_client

        if not player or not player.current:
            return await inter.send(
                f"{EMOJIS['error']} Não há nenhuma música tocando no momento.", ephemeral=True
            )

        playlists = self._load_playlists()
        user_id = str(inter.author.id)

        if user_id not in playlists or nome not in playlists[user_id]:
            return await inter.send(
                f"{EMOJIS['error']} Você não tem uma playlist com esse nome.", ephemeral=True
            )

        track_data = {
            "title": player.current.title,
            "uri": player.current.uri,
            "author": player.current.author,
            "length": player.current.length,
        }

        if track_data in playlists[user_id][nome]:
            return await inter.send(
                f"{EMOJIS['error']} Esta música já está na playlist.", ephemeral=True
            )

        playlists[user_id][nome].append(track_data)
        self._save_playlists(playlists)

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['add']} Música adicionada"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(
                f"-# **{player.current.title}** foi adicionada à playlist **{nome}**"
            ),
            accent_colour=disnake.Color.green(),
        )

        await inter.send(components=[container])

    @playlist.sub_command()
    async def list(self, inter: disnake.GuildCommandInteraction):
        """Lista todas as suas playlists."""

        playlists = self._load_playlists()
        user_id = str(inter.author.id)

        if user_id not in playlists or not playlists[user_id]:
            return await inter.send(
                f"{EMOJIS['error']} Você não tem nenhuma playlist.", ephemeral=True
            )

        texto = ""
        for nome, musicas in playlists[user_id].items():
            texto += f"-# {EMOJIS['playlist']} **{nome}** ({len(musicas)} músicas)\n"

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['playlist']} Suas Playlists"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(texto),
            accent_colour=disnake.Color.blue(),
        )

        await inter.send(components=[container])

    @playlist.sub_command()
    async def load(self, inter: disnake.GuildCommandInteraction, nome: str):
        """Carrega uma playlist e toca as músicas.

        Parameters
        ----------
        nome: Nome da playlist
        """

        if not inter.author.voice or not inter.author.voice.channel:
            return await inter.send(
                f"{EMOJIS['error']} Você precisa estar em um canal de voz.", ephemeral=True
            )

        await inter.response.defer()

        playlists = self._load_playlists()
        user_id = str(inter.author.id)

        if user_id not in playlists or nome not in playlists[user_id]:
            return await inter.edit_original_response(
                content=f"{EMOJIS['error']} Você não tem uma playlist com esse nome."
            )

        player: MusicPlayer | None = inter.guild.voice_client

        if not player:
            channel = inter.author.voice.channel
            player = await channel.connect(cls=MusicPlayer)

        tracks_data = playlists[user_id][nome]

        if not tracks_data:
            return await inter.edit_original_response(
                content=f"-# {EMOJIS['error']} Esta playlist está vazia."
            )

        for track_data in tracks_data:
            tracks = await player.fetch_tracks(track_data["uri"])
            if tracks:
                track = tracks[0] if not isinstance(tracks, list) else tracks[0]
                
                if not player.current:
                    await player.play(track)
                else:
                    player.queue.append(track)

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['playlist']} Playlist carregada"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(
                f"-# **{len(tracks_data)}** músicas da playlist **{nome}** foram adicionadas à fila"
            ),
            accent_colour=disnake.Color.green(),
        )

        await inter.edit_original_response(components=[container])

    @playlist.sub_command()
    async def delete(self, inter: disnake.GuildCommandInteraction, nome: str):
        """Deleta uma playlist.

        Parameters
        ----------
        nome: Nome da playlist
        """

        playlists = self._load_playlists()
        user_id = str(inter.author.id)

        if user_id not in playlists or nome not in playlists[user_id]:
            return await inter.send(
                f"{EMOJIS['error']} Você não tem uma playlist com esse nome.", ephemeral=True
            )

        del playlists[user_id][nome]
        self._save_playlists(playlists)

        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"{EMOJIS['success']} Playlist deletada"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(f"-# A playlist **{nome}** foi removida."),
            accent_colour=disnake.Color.red(),
        )

        await inter.send(components=[container])


def setup(bot: Bot):
    bot.add_cog(PlaylistCommands(bot))