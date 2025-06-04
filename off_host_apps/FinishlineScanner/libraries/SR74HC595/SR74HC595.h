#ifndef SR74HC595_h
#define SR74HC595_h
#define __SR74HC595_VERSION__ 1.0.0.0
#include "Arduino.h"

class SR74HC595		
{									
  private:
	uint8_t clkpin=0; 		//74HC595 clock pin
	uint8_t datapin=0; 		//74HC595 data pin
	uint8_t latchpin=0; 		//74HC595 latch pin
	uint8_t dataRegister=0;
	
	void initializePins();
	void clock();
	void store();
	void serialToParallel();

  public:

  	SR74HC595(uint8_t _Data,uint8_t _Clk, uint8_t _Latch); 
	void sendToShiftRegister(uint8_t*,uint8_t srNos);
	void sendToShiftRegister(uint8_t data);
};

#endif 
