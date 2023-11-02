import gradio as gr
from backend import *

with open("prompts.csv") as f:
    prompts = [line.strip() for line in f.readlines()]

system_prompt = {"role": "system", "content": "Ты пират, отвечай как пират."}
conversation = [{"role": "system", "content": "Ты пират, отвечай как пират."}]

journal = {"items": [],
           "characters": [],
           "places": [],
           "actions": [],
           }

def chat_response(message, history):
    return response(message, conversation, journal)

def chat_retry():
    del conversation[-1]
    message = conversation.pop()["content"]
    return message

def chat_undo():
    if (conversation[-1]["role"] == "user"):
        del conversation[-1:-3:-1]
    else:
        del conversation[-1:-4:-1]

def chat_clear():
    conversation.clear()
    conversation.append(system_prompt)

def add_items():
    items = ""
    for item in journal["items"]:
        items += f"## {item['item']}\n{item['description']}\n\n"
    characters = ""
    for character in journal["characters"]:
        characters += f"## {character['character']}\n{character['description']}\n\n"
    places = ""
    for place in journal["places"]:
        places += f"## {place['place']}\n{place['description']}\n\n"
    actions = ""
    for action in journal["actions"]:
        actions += f"## {action['action']}\n{action['description']}\n\n"
    return gr.Markdown(items), gr.Markdown(characters), gr.Markdown(places), gr.Markdown(actions)

with gr.Blocks() as webui:
    with gr.Row():
        with gr.Column():
            chat = gr.ChatInterface(chat_response)
            analyze_button = gr.Button("Анализ")
        with gr.Column(variant="panel"):
            gr.Markdown("# Журнал")
            with gr.Tab("Предметы", id="items_tab"):
                gr.Markdown('Для использования предмета в начале сообщения напишите: _Используя предмет "**Название предмета**",_')
                items = gr.Markdown()
            with gr.Tab("Персонажи", id="characters_tab"):
                characters = gr.Markdown()
            with gr.Tab("Локации", id="locations_tab"):
                locations = gr.Markdown()
            with gr.Tab("События", id="actions_tab"):
                actions = gr.Markdown()
    analyze_button.click(fn=add_items, outputs=[items, characters, locations, actions])
    chat.retry_btn.click(chat_retry, outputs=[chat.saved_input])
    chat.undo_btn.click(chat_undo)
    chat.clear_btn.click(chat_clear)
webui.launch()