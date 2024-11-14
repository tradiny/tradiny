# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from config import Config
from openai import AsyncOpenAI
import openai

openai.api_key = Config.OPENAI_API_KEY
import time
import logging
from collections import defaultdict

from utils import LimitedSizeDict, register_request, is_request_allowed

max_size = 1000
conversations = LimitedSizeDict(max_size)
ip_requests = defaultdict(list)


async def query(
    client_ip,
    conversation_id,
    system_content,
    user_content,
    img,
    model="gpt-4-turbo",
    max_tokens=64,
    on_chunk=None,
):
    if not is_request_allowed(
        Config.MAX_OPENAI_REQUESTS_PER_IP_PER_HOUR, ip_requests, client_ip
    ):
        logging.info(f"Too many requests: {client_ip}")
        return await on_chunk("Error: Too many requests.")

    if client_ip not in Config.WHITELIST_IP:
        register_request(ip_requests, client_ip)

    client = AsyncOpenAI()

    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})

    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_content},
                {"type": "image_url", "image_url": {"url": img}},
            ],
        }
    )

    conversations[conversation_id] = messages

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0,
            top_p=1,
            stream=True,  # Enable streaming mode
        )

        assistant_message_content = ""

        async for chunk in response:
            if on_chunk:
                chunk_dict = chunk.to_dict()
                if "content" in chunk_dict["choices"][0]["delta"]:
                    assistant_message_content += chunk_dict["choices"][0]["delta"][
                        "content"
                    ]
                    await on_chunk(chunk_dict["choices"][0]["delta"]["content"])

        if assistant_message_content:
            conversations[conversation_id].append(
                {"role": "assistant", "content": assistant_message_content}
            )
    except Exception as e:
        logging.error(f"Error: {e}")
        return await on_chunk(f"Error: {e}")


async def query_reply(
    client_ip,
    conversation_id,
    user_content,
    model="gpt-4-turbo",
    max_tokens=64,
    on_chunk=None,
):

    if not is_request_allowed(
        Config.MAX_OPENAI_REQUESTS_PER_IP_PER_HOUR, ip_requests, client_ip
    ):
        logging.info(f"Too many requests: {client_ip}")
        return await on_chunk("Too many requests.")

    if client_ip not in Config.WHITELIST_IP:
        register_request(ip_requests, client_ip)

    client = AsyncOpenAI()

    messages = conversations[conversation_id]

    messages.append(
        {"role": "user", "content": [{"type": "text", "text": user_content}]}
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0,
            top_p=1,
            stream=True,  # Enable streaming mode
        )

        assistant_message_content = ""

        async for chunk in response:
            if on_chunk:
                chunk_dict = chunk.to_dict()
                if "content" in chunk_dict["choices"][0]["delta"]:
                    assistant_message_content += chunk_dict["choices"][0]["delta"][
                        "content"
                    ]
                    await on_chunk(chunk_dict["choices"][0]["delta"]["content"])

        if assistant_message_content:
            conversations[conversation_id].append(
                {"role": "assistant", "content": assistant_message_content}
            )

    except Exception as e:
        logging.error(f"Error: {e}")
        return await on_chunk(f"Error: {e}")
