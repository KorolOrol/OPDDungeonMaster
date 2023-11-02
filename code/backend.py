import g4f
import tiktoken
import json
import pandas as pd
import re

max_response_tokens = 1024
token_limit = 16000

# Count tokens
def num_tokens_from_messages(messages):
    encoding= tiktoken.get_encoding("cl100k_base")  #model to encoding mapping https://github.com/openai/tiktoken/blob/main/tiktoken/model.py
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

# Chat response
def response(message, conversation, journal):
    if message != "":
        conversation.append({"role": "user", "content": message})
    if re.match(r"Используя предмет \".+\",", message):
        item_name = re.search(r"Используя предмет \"(.+)\",", message).group(1)
        for item in journal["items"]:
            if item["item"] == item_name:
                conversation.append({"role": "system", "content": f"Предмет: {item['item']['name']}. Описание: {item['item']['description']}"})
                break
        else:
            conversation.append({"role": "system", "content": "Предмета нет в инвентаре."})

    # Remove old messages if token limit is reached
    conv_history_tokens = num_tokens_from_messages(conversation)
    while conv_history_tokens + max_response_tokens >= token_limit:
        del conversation[1] 
        conv_history_tokens = num_tokens_from_messages(conversation)

    answer = g4f.ChatCompletion.create(
        model=g4f.models.gpt_35_turbo_16k_0613,
        #provider=g4f.Provider.NeuroGPT,
        messages=conversation,
        stream=False,
    )

    conversation.append({"role": "assistant", "content": answer})
    return answer

# Analyze message
def analyze(message):
    answer = g4f.ChatCompletion.create(
        model=g4f.models.gpt_35_turbo_16k_0613,
        #provider=g4f.Provider.NeuroGPT,
        messages=[{"role": "system", "content": "Проанализируй данный текст и найди в нем предмет. Если здесь нет предмета, то напиши 'None'. Если предмет найден, то напиши в формате \{\"name\": \"Название предмета\", \"description\": \"Описание предмета\"\}"},
                  {"role": "user", "content": message}],
        stream=False,
    )
    answer = json.loads(answer)
    return answer

def retry(conversation, journal):
    return response("", conversation, journal)