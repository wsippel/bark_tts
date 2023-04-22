# BARK Text-to-Audio Extension for Oobabooga

This extension uses [suno-ai/bark](https://github.com/suno-ai/bark/) to add audio synthesis to [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui). Bark is a powerful transformer-based text-to-audio solution, capable of producing realistic speech output with natural inflection and cadence, and can even generate nonverbal communication such as laughing, sighing or crying. Emotions can be controlled using a trigger word in brackets, such as `[laughs]`. Bark is limited to generating up to 15 seconds of audio at a time, so bark_tts uses NLTK to split text into individual sentences by default. This approach doesn't work well with all speakers, and adds additional overhead, so I made it a toggle. I'm sure there's room for improvement here. Also, be aware that Bark has pretty steep hardware requirements, it needs several gigabytes of VRAM and a flagship GPU to achieve realtime generation speeds.

## Installation
Clone this repository into your `text-generation-webui/extensions` folder, activate the virtual environment, install the requirements and launch the web UI with `--extension bark_tts`. On Linux or WSL with a standard Python virtual environment, it would look something like this:
```
source venv/bin/activate
cd extensions
git clone https://github.com/wsippel/bark_tts.git
pip install -r bark_tts/requirements.txt
cd ..
python server.py --extension bark_tts
```