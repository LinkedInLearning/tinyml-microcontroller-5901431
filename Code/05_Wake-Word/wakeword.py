# The MIT License (MIT)
# Copyright (c) 2021 Michael O'Cleirigh
# https://opensource.org/licenses/MIT
#
#
# This started from the i2s examples and was then combined with the micro_speech C++ example
# from tensorflow.
#
# i2s example: https://github.com/miketeachman/micropython-i2s-examples/blob/master/examples/record-mic-to-sdcard-non-blocking.py
# tensorflow: https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite/micro/examples/micro_speech

import gc
import io
from ulab import numpy as np    # type: ignore
import micro_speech             # type: ignore
from results import Results
import microlite                # type: ignore
import utime                    # type: ignore
from machine import Pin, I2S    # type: ignore


model_size = 18960
wake_words = ["yes", "no"]
# wake_words = ["marvin", "stop"]
model_name = f"model_{wake_words[0]}_{wake_words[1]}.tflite"

print_store_results = False

micro_speech_model = bytearray(model_size)
model_file = io.open(model_name, 'rb')
model_file.readinto(micro_speech_model)
model_file.close()

def input_callback (microlite_interpreter):

	inputTensor = microlite_interpreter.getInputTensor(0)
	featureData.setInputTensorValues(inputTensor)
	
def output_callback (microlite_interpreter):
	outputTensor = microlite_interpreter.getOutputTensor(0)

	results.storeResults({
		"silence": outputTensor.getValue(0), 
		"unknown": outputTensor.getValue(1), 
		wake_words[0]: outputTensor.getValue(2), 
		wake_words[1]: outputTensor.getValue(3)
		})

try:
	print ("starting interpreter\n")
	interp = microlite.interpreter(micro_speech_model, model_size, input_callback, output_callback)
	print ("interpreter started\n")

except (KeyboardInterrupt, Exception) as e:
	print('caught exception {} {}'.format(type(e).__name__, e))
	raise

featureData = micro_speech.FeatureData(interp)

inferences = 0

print('starting...')

classes = ["silence", "unknown", wake_words[0], wake_words[1]]
results = Results(classes)

pgm_start = utime.ticks_ms()

samplingDelayMs = const(10)
inferenceDelayMs = const (500)

def processAudio(i2s):
	global bytesReadPerSecond
	global totalSlices
	global printPerSecondStats
	global audio_in
	global mic_samples_mv
	global bytes_processed_since_last_inference
	global trailing_10ms
	global num_read
	global featureData
	global inferenceNeeded

	try:
		gc.collect()
		audio_samples = np.frombuffer(mic_samples_mv[:num_read], dtype=np.int16)
		trailing_10ms = micro_speech.segmentAudio(featureData, audio_samples, trailing_10ms)
		num_read = audio_in.readinto(mic_samples_mv)

	except (KeyboardInterrupt, Exception) as e:
		print('caught exception {} {}'.format(type(e).__name__, e))
		audio_in.deinit()
		raise

printPerSecondStats = False

led = Pin(25, Pin.OUT)

bck_pin  = Pin(0)  # BCLK
ws_pin   = Pin(1)  # LRCLK
sdin_pin = Pin(2)  # DOUT

# https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/pinouts
#
# BCLK  - the bit clock, also known as the data clock or just 'clock' - 
#         comes from the I2S main to tell the microphone its time to transmit data. 
# DOUT  - the data output from the mic!
# LRCLK - the left/right clock, also known as WS (word select), 
#         this tells the mic when to start transmitting.
#         When the LRCLK is low, the left channel will transmit.
#         When LRCLK is high, the right channel will transmit.

audio_in = I2S(
	0,
	sck=bck_pin,
	ws=ws_pin,
	sd=sdin_pin,
	mode=I2S.RX,
	bits=16,
	format=I2S.MONO,
	rate=16000,
	ibuf=9600
)

mic_samples = bytearray(3200)
mic_samples_mv = memoryview(mic_samples)

trailing_10ms = np.zeros(160, dtype=np.int16)

audio_in.irq(processAudio)

num_read = audio_in.readinto(mic_samples_mv)

inferenceNeeded = False

def timerCallback(timer):
	global printPerSecondStats
	printPerSecondStats = True

bytes_processed_since_last_inference = 0
time_of_last_inference = utime.ticks_ms()

def runModel():
	global inferences
	global interp
	global results
	global bytes_processed_since_last_inference
	global time_of_last_inference

	interp.invoke()

	bytes_processed_since_last_inference = 0
	time_of_last_inference = utime.ticks_ms()

	inferences = inferences + 1

	score = results.computeResults()

	if score != None:
		if score.kind == wake_words[0] or score.kind == wake_words[1]:
			print ("found - %s at %d seconds -> %d\n" % (score.kind, utime.ticks_diff(time_of_last_inference, pgm_start)/1000, score.score))
			if score.kind == wake_words[0]:
				## LED on
				led.on()
			else:
				## LED off
				led.off()

			results.resetScore()
			featureData.reset()

print("ready to listen");

try:
	while True:
		gc.collect()
		runModel()

except (KeyboardInterrupt, Exception) as e:
	print('caught exception {} {}'.format(type(e).__name__, e))
	raise
finally:
	audio_in.deinit()
	print('Done')
