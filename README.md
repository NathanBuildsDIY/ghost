These are the plans - schematics, parts, code for an AI powered talking/listening ghost that tells jokes and answer questions. See the youtube video for details on how to assemble/use.  To install this repo:
1. Get a raspberry pi 5 8GB and install the latest OS on an SD card with pi imager
2. Clone this repo - git clone https://github.com/NathanBuildsDIY/ghost
3. run the install.sh script included in this repository
4. Build the ghost with LED's and speaker/microphone and install in the 3d printed head as per the youtube video. Then cloak in a white sheet.
5. Get an API key from google so you can access gemini (this is free with any google acct, up to 15 requests/minute). https://console.developers.google.com/  Put it in a file called ~/ghost/apikey.txt
6. Run alsamixer from the command line. press up arrow until volume of speaker is >90% so speaker is nice and loud.
