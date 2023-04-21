# BARK Text-to-Audio Extension for Oobabooga

This extension uses [suno-ai/bark](https://github.com/suno-ai/bark/) to add audio synthesis to [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui). Bark is a powerful transformer-based text-to-audio solution, capable of producing realistic speech output with natural inflection and cadence, and even generating nonverbal communication such as laughing, sighing or crying. Emotions can be controlled using a trigger word in brackets, such as `[laughs]`. Bark is limited to generating up to 40 tokens at a time, or about 15 seconds of audio. Those 40 tokens are not the same as text tokens, and as such there's no way to set a matching token limit for the language model - you'll have to experiment yourself. Also, be aware that Bark has pretty steep hardware requirements, it increases VRAM requirements by several gigabytes and is currently about four times slower than realtime on my AMD 7900XTX, at roughly one minute per 15 seconds of audio, though this should improve significantly in the coming days, once [#27](https://github.com/suno-ai/bark/pull/27) is merged. If you compile Bark yourself with the linked patch, make sure you use the `k/v` branch of this extension.

## Installation
Clone this repository into your `text-generation-webui/extensions` folder, activate the virtual environment, install the requirements and launch the web UI with `--extension bark_tts`.
```
source venv/bin/activate
cd extensions
git clone https://github.com/wsippel/bark_tts.git
pip install -r bark_tts/requirements.txt
cd ..
python server.py --extension bark_tts
```