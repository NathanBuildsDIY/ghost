echo "get up to date packages with apt-get"
sudo apt-get update
sudo apt-get -y upgrade

echo "install pip so we can install other things"
sudo apt-get -y install pip

echo "setup venv"
cd ~/ghost
python -m venv venv 
source venv/bin/activate

echo "setup gpiozero"
pip install gpiozero
sudo apt remove python3-rpi.gpio
pip3 install rpi-lgpio

echo "install TTS and STT and audio mixing stuff"
pip3 install vosk
pip3 install sounddevice
sudo apt-get install libportaudio2
pip3 install piper piper-tts pysndfx
sudo apt install sox
pip install pydub
pip install librosa
pip install soundfile

echo "download voice files for piper tts"
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

echo "create entry in crontab to always run weeder app on startup"
line="@reboot ~/ghost/venv/bin/python ~/ghost/casper.py >> ~/ghost/log.out 2>&1"
(crontab -u $(whoami) -l; echo "$line" ) | crontab -u $(whoami) -

echo "done with installs.  After reboot, casper will start automatically."
echo "Remember to create apikey.txt in the ~/ghost/apikey.txt file, it will be used to contact gemini"
echo "address for apikey is https://console.developers.google.com/   You'll need a google account to get in."
echo "see associated youtube video for details if you need them"
echo "Also run alsamixer and press the up arrow until volume is 90% or greater so your speaker will be loud"
