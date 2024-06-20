/********************************************************
  Sipper counter v2.1.0
  Written by Lex Kravitz and Meaghan Creed
  https://hackaday.io/project/160388-automated-mouse-homecage-two-bottle-choice-test-v2

  October, 2020

  Minor revision to version 2.1.0 with following changes:
  - Improved timekeeping for sipper durations.
  - Implemented sleep functionality to improve battery life ~3.5x (estimated to last ~45 days now with screen off, ~30days with screen on)
  - Added "shock" output functionality with customizable left/right probabilities that can be modified from the device by holding Button "C" at startup screen.
      This functionality will send a 1s pulse to Pin 12 at user-set probabilities
  - Improved graphics displays on sipper screen

  This project code includes code from:
  *** Adafruit, who made the hardware breakout boards and associated code ***

  Cavemoa's excellent examples of datalogging with the Adalogger:
  https://github.com/cavemoa/Feather-M0-Adalogger

  Uses Arduino Time library http://playground.arduino.cc/code/time
  Maintained by Paul Stoffregen https://github.com/PaulStoffregen/Time

  Uses Arduino Zero RTC library https://www.arduino.cc/en/Reference/RTC
  Maintained by Arturo Guadalupi https://github.com/arduino-libraries/RTCZero

  This project is released under The MIT license:

  Copyright (c) 2020 Meaghan Kravitz

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
********************************************************/


/********************************************************
  Setup code
********************************************************/
#include "a_Header.h" //See "a_Header.h" for #defines and other constants 

void setup() {
  StartUpCommands();
}

/********************************************************
  Main loop
********************************************************/
void loop() {
  UpdateDisplay();
  CheckSippers();
  LogData();
  GoToSleep ();
  wakeUp();
}
