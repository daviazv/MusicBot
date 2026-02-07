import os
import asyncio
import requests


def check_credits():
    if not os.path.exists("creditos_visionario.txt"):
        raise SystemExit("[CRITICAL] ⚠️ Arquivo 'creditos_visionario.txt' não encontrado. desligando o bot...")


async def alterar_descricao_bot(bot, token: str):
    await asyncio.sleep(8)

    descricao = (
        "**Developed by: @darkgzzh\n"
        "**Posted on: https://discord.gg/visionario"
    )

    url = f"https://discord.com/api/v10/applications/{bot.user.id}"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }
    payload = {"description": descricao}

    try:
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 429:
            retry_after = response.json().get("retry_after", 5)
            await asyncio.sleep(retry_after)
            requests.patch(url, headers=headers, json=payload)

    except:
        pass