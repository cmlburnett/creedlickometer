/********************************************************
   FUNCTION IS CALLED WHEN Sipper_PIN IS INTERRUPTED
  *****************************************************/
void wake() {
  digitalWrite(GREEN_LED, HIGH);
  sleeptimer = rtc.getEpoch();  //reset sleeptimer if either poke is triggered, so device doesn't go to sleep right after interrupt which sometimes caused a freeze up
  BeAwake = true;
}

/********************************************************
   FUNCTION FOR PUTTING THE ADALOGGER TO SLEEP
 *****************************************************/
void GoToSleep () {
  if (sleepReady == true and (rtc.getEpoch() - StartTime) > 10) {  //don't sleep in first 10 seconds
    sleepReady = false;
    sleeptimer = rtc.getEpoch();
    BeAwake = false;
    digitalWrite(GREEN_LED, LOW);
    UpdateDisplay();
    if (SleepDisplay  == true) {
      delay (100);
      display.ssd1306_command(SSD1306_DISPLAYOFF);
    }
    delay (100);  //make sure everything is finished before turning off processor
    SysTick->CTRL &= ~SysTick_CTRL_TICKINT_Msk;  //To stop SAMD21 freeze problem during sleep documented here: https://www.avrfreaks.net/forum/samd21-samd21e16b-sporadically-locks-and-does-not-wake-standby-sleep-mode
    rtc.standbyMode();
    SysTick->CTRL |= SysTick_CTRL_TICKINT_Msk;
  }
}

void wakeUp() {
  if (BeAwake == true) {
    if (SleepDisplay  == true) {
      display.ssd1306_command(SSD1306_DISPLAYON);
    }
    Adafruit_SSD1306 display(OLED_RESET);
  }
}
