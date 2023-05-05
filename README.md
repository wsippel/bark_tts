# BARK Text-to-Audio Extension for Oobabooga

This extension uses [suno-ai/bark](https://github.com/suno-ai/bark/) to add audio synthesis to [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui). Bark is a powerful transformer-based text-to-audio solution, capable of producing realistic speech output with natural inflection and cadence, and can even generate nonverbal communication such as laughing, sighing or crying. Emotions can be controlled using a trigger word in brackets, such as `[sad]` or `[laughs]`. Bark itself is limited to generating up to 15 seconds of audio at a time, so bark_tts uses NLTK to split text into individual sentences, joins short sentences up to a maximum of 250 text tokens by default, processes those chunks individually, then concatenates the resulting audio files. This approach doesn't work well with all speakers, and adds additional overhead, so I made it a toggle. I'm sure there's room for improvement here. Also, be aware that Bark has pretty steep hardware requirements, it needs several gigabytes of VRAM and a flagship GPU to achieve realtime generation speeds.

## Troubleshooting
Bark was only just released and the API isn't stable yet. I try to implement the latest features as they become available, which is going to break installations. You should ideally reinstall Bark whenever you update the extension for the time being, or at least whenever something breaks. Just `pip uninstall suno-bark`, then repeat the `pip install -r requirements.txt` step as outlined in the installation instructions. 

Also note that this extension, just like several of Oobabooga's built-in extensions, only works in chat and cai-chat mode, so make sure you launch the web UI with the `--chat` or `--cai-chat` argument.

## Custom speakers
If you have custom speakers from one of the Bark forks, just put the `.npz` files in the `voices` folder and restart the web UI. They'll be at the top of the speaker dropdown. Make sure the filenames start with the appropriate language prefix. For example, the file for your custom English `mycustomspeaker` should be named `en_mycustomspeaker.npz`.

## Installation
***TLDR:*** Clone this repository into your `text-generation-webui/extensions` folder, activate the virtual environment, install the requirements and launch the web UI with `--extension bark_tts`. 

### Linux
On Linux or WSL with a standard Python virtual environment, it would look something like this:
```
source venv/bin/activate
cd extensions
git clone https://github.com/wsippel/bark_tts.git
pip install -r bark_tts/requirements.txt
cd ..
python server.py --chat --extension bark_tts
```

### Windows
>**Note:** These instructions assume you have installed Oobabooga using the One-Click Installer.

There are two versions of the Oobabooga One-Click installer that slightly modify the install. To determine which version you have, navigate to the directory you have cloned Oobabooga (the folder that contains the text-generation-webui folder). 
 - If you have the old version you will see a batch file named `micromamba-cmd.bat`
 - If you have the new version you will see a batch file named `cmd_windows.bat`

The instructions apply the same to both, they just have different names. I will refer to these files as "Environment Batch File".

Run the Environment Batch File and enter the following commands:
```
cd text-generation-webui\extensions
git clone https://github.com/wsippel/bark_tts.git
pip install -r bark_tts/requirements.txt
```
Once that has completed, you can close the Environment Batch File.

- If you have the old version of Oobabooga's installer, add `--extensions bark_tts` to the end of the `call python server.py` line in the `start-webui.bat` file.
- If you have the new version of Oobabooga's installer, add `--extensions bark_tts` at the end of the inside of the brackets on the `run_cmd("python server.py")` line in the `webui.py` file so it looks like `run_cmd("python server.py --extensions bark_tts")`. (The line is near the bottom of the file).

Once done, save and close the file and you can run the WebUI as normal.

The first launch after installation will be slow as the models for bark download.

#### Reinstallation
If reinstalling bark_tts:
- Ensure you delete any folder referring to bark_tts in your `text-generation-webui\extensions` folder.
- Start your Environment Batch File and run the command `pip uninstall suno-bark`.
- Continue with the normal installation process above.


## Configuration
bark_tts now saves all settings to a configuration file named `bark_tts.ini`, so they are persistant between runs. Additionally, manually editing the `bark_internals` section in `bark_tts.ini` allows you to switch to Bark's smaller models (for users with limited VRAM), or move all or parts of the processing to the CPU (very slow). By default, bark_tts always uses the highest quality models and generates on the GPU if possible. Users with lower-end or unsupported hardware might want to edit the configuration file. Once Suno provides proper documentation, I will update this section to clarify what the individual performance settings do.
