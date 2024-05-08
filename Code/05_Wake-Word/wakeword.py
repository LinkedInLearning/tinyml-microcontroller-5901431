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
from ulab import numpy as np              # type: ignore
import micro_speech                       # type: ignore
import microlite                          # type: ignore
import utime                              # type: ignore
from machine import Timer, Pin, I2S       # type: ignore
import math


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
	


totalSlices = 0

kSilenceIndex = const (0)
kUnknownIndex = const (1)
kYesIndex = const (2)
kNoIndex = const (3)

scoreThreshold = const (200)
startValue = const (0)

class Score:

	def __init__(self, kind, score):
		self.kind = kind
		self.score = score

class Results:

	def __init__(self):
		self.silence_data = []
		self.unknown_data = []
		self.yes_data = []
		self.no_data  = []

		self.nextIndex = 0

		self.score = Score("unknown", startValue)

		for i in range (3):
			self.silence_data.append(startValue)
			self.unknown_data.append(startValue)
			self.yes_data.append(startValue)
			self.no_data.append(startValue)

	def _computeAverageTotal (self, array_data):
		total = 0

		array_length = len(array_data)

		for i in range (array_length):
			total = total + array_data[i]

		return math.floor(total / array_length)

	def computeResults(self):

		# total occurances over threshold
		totalSilence = 0
		totalUnknown = 0
		totalYes = 0
		totalNo = 0

		for index in range(3):

			silence = self.silence_data[index]
			unknown = self.unknown_data[index]
			yes     = self.yes_data[index]
			no      = self.no_data[index]

			if silence > scoreThreshold:
				totalSilence = totalSilence + 1

			if unknown > scoreThreshold:
				totalUnknown = totalUnknown + 1

			if yes > scoreThreshold:
				totalYes = totalYes + 1

			if no > scoreThreshold:
				totalNo = totalNo + 1

		topScore = totalSilence
		topScoreKind = "silence"

		if totalUnknown > topScore:
			topScoreKind = "unknown"
			topScore = totalUnknown

		if totalYes > topScore:
			topScoreKind = "yes"
			topScore = totalYes

		if totalNo > topScore:
			topScoreKind = "no"
			topScore = totalNo


		if topScore > 0:
			self.score.kind = topScoreKind
			self.score.score = topScore
		else:
			self.score.kind = "unknown"
			self.score.score = startValue

		return self.score

	def resetScore(self):
		self.nextIndex = 0

		for i in range (len(self.silence_data)):
			self.silence_data[i] = startValue
			self.unknown_data[i] = startValue
			self.yes_data[i] = startValue
			self.no_data[i] = startValue

		self.score.kind = "unknown"
		self.score.score = startValue

	def storeResults(self, silenceScore, unknownScore, yesScore, noScore):

		if print_store_results and silenceScore + 128 < 5:
			print("storeResults: nextIndex=%d,silence=%d, unknown=%d, yes=%d, no=%d\n" %(self.nextIndex,silenceScore + 128, unknownScore + 128, yesScore + 128, noScore + 128))

		if self.nextIndex == 2:
			self.nextIndex = 0
		else:
			self.nextIndex = self.nextIndex + 1

		index = self.nextIndex

		self.silence_data[index] = silenceScore + 128
		self.unknown_data[index] = unknownScore + 128
		self.yes_data[index] = yesScore + 128
		self.no_data[index] = noScore + 128

results = Results()

def output_callback (microlite_interpreter):
	# print ("output callback")

	outputTensor = microlite_interpreter.getOutputTensor(0)

	# we expect there to be a category

	silence = outputTensor.getValue(kSilenceIndex)
	unknown = outputTensor.getValue(kUnknownIndex)
	yes     = outputTensor.getValue(kYesIndex)
	no      = outputTensor.getValue(kNoIndex)

	results.storeResults(silence, unknown, yes, no)


try:
	print ("starting interpreter\n")
	interp = microlite.interpreter(micro_speech_model,10 * 1024, input_callback, output_callback)
	print ("interpreter started\n")

except (KeyboardInterrupt, Exception) as e:
	print('caught exception {} {}'.format(type(e).__name__, e))
	raise



featureData = micro_speech.FeatureData(interp)



inferences = 0


print('Starting')

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

		start = utime.ticks_ms()

		audio_samples = np.frombuffer(mic_samples_mv[:num_read], dtype=np.int16)

		trailing_10ms = micro_speech.segmentAudio(featureData, audio_samples, trailing_10ms)


		complete = utime.ticks_ms()


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
# BCLK - the bit clock, also known as the data clock or just 'clock' - comes from the I2S main to tell the microphone its time to transmit data. This should run at 2-4 MHz but we've found you can often run it a little slower and it'll work fine
# DOUT - the data output from the mic!
# LRCLK - the left/right clock, also known as WS (word select), this tells the mic when to start transmitting. When the LRCLK is low, the left channel will transmit. When LRCLK is high, the right channel will transmit.



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

	start = utime.ticks_ms()

	interp.invoke()

	complete = utime.ticks_ms()

	bytes_processed_since_last_inference = 0
	time_of_last_inference = utime.ticks_ms()

	inferences = inferences + 1

	score = results.computeResults()

	if score != None:
		if score.kind == "yes" or score.kind == "no":
			print ("found - %s at %d seconds -> %d\n" % (score.kind, utime.ticks_diff(time_of_last_inference, pgm_start)/1000, score.score))
			if score.kind == "yes":
				## LED on
				led.on()
			else:
				## LED off
				led.off()

			#featureData.writeSpectogramValues(score.kind, dump_spectrograms)
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
