from __future__ import annotations

from typing import TYPE_CHECKING

import disnake
from mafic import Player, Track, TrackEndEvent

if TYPE_CHECKING:
    from main import Bot


class MusicPlayer(Player):
    def __init__(self, client: Bot, channel: disnake.VoiceChannel) -> None:
        super().__init__(client, channel)
        self.queue: list[Track] = []


async def setup_events(bot: Bot):
    @bot.listen()
    async def on_track_end(event: TrackEndEvent):
        if isinstance(event.player, MusicPlayer) and event.player.queue:
            await event.player.play(event.player.queue.pop(0))