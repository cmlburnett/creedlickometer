/********************************************************
  Check Sippers
********************************************************/
void  CheckSippers() {
  ReadBatteryLevel();  //Read battery level
  sleeptimerfunction ();  // Is it time to log data? (Edit variable "logfreq" in a_header to change this timing)

  digitalWrite (outLeft, HIGH); // hold both outputs LOW
  digitalWrite (outRight, LOW);
  digitalWrite (shockOut, LOW);

  // Monitor Left Sip
  leftmillis = millis();

  int val = digitalRead(LeftSip);
  if (val == LOW && leftState == LOW) {
    // Do nothing
  } else if (val == HIGH && leftState == HIGH) {
    // Do nothing
  } else {
    leftState = val;
    stateChanged = 1;
  }

  val = digitalRead(RightSip);
  if (val == LOW && rightState == LOW) {
    // Do nothing
  } else if (val == HIGH && rightState == HIGH) {
    // Do nothing
  } else {
    rightState = val;
    stateChanged = 1;
  }

  shock = false;
  while (digitalRead (LeftSip) == LOW) {  // if left sip beam is broken
    digitalWrite (outLeft, HIGH); //Left output HIGH
    display.fillCircle(31, 3, 2, WHITE);
    display.display();
    if (LeftProb < ShockProbLeft and shock == false) {            //set probability of getting shocked here (hardcoded version)
      digitalWrite (shockOut, HIGH); //Shock output HIGH
      ShockCount++;
      //display right sips
      display.fillRoundRect (0, 0, 41, 8, 0, WHITE);
      display.fillCircle(31, 3, 2, BLACK);
      display.setTextColor(BLACK);
      display.setCursor(3, 0);
      display.println("Left");
      display.setCursor(4, 0);
      display.println("Left");
      display.display();
      display.setTextColor(WHITE);
      delay(1000);
      digitalWrite (shockOut, LOW); //Shock output HIGH
      shock = true;
      LeftDuration = LeftDuration - 1;                    //this is to correct for the 1 sec delay to allow the shock to happen; assume the mouse is not drinking during the shock.
    }
    if (digitalRead (LeftSip) == HIGH) {
      LeftCount++;
      LeftDuration += ((millis() - leftmillis) / 1000.0);
      LeftProb = random(1, 101);              // inclusive min and exclusive max, defining probability of being shocked
    }
  }

  // Monitor Right Sip
  rightmillis = millis();

  shock = false;
  while (digitalRead (RightSip) == LOW) { // if right sip beam is broken
    digitalWrite (outRight, HIGH);  // Right output HIGH
    display.fillCircle(83, 3, 2, WHITE);
    display.display();
    if (RightProb < ShockProbRight and shock == false) {            //set probability of getting shocked here (hardcoded version)
      digitalWrite (shockOut, HIGH); //Shock output HIGH
      ShockCount++;
      //display right sips
      display.fillRoundRect (47, 0, 41, 8, 0, WHITE);
      display.fillCircle(83, 3, 2, BLACK);
      display.setTextColor(BLACK);
      display.setCursor(50, 0);
      display.println("Right");
      display.setCursor(51, 0);
      display.println("Right");
      display.display();
      display.setTextColor(WHITE);
      delay(1000);
      digitalWrite (shockOut, LOW); //Shock output HIGH
      shock = true;
      RightDuration = RightDuration - 1;                    //this is to correct for the 1 sec delay to allow the shock to happen; assume the mouse is not drinking during the shock.
    }
    if (digitalRead (RightSip) == HIGH) {
      RightCount++;
      RightDuration += ((millis() - rightmillis) / 1000.0);
      RightProb = random(1, 101);              // inclusive min and exclusive max, defining probability of being shocked
    }
  }

  // Show time elapsed when C is pressed
  while (digitalRead (buttonC) == LOW) {
    DisplayTimeElapsed();
  }

  // Toggle between screen being off with Button B
  if (digitalRead (buttonB) == LOW) {
    if (SleepDisplay == true) {
      SleepDisplay = false;
      display.clearDisplay();
      display.setCursor(10, 10);
      display.println("Display ON");
      display.display();
      Blink (RED_LED, 50, 2);
      delay (500);
    }

    else {
      SleepDisplay = true;
      display.clearDisplay();
      display.setCursor(10, 10);
      display.println("Display OFF");
      display.display();
      Blink (RED_LED, 50, 2);
      delay (500);
    }
  }
}
