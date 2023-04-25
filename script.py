import time
from pathlib import Path
import configparser

import glob
import gradio as gr
import numpy as np
import nltk
nltk.download('punkt')

from bark import SAMPLE_RATE, generate_audio, preload_models
from IPython.display import Audio
from scipy.io.wavfile import write as write_wav

from extensions.bark_tts import tts_preprocessor
from modules import chat, shared
from modules.html_generator import chat_html_wrapper


config_file = configparser.ConfigParser()

if Path('extensions/bark_tts/bark_tts.ini').is_file() == False:

    config_file.add_section('bark_tts')
    config_file.set('bark_tts', 'speaker', 'en_speaker_8')
    config_file.set('bark_tts', 'activate', 'True')
    config_file.set('bark_tts', 'show_text', 'True')
    config_file.set('bark_tts', 'autoplay', 'True')
    config_file.set('bark_tts', 'tokenize', 'True')
    config_file.set('bark_tts', 'text_temp', '0.6')
    config_file.set('bark_tts', 'waveform_temp', '0.6')
    config_file.add_section('bark_internals')
    config_file.set('bark_internals', 'text_use_gpu', 'True')
    config_file.set('bark_internals', 'text_use_small', 'False')
    config_file.set('bark_internals', 'coarse_use_gpu', 'True')
    config_file.set('bark_internals', 'coarse_use_small', 'False')
    config_file.set('bark_internals', 'fine_use_gpu', 'True')
    config_file.set('bark_internals', 'fine_use_small', 'False')
    config_file.set('bark_internals', 'codec_use_gpu', 'True')
    config_file.set('bark_internals', 'force_reload', 'False')

    with open(r'extensions/bark_tts/bark_tts.ini', 'w') as configfileObj:
        config_file.write(configfileObj)
        configfileObj.flush()
        configfileObj.close()

    print()
    print("Config file 'bark_tts.ini' recreated with default settings")

def read_config():
    config_file.read('extensions/bark_tts/bark_tts.ini')
    return config_file

config = read_config()

def update_config(setting, value):
    global config
    config_file['bark_tts'][setting] = str(value)
    with open('extensions/bark_tts/bark_tts.ini','w') as configfileObj:
        config_file.write(configfileObj)
        configfileObj.flush()
        configfileObj.close()
    config = read_config()


params = {
    'speaker': config['bark_tts']['speaker'],
    'activate': config['bark_tts'].getboolean('activate'),
    'show_text': config['bark_tts'].getboolean('show_text'),
    'autoplay': config['bark_tts'].getboolean('autoplay'),
    'tokenize': config['bark_tts'].getboolean('tokenize'),
    'text_temp': config['bark_tts'].getfloat('text_temp'),
    'waveform_temp': config['bark_tts'].getfloat('waveform_temp')
}


print()
print('Loading Bark models...')
preload_models(
    text_use_gpu = config['bark_internals'].getboolean('text_use_gpu'),
    text_use_small = config['bark_internals'].getboolean('text_use_small'),
    coarse_use_gpu = config['bark_internals'].getboolean('coarse_use_gpu'),
    coarse_use_small = config['bark_internals'].getboolean('coarse_use_small'),
    fine_use_gpu = config['bark_internals'].getboolean('fine_use_gpu'),
    fine_use_small = config['bark_internals'].getboolean('fine_use_small'),
    codec_use_gpu = config['bark_internals'].getboolean('codec_use_gpu'),
    force_reload = config['bark_internals'].getboolean('force_reload')
)


default_voices = ['en_speaker_0', 'en_speaker_1', 'en_speaker_2', 'en_speaker_3', 'en_speaker_4', 'en_speaker_5', 'en_speaker_6', 'en_speaker_7', 'en_speaker_8', 'en_speaker_9']
custom_voices = glob.glob('extensions/bark_tts/voices/*.npz')
voices = custom_voices + default_voices
streaming_state = shared.args.no_stream  # remember if chat streaming was enabled


def remove_tts_from_history(name1, name2, mode):
    for i, entry in enumerate(shared.history['internal']):
        shared.history['visible'][i] = [shared.history['visible'][i][0], entry[1]]
    return chat_html_wrapper(shared.history['visible'], name1, name2, mode)


def toggle_text_in_history(name1, name2, mode):
    for i, entry in enumerate(shared.history['visible']):
        visible_reply = entry[1]
        if visible_reply.startswith('<audio'):
            if params['show_text']:
                reply = shared.history['internal'][i][1]
                shared.history['visible'][i] = [shared.history['visible'][i][0], f"{visible_reply.split('</audio>')[0]}</audio>\n\n{reply}"]
            else:
                shared.history['visible'][i] = [shared.history['visible'][i][0], f"{visible_reply.split('</audio>')[0]}</audio>"]
    return chat_html_wrapper(shared.history['visible'], name1, name2, mode)


def input_modifier(string):
    """
    This function is applied to your text inputs before
    they are fed into the model.
    """

    # Remove autoplay from the last reply
    if shared.is_chat() and len(shared.history['internal']) > 0:
        shared.history['visible'][-1] = [shared.history['visible'][-1][0], shared.history['visible'][-1][1].replace('controls autoplay>', 'controls>')]

    shared.processing_message = "*Is recording a voice message...*"
    shared.args.no_stream = True  # Disable streaming cause otherwise the audio output will stutter and begin anew every time the message is being updated
    return string


