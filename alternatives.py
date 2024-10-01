#/bin/python
#this is a group of gists so that you can try out other STT, TTS and local LLM models  
#Just uncomment the big block of 3 quotes, install the prerequs and test out
#this has been tested on raspberry pi 5, ymmv on other devices
#remember to source venv/bin/activate in ghost directory to install things via pip in pi 5

######## STT ##########
#whisper streaming - longer delay than vosk, but more accurate. Stability issues though. 
'''
#git clone https://github.com/ufal/whisper_streaming/
#edit the whisper_online.py to use CPU instead of gpu
#sudo apt-get install ncat
#Test on a static file
# python3 whisper_online.py ../welcome.wav --language en --min-chunk-size 1 --backend faster-whisper --model tiny > out.txt
#
# Stream translate from microphone
# python3 whisper_online_server.py --language en --min-chunk-size 1 --model tiny --backend faster-whisper --host localhost > out.txt #start the server
# arecord -f S16_LE -c1 -r 16000 -t raw -D default | nc localhost 43007 #direct microphone to server port
'''

#c++ compiled whisper - faster on pi?
#pip install git+https://github.com/AIWintermuteAI/whispercpp.git -vv
#go wait awhile - this takes some time :)
#python3 whispercpp/examples/stream/stream.py

# speech recognition package - google translate and whisper translate both available. 
# However, pyaudio install via pip seems to make my audio garbled. Alsa errors present in spite of fixing up alsa config file.
# Also, issue is latency - 3-12 seconds. 
'''
#sudo apt install portaudio19-dev python3-pyaudio python3-all-dev
#pip3 install pyaudio
#pip3 install speechrecognition
#sudo vi /usr/share/alsa/alsa.conf   change default card to 2, device stays 0. that's the mic I have (arcord -l)
# google recognize
#pip install google-cloud-speech
#sudo apt-get install flac
# whisper recognize
#python3 -m pip install SpeechRecognition[whisper-local]

import speech_recognition as sr
r = sr.Recognizer()
while(1):    
    
    # Exception handling to handle
    # exceptions at the runtime
    try:
        
        # use the microphone as source for input.
        with sr.Microphone() as source2:
            
            # wait for a second to let the recognizer
            # adjust the energy threshold based on
            # the surrounding noise level 
            r.adjust_for_ambient_noise(source2, duration=0.2)
            
            #listens for the user's input 
            audio2 = r.listen(source2)
            
            # Using google to recognize audio
            MyText = r.recognize_google(audio2)
            #MyText = r.recognize_whisper(audio2)
            MyText = MyText.lower()

            print("Did you say",MyText)
            #SpeakText(MyText)
            
    except sr.RequestError as e:
        print("Could not request results")
        
    except sr.UnknownValueError:
        print("unknown error occurred")
'''

# realtimestt
# Requires pyaudio, but doesn't break the speaker?  Latency is 3-4 seconds.  ALSA errors abound though.
'''
#pip install RealtimeSTT
#sudo apt-get install ffmpeg
#Note on pi 5 - porcupine doesn't work yet, and this originally used porcupine for wake word detection. I removed it as shown in # comments below
#from RealtimeSTT import AudioToTextRecorder
#if __name__ == '__main__':
#    recorder = AudioToTextRecorder(spinner=False, model="tiny.en", language="en")
#
#    print("Say something...")
#    while (True): print(recorder.text(), end=" ", flush=True)
#had to get in and comment out porcupine wake because it wouldn't install as well.

from RealtimeSTT import AudioToTextRecorder
from colorama import Fore, Back, Style
import colorama
import os

if __name__ == '__main__':

    print("Initializing RealtimeSTT test...")

    colorama.init()

    full_sentences = []
    displayed_text = ""

    def clear_console():
        os.system('clear' if os.name == 'posix' else 'cls')

    def text_detected(text):
        global displayed_text
        sentences_with_style = [
            f"{Fore.YELLOW + sentence + Style.RESET_ALL if i % 2 == 0 else Fore.CYAN + sentence + Style.RESET_ALL} "
            for i, sentence in enumerate(full_sentences)
        ]
        new_text = "".join(sentences_with_style).strip() + " " + text if len(sentences_with_style) > 0 else text

        if new_text != displayed_text:
            displayed_text = new_text
            clear_console()
            print(f"Language: {recorder.detected_language} (realtime: {recorder.detected_realtime_language})")
            print(displayed_text, end="", flush=True)

    def process_text(text):
        full_sentences.append(text)
        text_detected("")

    recorder_config = {
        'spinner': False,
        'model': 'tiny',
        'silero_sensitivity': 0.4,
        'webrtc_sensitivity': 2,
        'post_speech_silence_duration': 0.4,
        'min_length_of_recording': 0,
        'min_gap_between_recordings': 0,
        'enable_realtime_transcription': True,
        'realtime_processing_pause': 0.2,
        'realtime_model_type': 'tiny',
        'on_realtime_transcription_update': text_detected, 
        'silero_deactivity_detection': True,
    }

    recorder = AudioToTextRecorder(**recorder_config)

    clear_console()
    print("Say something...", end="", flush=True)

    while True:
        recorder.text(process_text)
'''

######### LLM #########
#ollama - phi3 is slow, responses are hit and msis. tinyllama is fast, but not very creative. llama3 is great, but slow.

#install steps
#curl -fsSL https://ollama.com/install.sh | sh
#pip install ollama

#Command line test, do this first - this is useful b/c it downloads the model
#ollama run <model name> - popular model names are - tinyllama gemma llava llama3 phi3
'''
#to use in python, do this:
from ollama import generate
response = generate('tinyllama', 'Pretend you are a ghost who tells jokes. Why is the sky blue?')
print(response['response'])
'''

###### TTS #######
#flite - there are other voices better than the default, but they're not as good as piper TTS IMHO
#sudo apt install flite
#flite -t "All good men come to the aid of the rebellion"
#flite -voice slt -t "All good men come to the aid of the rebellion" #this is a better voice
