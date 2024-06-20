void SetClockVars() {
  //Display all current data
  display.clearDisplay();
  display.setCursor(5, 0);
  display.print (" ");
  display.display();
  delay (100);
  display.setCursor(5, 0);
  if (rtc.getMonth() < 10)
    display.print('0');      // Trick to add leading zero for formatting
  display.print(rtc.getMonth());
  display.print("/");
  if (rtc.getDay() < 10)
    display.print('0');      // Trick to add leading zero for formatting
  display.print(rtc.getDay());
  display.print("/");
  display.print(rtc.getYear() + 2000);
  display.print("  ");
  if (rtc.getHours() < 10)
    display.print('0');      // Trick to add leading zero for formatting
  display.print(rtc.getHours());
  display.print(":");
  if (rtc.getMinutes() < 10)
    display.print('0');      // Trick to add leading zero for formatting
  display.print(rtc.getMinutes());
  display.print(":");
  if (rtc.getSeconds() < 10)
    display.print('0');      // Trick to add leading zero for formatting
  display.println(rtc.getSeconds());
  display.fillRoundRect (100, 0, 10, 10, 0, WHITE); //cover up when sometimes an extra zero occurs

  display.setCursor(5, 12);
  display.print ("    Set Variables");

  display.setCursor(5, 25);
  display.println(filename);
  display.display();

  //Adjust months
  while (SetSequence == 1) {
    display.fillRoundRect (4, 0, 12, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(5, 0);
    if (rtc.getMonth() < 10) {
      display.print(0);
    }
    display.print(rtc.getMonth());
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setMonth(rtc.getMonth() + 1);
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setMonth(rtc.getMonth() - 1);
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 2;
    }
  }

  //Adjust days
  while (SetSequence == 2) {
    display.fillRoundRect (22, 0, 12, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(23, 0);
    if (rtc.getDay() < 10) {
      display.print(0);
    }
    display.print(rtc.getDay());
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setDay(rtc.getDay() + 1);
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setDay(rtc.getDay() - 1);
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 3;
    }
  }

  //Adjust year
  while (SetSequence == 3) {
    display.fillRoundRect (40, 0, 30, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(41, 0);
    display.print(rtc.getYear() + 2000);
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setYear(rtc.getYear() + 1);
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setYear(rtc.getYear() - 1);
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 4;
    }
  }

  //Adjust hours
  while (SetSequence == 4) {
    display.fillRoundRect (77, 0, 12, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(78, 0);
    if (rtc.getHours() < 10) {
      display.print(0);
    }
    display.print(rtc.getHours());
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setHours(rtc.getHours() + 1);
      if (rtc.getHours () > 24) {
        rtc.setHours (0);
      }
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setHours(rtc.getHours() - 1);
      if (rtc.getHours () < 1) {
        rtc.setHours (24);
      }
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 5;
    }
  }

  //Adjust minutes
  while (SetSequence == 5) {
    display.fillRoundRect (95, 0, 12, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(96, 0);
    if (rtc.getMinutes() < 10) {
      display.print(0);
    }
    display.print(rtc.getMinutes());
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setMinutes(rtc.getMinutes() + 1);
      if (rtc.getMinutes () > 59) {
        rtc.setMinutes (0);
      }
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setMinutes(rtc.getMinutes() - 1);
      if (rtc.getMinutes () < 0) {
        rtc.setMinutes (59);
      }
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 6;
    }
  }


  //Adjust Seconds
  while (SetSequence == 6) {
    display.fillRoundRect (113, 0, 12, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(114, 0);
    if (rtc.getSeconds() < 10) {
      display.print(0);
    }
    display.print(rtc.getSeconds());
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      rtc.setSeconds(rtc.getSeconds() + 1);
    }
    if (digitalRead(buttonC) == LOW) {
      rtc.setSeconds(rtc.getSeconds() - 1);
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 7;
    }
  }

  while (SetSequence == 7) {
    display.fillRoundRect (22, 25, 18, 9, 0, BLACK);
    display.display();
    delay (100);

    display.setCursor(23, 25);
    if (Sip < 100 & Sip >= 10) {
      display.print ("0");
    }
    if (Sip < 10) {
      display.print ("00");
    }
    display.print (Sip);
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      Sip += 1;
    }
    if (digitalRead(buttonC) == LOW) {
      Sip -= 1;;
      if (Sip < 1) {
        Sip = 0;
      }
      if (Sip > 700) {
        Sip = 700;
      }
    }
    if (digitalRead(buttonB) == LOW) {
      display.clearDisplay();
      display.setCursor(5, 12);
      display.print ("    Variables Set!");
      display.display();
      delay (500);
      sipper.deviceNumber = Sip;
      my_flash_store.write(sipper);
      CreateFile();
      writeHeader();
      SetSequence = 0;
    }
  }
}


void SetProbabilities() {
  //Adjust probabilities
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print ("Left Probability: ");
  display.println (ShockProbLeft);
  display.println("");
  display.print ("Right Probability: ");
  display.println (ShockProbRight);
  display.display();
  delay (100);
  while (SetSequence == 10) {
    display.fillRoundRect (108, 0, 30, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(108, 0);
    display.print (ShockProbLeft);
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      ShockProbLeft += 1;
      if (ShockProbLeft > 100) ShockProbLeft = 100;
    }
    if (digitalRead(buttonC) == LOW) {
      ShockProbLeft -= 1;
      if (ShockProbLeft < 0) ShockProbLeft = 0;
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 11;
    }
  }

  while (SetSequence == 11) {
    display.fillRoundRect (108, 15, 30, 9, 0, BLACK);
    display.display();
    delay (100);
    display.setCursor(108, 15);
    display.print (ShockProbRight);
    display.display();
    delay (100);
    if (digitalRead(buttonA) == LOW) {
      ShockProbRight += 1;
      if (ShockProbRight > 100) ShockProbRight = 100;
    }
    if (digitalRead(buttonC) == LOW) {
      ShockProbRight -= 1;
      if (ShockProbRight < 0) ShockProbRight = 0;
    }
    if (digitalRead(buttonB) == LOW) {
      SetSequence = 12;
    }
  }
  display.clearDisplay();
  display.setCursor(10, 10);
  display.print ("Probabilities Set!");
  sipper.rightProb = ShockProbRight;
  sipper.leftProb = ShockProbLeft;
  my_flash_store.write(sipper);
  display.display();
  delay (1000);
}
