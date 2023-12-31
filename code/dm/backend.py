from openai import OpenAI
import tiktoken
import json
import re

client = OpenAI(api_key="sk-...", base_url="https://neuroapi.host/v1")

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

    # Using journal
    if re.match(r"Используя предмет \".+\",", message):
        item_name = re.search(r"Используя предмет \"(.+)\",", message).group(1)
        for item in journal["items"]:
            if item["item"] == item_name:
                conversation.append({"role": "system", "content": f"Предмет: {item['item']}. Описание: {item['description']}"})
                break
        else:
            conversation.append({"role": "system", "content": "Предмета нет в инвентаре."})
    elif re.match(r"Обращаясь к персонажу \".+\",", message):
        character_name = re.search(r"Обращаясь к персонажу \"(.+)\",", message).group(1)
        for character in journal["characters"]:
            if character["character"] == character_name:
                conversation.append({"role": "system", "content": f"Персонаж: {character['character']}. Описание: {character['description']}"})
                break
        else:
            conversation.append({"role": "system", "content": "Персонаж неизвестен."})
    elif re.match(r"Посетить локацию \".+\"", message):
        location_name = re.search(r"Посетить локацию \"(.+)\"", message).group(1)
        for location in journal["locations"]:
            if location["location"] == location_name:
                conversation.append({"role": "system", "content": f"Локация: {location['location']}. Описание: {location['description']}"})
                break
        else:
            conversation.append({"role": "system", "content": "Локация неизвестна."})

    # Remove old messages if token limit is reached
    conv_history_tokens = num_tokens_from_messages(conversation)
    while conv_history_tokens + max_response_tokens >= token_limit:
        del conversation[1] 
        conv_history_tokens = num_tokens_from_messages(conversation)

    answer = client.chat.completions.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=conversation
    )

    conversation.append({"role": "assistant", "content": answer.choices[0].message.content})
    return answer.choices[0].message.content

# Analyze message
def analyze(prompts, item=None, character=None, location=None, quest=None):
    if item:
        prompt = prompts["item"] + f"Найди предмет {item}"
    elif character:
        prompt = prompts["character"] + f"Найди персонажа {character}"
    elif location:
        prompt = prompts["location"]
    elif quest:
        prompt = prompts["quest"]
    answer = client.chat.completions.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[{"role": "system", "content": prompt + "\n"}],
        stream=False,
    )
    answer = json.loads(answer.choices[0].message.content)
    return answer

def retry(conversation, journal):
    return response("", conversation, journal)