def output_modifier(string):
    """
    This function is applied to the model outputs.
    """

    global model, current_params, streaming_state

    for i in params:
        if params[i] != current_params[i]:
            # model = load_model()
            current_params = params.copy()
            break

    if not params['activate']:
        return string

    original_string = string
    string = tts_preprocessor.preprocess(string)

    if string == '':
        string = '*Empty reply, try regenerating*'
    else:
        output_file = Path(f'extensions/bark_tts/outputs/{shared.character}_{int(time.time())}.wav')
        if params['tokenize'] == True:
            sentences = nltk.sent_tokenize(string)
            audio_array = np.empty(0, dtype=np.int16)
            chunks = ['']
            token_counter = 0
            for sentence in sentences:
                current_tokens = len(nltk.Text(sentence))
                if token_counter + current_tokens <= 250:
                    token_counter = token_counter + current_tokens
                    chunks[-1] = chunks[-1] + " " + sentence
                else:
                    chunks.append(sentence)
                    token_counter = current_tokens
            for chunk in chunks:
                audio_chunk = generate_audio(chunk, history_prompt=params['speaker'], text_temp=params['text_temp'], waveform_temp=params['waveform_temp'])
                audio_array = np.concatenate((audio_array, audio_chunk))
        else:
            audio_array = generate_audio(string, history_prompt=params['speaker'], text_temp=params['text_temp'], waveform_temp=params['waveform_temp'])
        Audio(audio_array, rate=SAMPLE_RATE)
        write_wav(output_file, SAMPLE_RATE, audio_array)

        autoplay = 'autoplay' if params['autoplay'] else ''
        string = f'<audio src="file/{output_file.as_posix()}" controls {autoplay}></audio>'
        if params['show_text']:
            string += f'\n\n{original_string}'

    shared.processing_message = "*Is typing...*"
    shared.args.no_stream = streaming_state  # restore the streaming option to the previous value
    return string


def bot_prefix_modifier(string):
    """
    This function is only applied in chat mode. It modifies
    the prefix text for the Bot and can be used to bias its
    behavior.
    """

    return string


def setup():
    global current_params
    current_params = params.copy()


def ui():
    # Gradio elements
    with gr.Accordion("Bark TTS"):
        with gr.Row():
            activate = gr.Checkbox(value=params['activate'], label='Activate TTS')
            autoplay = gr.Checkbox(value=params['autoplay'], label='Play TTS automatically')
            tokenize = gr.Checkbox(value=params['tokenize'], label='Tokenize the reply')

        show_text = gr.Checkbox(value=params['show_text'], label='Show message text under audio player')
        voice = gr.Dropdown(value=params['speaker'], choices=voices, label='TTS voice')
        with gr.Row():
            t_temp = gr.Slider(0, 1, value=params['text_temp'], step=0.01, label='Text temperature')
            w_temp = gr.Slider(0, 1, value=params['waveform_temp'], step=0.01, label='Waveform temperature')

        with gr.Row():
            convert = gr.Button('Permanently replace audios with the message texts')
            convert_cancel = gr.Button('Cancel', visible=False)
            convert_confirm = gr.Button('Confirm (cannot be undone)', variant="stop", visible=False)

    # Convert history with confirmation
    convert_arr = [convert_confirm, convert, convert_cancel]
    convert.click(lambda: [gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)], None, convert_arr)
    convert_confirm.click(lambda: [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)], None, convert_arr)
    convert_confirm.click(remove_tts_from_history, [shared.gradio[k] for k in ['name1', 'name2', 'mode']], shared.gradio['display'])
    convert_confirm.click(lambda: chat.save_history(mode='chat', timestamp=False), [], [], show_progress=False)
    convert_cancel.click(lambda: [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)], None, convert_arr)

    # Toggle message text in history
    show_text.change(lambda x: [params.update({"show_text": x}), update_config('show_text', x)], show_text, None)
    show_text.change(toggle_text_in_history, [shared.gradio[k] for k in ['name1', 'name2', 'mode']], shared.gradio['display'])
    show_text.change(lambda: chat.save_history(mode='chat', timestamp=False), [], [], show_progress=False)

    # Event functions to update the parameters in the backend
    activate.change(lambda x: [params.update({"activate": x}), update_config('activate', x)], activate, None)
    autoplay.change(lambda x: [params.update({"autoplay": x}), update_config('autoplay', x)], autoplay, None)
    tokenize.change(lambda x: [params.update({"tokenize": x}), update_config('tokenize', x)], autoplay, None)
    voice.change(lambda x: [params.update({"speaker": x}), update_config('speaker', x) ], voice, None)
    t_temp.change(lambda x: [params.update({"text_temp": x}), update_config('text_temp', x)], t_temp, None)
    w_temp.change(lambda x: [params.update({"waveform_temp": x}), update_config('waveform_temp', x) ], w_temp, None)
