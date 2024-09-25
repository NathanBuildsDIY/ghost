#!/bin/python

#setup
#mkdir ghost
#cd ghost
#python -m venv venv 
# source venv/bin/activate
#python3 casper.py

#other install stuff here:
#have to use lgpio for pins
#pip install gpiozero
#sudo apt remove python3-rpi.gpio
#pip3 install rpi-lgpio

#pip3 install vosk
#pip3 install sounddevice
#sudo apt-get install libportaudio2
#pip3 install piper piper-tts pysndfx
#sudo apt install sox
#pip install pydub
#pip install librosa
#pip install soundfile

#alsamixer - up to 95%

import os, sys, random
import datetime
from piper.voice import PiperVoice
from pydub import AudioSegment
from pydub.playback import play
import wave
import numpy as np
import librosa
import soundfile as sf
from pysndfx import AudioEffectsChain
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import requests
from threading import Thread
import threading
from gpiozero import PWMLED, DistanceSensor, AngularServo
import time
from pathlib import Path
#future - ollama/ai accelerator?  Add back in arms - they suck too much power for now but separate supply would be fine

#declare things to be later used
#vosk
q = queue.Queue()
#piper
p = Path('~').expanduser()
model = str(p)+"/ghost/en_US-lessac-medium.onnx"
voice=PiperVoice.load(model)
#control flags
questionReceived = False
answerReceived = False
responseRead = True
someonePresent = False
workingdir = str(p)+"/ghost/"
os.chdir(workingdir)
#LEDs
mouth = PWMLED(21) #mouth.value = 0
eyeL1 = PWMLED(7)
eyeL2 = PWMLED(5)
eyeR1 = PWMLED(13)
eyeR2 = PWMLED(24)
#Proximity
humanPresence = DistanceSensor(echo=4, trigger=2, max_distance=3.0) #read - int(humanPresence.distance*100)
#arms - these draw too much current and maek the pi shut down randomly. Add back later w/ a separate supply
#leftArm = AngularServo(14, initial_angle=180, min_angle=0, max_angle=180, min_pulse_width=6/10000, max_pulse_width=26/10000) #leftArm.angle = 0
#rightArm = AngularServo(18, initial_angle=180, min_angle=0, max_angle=180, min_pulse_width=6/10000, max_pulse_width=26/10000)

def earQuestion():
  #adapted from https://github.com/alphacep/vosk-api/python/example/test_microphone.py
  #transcribes audio continually, breaking on silence (sentence) boundaries. Looks for a question starting with hey casper
  global questionReceived, answerReceived, responseRead, someonePresent
  device=0 #usb mic
  dump_fn = None
  try:
    device_info = sd.query_devices(device, "input")
    # soundfile expects an int, sounddevice provides a float:
    samplerate = int(device_info["default_samplerate"])
    model = Model(lang="en-us")
    listen_thread = threading.Thread(target=eyeControl, args=("listen",)) #start thread to light up mouth LED
    listen_thread.start()
    heyCasperFound = False
    with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, device=device, dtype="int16", channels=1, callback=callbackVosk):
      rec = KaldiRecognizer(model, samplerate)
      while questionReceived == False and someonePresent == True:
        data = q.get()
        if rec.AcceptWaveform(data):
          phrase = rec.Result()
          print(phrase)
          phrasejson = json.loads(phrase)
          phrasetext = phrasejson["text"]
          if phrasetext.startswith("hey casper") or phrasetext.startswith("who casper") or phrasetext.startswith("her casper") or phrasetext.startswith("he casper"):
			#remove Hey Casper
            phrasetext = phrasetext.replace("hey casper","")
            phrasetext = phrasetext.replace("who casper","")
            phrasetext = phrasetext.replace("her casper","")
            phrasetext = phrasetext.replace("he casper","")
            print("we have a valid question, logging it. Question is:", phrasetext)
			#valid question asked - save it out for reference
            f = open(workingdir+"question.txt", "w")
            f.write(phrasetext)
            f.close()
            questionReceived = True
            responseRead = False
        else:
          phrase = rec.PartialResult()
          print(phrase)
          phrasejson = json.loads(phrase)
          phrasetext = phrasejson["partial"]
          print(phrasetext)
          if heyCasperFound == False:
            if phrasetext.startswith("hey casper") or phrasetext.startswith("who casper") or phrasetext.startswith("her casper") or phrasetext.startswith("he casper"):
              hey_thread = threading.Thread(target=eyeControl, args=("heyCasper",)) #start thread to blink eyes showing start of question found
              hey_thread.start()
              heyCasperFound = True #don't constantly restart this thread 
        if dump_fn is not None:
          dump_fn.write(data)
  except KeyboardInterrupt:
    print("\nDone listening - allow to quit out")
    questionReceived = False
    answerReceived = False
    responseRead = False
