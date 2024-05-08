import microlite          # type: ignore
from machine import Pin   # type: ignore
import io

# Define pins for buttons and LED
button_pin1 = Pin(17, Pin.IN, Pin.PULL_DOWN)
button_pin2 = Pin(16, Pin.IN, Pin.PULL_DOWN)
led_pin = Pin(25, Pin.OUT)

# Load the XOR model
xor_model_data = bytearray(1828)
model_file = io.open('model_xor.tflite', 'rb')
model_file.readinto(xor_model_data)
model_file.close()

# Define the input callback function
def input_callback(microlite_interpreter):
    input_tensor = microlite_interpreter.getInputTensor(0)
    input_tensor.setValue(0, button_pin1.value())
    input_tensor.setValue(1, button_pin2.value())

# Define the output callback function
def output_callback(microlite_interpreter):
    global prediction_result
    output_tensor = microlite_interpreter.getOutputTensor(0)
    prediction_result = output_tensor.getValue(0)

# Create the Microlite interpreter
interpreter = microlite.interpreter(xor_model_data, 2048, input_callback, output_callback)

while True:
    # Invoke the interpreter
    interpreter.invoke()

    print(f"Button1: {button_pin1.value()} Button2: {button_pin2.value()} Output: {prediction_result}")

    # If the prediction result is greater than 0.5, turn on the LED
    if prediction_result > 0.5:
        led_pin.on()
    else:
        led_pin.off()
