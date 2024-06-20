void LogData() {
  if ((rtc.getEpoch() - StartTime) > logtime + 10) {
    Blink(RED_LED, 50, 3);  //blink while logging
    WriteToSD();
    logfile.flush();
    delay (100);
    logtime = (rtc.getEpoch() - StartTime);
  }
}

// Create new file on uSD incrementing file name as required
void CreateFile() {
  //put this next line *Right Before* any file open line:
  SdFile::dateTimeCallback(dateTime);

  // see if the card is present and can be initialized:
  if (!SD.begin(cardSelect, SPI_HALF_SPEED)) {
    error(2);
  }

  // Name filename in format F###_MMDDYYNN, where MM is month, DD is day, YY is year, and NN is an incrementing number for the number of files initialized each day
  strcpy(filename, "SIP_____________.CSV");  // placeholder filename
  getFilename(filename);
  logfile = SD.open(filename, FILE_WRITE);

  if ( ! logfile ) {
    error(3);
  }
}

// Write data header to file of uSD.
void writeHeader() {
  logfile.println("MM:DD:YYYY hh:mm:ss, ElapsedSecs, Device, LeftCount, LeftDuration, RightCount, RightDuration, Shocks, LeftShockProbability, RightShockProbability, BatteryVoltage");
  ReadBatteryLevel();
  WriteToSD();  //Write one line of zeros to logfile to note start of session
}

// Write data to SD
void WriteToSD() {
  logfile.print(rtc.getMonth());
  logfile.print("/");
  logfile.print(rtc.getDay());
  logfile.print("/");
  logfile.print(rtc.getYear() + 2000);
  logfile.print(" ");
  logfile.print(rtc.getHours());
  logfile.print(":");
  if (rtc.getMinutes() < 10)
    logfile.print('0');      // Trick to add leading zero for formatting
  logfile.print(rtc.getMinutes());
  logfile.print(":");
  if (rtc.getSeconds() < 10)
    logfile.print('0');      // Trick to add leading zero for formatting
  logfile.print(rtc.getSeconds());
  logfile.print(",");
  logfile.print(rtc.getEpoch() - StartTime); //elapsed time
  logfile.print(",");
  logfile.print(Sip); // Print device name
  logfile.print(",");
  logfile.print(LeftCount);
  logfile.print(",");
  logfile.print(LeftDuration);
  logfile.print(",");
  logfile.print(RightCount);
  logfile.print(",");
  logfile.print(RightDuration);
  logfile.print(",");
  logfile.print(ShockCount);
  logfile.print(",");
  logfile.print(ShockProbLeft);
  logfile.print(",");
  logfile.print(ShockProbRight);
  logfile.print(",");
  logfile.println(measuredvbat); // Print battery voltage
}

void error(uint8_t errno) {
  while (1) {
    uint8_t i;
    for (i = 0; i < errno; i++) {
      DisplaySDError();
    }
  }
}

void getFilename(char *filename) {
  sipper = my_flash_store.read();
  Sip = sipper.deviceNumber;
  filename[3] = (Sip / 100) % 10 + '0';
  filename[4] = (Sip / 10) % 10 + '0';
  filename[5] = Sip % 10 + '0';
  filename[7] = rtc.getMonth() / 10 + '0';
  filename[8] = rtc.getMonth() % 10 + '0';
  filename[9] = rtc.getDay() / 10 + '0';
  filename[10] = rtc.getDay() % 10 + '0';
  filename[11] = rtc.getYear() / 10 + '0';
  filename[12] = rtc.getYear() % 10 + '0';
  filename[16] = '.';
  filename[17] = 'C';
  filename[18] = 'S';
  filename[19] = 'V';
  for (uint8_t i = 0; i < 100; i++) {
    filename[14] = '0' + i / 10;
    filename[15] = '0' + i % 10;
    // create if does not exist, do not open existing, write, sync after write
    if (! SD.exists(filename)) {
      break;
    }
  }
  return;
}

void sleeptimerfunction() {
  if (rtc.getEpoch() - sleeptimer >= 2) {  //Sleep after 2 seconds without activity on Sipper
    sleepReady = true;
  }
}
