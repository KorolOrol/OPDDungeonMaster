import gradio as gr
import json
from backend import *

with open("code\prompts.txt", 'r', encoding='utf-8') as f:
    prompts = json.load(f)

conversation = [{"role": "system", "content": prompts["story"]}]

journal = {"items": [],
           "characters": [],
           "locations": [],
           "quests": [],
           }



with gr.Blocks() as webui:

    with gr.Row():
        chat_column = gr.Column(variant="panel")
        with gr.Column(variant="panel"):
            gr.Markdown("# Журнал")
            with gr.Tab("Предметы", id="items_tab"):
                gr.Markdown('''Чтобы положить предмет в инвентарь, напишите: _Положить предмет "**Название предмета**" в инвентарь_\n
                            Для использования предмета в начале сообщения напишите: _Используя предмет "**Название предмета**",_''')
                items = gr.Markdown()
            with gr.Tab("Персонажи", id="characters_tab"):
                gr.Markdown('''Чтобы запомнить персонажа, напишите: _Запомнить персонажа "**Имя персонажа**"_\n
                            Для обращения к персонажу в начале сообщения напишите: _Обращаясь к персонажу "**Имя персонажа**",_''')
                characters = gr.Markdown()
            with gr.Tab("Локации", id="locations_tab"):
                gr.Markdown('''Чтобы добавить локацию на карту, напишите: _Записать локацию на карту_\n
                            Для посещения локации в начале сообщения напишите: _Посетить локацию "**Название локации**"_''')
                locations = gr.Markdown()
            with gr.Tab("Задания", id="actions_tab"):
                gr.Markdown('''Чтобы записать задание в журнал, напишите: _Записать задание в журнал_''')
                quests = gr.Markdown()

    def update_journal():
        items_text = ""
        for item in journal["items"]:
            items_text += f"## {item['item']}\n{item['description']}\n\n"
        characters_text = ""
        for character in journal["characters"]:
            characters_text += f"## {character['character']}\n{character['description']}\n\n"
        locations_text = ""
        for location in journal["locations"]:
            locations_text += f"## {location['location']}\n{location['description']}\n\n"
        quests_text = ""
        for quest in journal["quests"]:
            quests_text += f"## {quest['quest']}\n{quest['description']}\n\n"
        return gr.Markdown(items_text), gr.Markdown(characters_text),\
               gr.Markdown(locations_text), gr.Markdown(quests_text)

    def chat_response(message, history):
        if re.match(r"Положить предмет \".+\" в инвентарь", message):
            item_name = re.search(r"Положить предмет \"(.+)\" в инвентарь", message).group(1)
            found_item = analyze(prompts, conversation, item=item_name)
            if found_item != None:
                journal["items"].append(found_item)
                return f"Получен предмет: {found_item['item']}"
            else:
                return "Предмет не найден."
        elif re.match(r"Запомнить персонажа \".+\"", message):
            character_name = re.search(r"Запомнить персонажа \"(.+)\"", message).group(1)
            found_character = analyze(prompts, conversation, character=character_name)
            if found_character != None:
                journal["characters"].append(found_character)
                return f"Персонаж записан в журнал: {found_character['character']}"
            else:
                return "Персонаж не найден."
        elif re.match(r"Записать локацию на карту", message):
            found_location = analyze(prompts, conversation, location=True)
            if found_location != None:
                journal["locations"].append(found_location)
                return f"Локация добавлена на карту: {found_location['location']}"
            else:
                return "Локация не найдена."
        elif re.match(r"Записать задание в журнал", message):
            found_quest = analyze(prompts, conversation, quest=True)
            if found_quest != None:
                journal["quests"].append(found_quest)
                return f"Задание добавлено в журнал: {found_quest['quest']}"
            else:
                return "Задание не найдено."
        return response(message, conversation, journal)

    def chat_retry():
        if conversation[-1]["role"] == "assistant":
            response = conversation[-1]
            del conversation[-1]
            if re.match(r"Получен предмет: \".+\"", response["content"]):
                item_name = re.search(r"Получен предмет: \"(.+)\"", response["content"]).group(1)
                for item in journal["items"]:
                    if item["item"] == item_name:
                        journal["items"].remove(item)
                        break
            elif re.match(r"Персонаж записан в журнал: \".+\"", response["content"]):
                character_name = re.search(r"Персонаж записан в журнал: \"(.+)\"", response["content"]).group(1)
                for character in journal["characters"]:
                    if character["character"] == character_name:
                        journal["characters"].remove(character)
                        break
            elif re.match(r"Локация добавлена на карту: \".+\"", response["content"]):
                location_name = re.search(r"Локация добавлена на карту: \"(.+)\"", response["content"]).group(1)
                for location in journal["locations"]:
                    if location["location"] == location_name:
                        journal["locations"].remove(location)
                        break
            elif re.match(r"Задание добавлено в журнал: \".+\"", response["content"]):
                quest_name = re.search(r"Задание добавлено в журнал: \"(.+)\"", response["content"]).group(1)
                for quest in journal["quests"]:
                    if quest["quest"] == quest_name:
                        journal["quests"].remove(quest)
                        break
        message = conversation.pop()["content"]
        return message

    def chat_undo():
        if (conversation[-1]["role"] == "user"):
            del conversation[-1:-3:-1]
        else:
            del conversation[-1:-4:-1]

    def chat_clear():
        conversation.clear()
        conversation.append(prompts["story"])

    with chat_column:
        chat = gr.ChatInterface(chat_response)
        chat.chatbot.height = 500
        chat.chatbot.layout = "panel"

    chat.retry_btn.click(chat_retry, outputs=[chat.saved_input])
    chat.undo_btn.click(chat_undo)
    chat.clear_btn.click(chat_clear)
    chat.chatbot.change(update_journal, outputs=[items, characters, locations, quests])
webui.launch()
    