def brainAnswer():
  #ask a large language model the question received. Currently using gemini, could use local LLM like llama3 but it's slow w/o accelerator
  global questionReceived, answerReceived, responseRead
  #read the saved question
  f = open(str(p)+"/ghost/question.txt",'r')
  questiontext = f.read()
  f.close()

  f = open(str(p)+"/ghost/apikey.txt",'r')
  apikey = f.read()
  f.close()
  
  #create post to send to gemini
  url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key="+apikey
  headers = {'Content-Type': 'application/json'}
  apiquestiontext = "Imagine you are a ghost who tells jokes. " + questiontext
  payload = {'contents':[{'parts':[{'text': apiquestiontext }]}]}
  res = requests.post(url, json=payload)
  resjson = json.loads(res.text)
  with open(str(p)+"/ghost/answer.txt", "w", encoding="utf-8") as f:
    f.write(resjson["candidates"][0]["content"]["parts"][0]['text'])
  #log the answer
  f = open(str(p)+"/ghost/answer.txt",'r')
  answertext = f.read()
  f.close()
  answertext = answertext.encode("ascii", "ignore") #get rid of all the emojis etc that we can't print
  print("we have an answer, it is:",answertext) 
  questionReceived = True
  answerReceived = True
def voiceAnswer():
  #user piper TTS to turn answer into audio. It's a ghost so make the voice spooky with reverb & tritones above/below
  global questionReceived, answerReceived, responseRead
  responseRead = False
  f = open(str(p)+"/ghost/answer.txt",'r')
  answer = f.read()
  answer = answer.replace("*","") #asterisks show up in responses and the reader pronounces them instead of emphasizing. So, remove
  answer = answer.replace("Spooky laughter","Ha Ha Ha He Ho,") #don't say "spooky laughter!"
  answer = answer.replace("More spooky laughter","HaHaHa,") #don't say "spooky laughter!"
  answer = answer.replace("Cue spooky laughter","HaHaHa,") #don't say "spooky laughter!"
  answer = answer.replace("more spooky laughter","HaHaHa,") #don't say "spooky laughter!"
  answer = answer.replace("cue spooky laughter","HaHaHa,") #don't say "spooky laughter!"
  answer = answer.replace("\n",",") #take pauses in audio when there's a new line
  answer = answer.encode("ascii", "ignore") #get rid of all the emojis etc that we can't read
  f.close()
  text = ["answer.wav",answer,""]
  #create the basic speech
  print(text)
  workingfile = workingdir+text[2]+text[0]
  wav_file = wave.open(workingfile, 'w')
  audio = voice.synthesize(text[1],wav_file)
  #add reverb
  fx = (AudioEffectsChain().reverb().phaser()) #removed .delay() from chain
  infile = str(text[2]+text[0])
  outfile = workingdir+'reverb.wav'
  fx(infile, outfile)
  #shift pitch up and down
  y, sr = librosa.load(workingdir+text[2]+text[0])
  y_tritoneup = librosa.effects.pitch_shift(y, sr=sr, n_steps=6) # shifted by 6 half steps
  sf.write(workingdir+'up.wav', y_tritoneup, sr, subtype='PCM_24')
  y_tritonedown = librosa.effects.pitch_shift(y, sr=sr, n_steps=-6) # shifted down tritone
  sf.write(workingdir+'down.wav', y_tritonedown, sr, subtype='PCM_24')
  #add fade to shift up and down, then mix all together
  regular = AudioSegment.from_file(workingdir+text[2]+text[0], format="wav")
  regular_reverb = AudioSegment.from_file('reverb.wav', format="wav")
  regular_up = AudioSegment.from_file(workingdir+'/up.wav', format="wav")
  regular_down = AudioSegment.from_file(workingdir+'/down.wav', format="wav")
  #fade first
  seconds = 0
  regular_upfade = regular_up[0:10]
  while seconds < regular_up.duration_seconds:
    regular_upfade = regular_upfade + regular_up[seconds*1000:seconds*1000+1500].fade_in(1000) 
    regular_upfade = regular_upfade + regular_up[seconds*1000+1500:seconds*1000+3000].fade_out(1000) 
    seconds = seconds + 3
  seconds = 0
  regular_downfade = regular_down[0:10]
  while seconds < regular_down.duration_seconds:
    regular_downfade = regular_downfade + regular_down[seconds*1000:seconds*1000+1500].fade_out(1000) 
    regular_downfade = regular_downfade + regular_down[seconds*1000+1500:seconds*1000+3000].fade_in(1000) 
    seconds = seconds + 3
  #now mix
  overlay_words = regular_reverb.overlay(regular, position=0).overlay(regular_upfade, position=0).overlay(regular_downfade, position = 0)
  #overlay_words = regular.overlay(regular_upfade, position=0).overlay(regular_downfade, position = 0)
  overlay_words.export(text[2]+text[0], format="wav") 
  questionReceived = False
  answerReceived = False
  responseRead = True
def callbackVosk(indata, frames, time, status):
  """This is used by earQuestion - vosk, called (from a separate thread) for each audio block."""
  if status:
    print(status, file=sys.stderr)
  q.put(bytes(indata))
def playStallResponse():
  #it takes time to create the audio for the answer (2-10 seconds), so say some stall words/play music
  random_file = random.choice(os.listdir(workingdir+'stall/')) #get a random background song
  stallAudio = AudioSegment.from_file(workingdir+'stall/'+random_file, format="wav")
  playAudioWithMouth(stallAudio)
def playMusic():
  while questionReceived == True:
    #play music while we process question
    random_file = random.choice(os.listdir(workingdir+'music/')) #get a random background song
    stallMusic = AudioSegment.from_file(workingdir+'music/'+random_file, format="wav")
    play(stallMusic)
def playAudioWithMouth(segment):
  #helper to light up mouth on one thread while playing audio on another
  playback_thread = threading.Thread(target=lightMouthFollowingAudioIntensity, args=(segment,)) #start thread to light up mouth LED
  playback_thread.start()
  play(segment) #actually play audio
def lightMouthFollowingAudioIntensity(segment):
  eyeL1.value = 0.25; eyeR1.value = 0.25; #also turn on eyes while mouth changes intensity
  timer = 0
  duration = 0.1 * 0.75 # Duration to print peak amplitude in seconds. Scale by 75% because of compute overhead - syncs w/ audio
  while timer < segment.duration_seconds:
    # Calculate peak amplitude
    peak_amplitude = segment[timer*1000:timer*1000 + duration*1000].dBFS
    intensity = (peak_amplitude+100)/150-.5 #scales it down a bit because LED brightness isn't linear, seems really bright even at low values
    if intensity < 0.05:
      intensity = 0 #clip on intensity to get obvious on/off and to avoid going under 0
    mouth.value = intensity
    eyeL2.value = intensity
    eyeR2.value = intensity
    time.sleep(duration)
    timer = timer + duration
  mouth.value = 0; eyeL1.value = 0; eyeR1.value = 0; eyeL2.value = 0; eyeR2.value = 0; #turn all of now that done talking
def eyeControl(mode):
  global questionReceived, responseRead
  #all eye threads stop when global flags are changed between modes so we can start threads w/o worry of them going forever
  if mode == "listen":
    print("starting eye control Listen mode - eyes on")
    while questionReceived == False:
      eyeL1.value = 0.25
      eyeR1.value = 0.25
  if mode == "heyCasper":
    print("starting eye control hey casper - eyes flash after hey casper is heard")
    #flash top eyes on recognition of key word until full quesiton is received
    while questionReceived == False:
      eyeL2.value = 1
      eyeR2.value = 1
      time.sleep(0.3)
      eyeL2.value = 0
      eyeR2.value = 0
      time.sleep(0.3)      
  if mode == "stall":
    print("running stall eye blink")
    while responseRead == False:
      eyeL2.value = 1
      eyeR2.value = 1
      time.sleep(0.3)
      eyeL2.value = 0.25
      eyeR2.value = 0.25
      time.sleep(0.3)     
      eyeL2.value = 0
      eyeR2.value = 0
      time.sleep(0.3)
      eyeL2.value = 0.25
      eyeR2.value = 0.25
      time.sleep(0.3)
  
def main():
  global questionReceived, answerReceived, responseRead, someonePresent
  try:
    while True:
      distanceObserved = int(humanPresence.distance*100)
      time.sleep(0.2)
      print("Distance Observed:",str(distanceObserved))
      if distanceObserved < 140:
        someonePresent = True #distance sensor sees something close by
        #say hello
        random_file = random.choice(os.listdir(workingdir+'greet/')) #get a random greeting
        greetingAudio = AudioSegment.from_file(workingdir+'greet/'+random_file, format="wav")
        playAudioWithMouth(greetingAudio)
        while someonePresent == True:
          if questionReceived == False and answerReceived == False and responseRead == True:
            print("Turning on ears to listen for question")
            earQuestion()
          if questionReceived == True and answerReceived == False:
            musicThread = threading.Thread(target=playMusic, args=()) #start background music while we process/play response
            musicThread.start()
            print("Turning on brain, question received")
            brainAnswer()
          if answerReceived == True:
            print("turning on voice generation, playing stall phrase, response generated")
            eyeStallThread = threading.Thread(target=eyeControl, args=("stall",)) #start background music for 30 seconds
            eyeStallThread.start()
            threads = [Thread(target=voiceAnswer, args=()), Thread(target=playStallResponse, args=())] #calculate response audio & play a stall phrase
            # Start all threads.
            for t in threads:
              t.start()
            # Wait for all threads to finish.
            for t in threads:
              t.join()
            print("playing response")
            answerAudio = AudioSegment.from_file('answer.wav', format="wav")
            playAudioWithMouth(answerAudio)
          if int(humanPresence.distance*100) > 170:
            someonePresent = False
        #just detected someonePresent == False, say goodbye
        random_file = random.choice(os.listdir(workingdir+'bye/')) #get a random background song
        byeAudio = AudioSegment.from_file(workingdir+'bye/'+random_file, format="wav")
        playAudioWithMouth(byeAudio)
  except KeyboardInterrupt:
    print("\nLeaving program")

if __name__=="__main__":
  main()
