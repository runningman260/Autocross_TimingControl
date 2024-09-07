#include "SR74HC595.h"

/////////////////////////////////////////////////INSTANT/INIT DEFINITION/////////////////////////////////////////////////

SR74HC595::SR74HC595(uint8_t _Data,uint8_t _Clk, uint8_t _Latch)
{
  	datapin = _Data;
	clkpin = _Clk;
	latchpin = _Latch;
	initializePins();
}

////////////////////////////////////////////////////PRIVATE DEFINITION////////////////////////////////////////////////////
void SR74HC595::initializePins()
{
	pinMode(datapin,OUTPUT);
	pinMode(clkpin,OUTPUT);
	pinMode(latchpin,OUTPUT);

	digitalWrite(datapin,LOW);
	digitalWrite(clkpin,LOW);
	digitalWrite(latchpin,LOW);
}

void SR74HC595::clock()
{
	digitalWrite(clkpin,HIGH);
	delayMicroseconds(500);
	digitalWrite(clkpin,LOW);
	delayMicroseconds(500);
}

void SR74HC595::store()
{
	digitalWrite(latchpin,HIGH);
	delay(5);
	digitalWrite(latchpin,LOW);
	delay(5);
}

void SR74HC595::serialToParallel()
{
	for(int8_t i=7;i>=0;i--)
	{
		digitalWrite(datapin,((dataRegister>>i) & 0x01));
		clock();
	}
}

////////////////////////////////////////////////////PUBLIC DEFINITION////////////////////////////////////////////////////

void SR74HC595::sendToShiftRegister(uint8_t* data,uint8_t srNos) // send data to shift register
{
	for(uint8_t i=0;i<srNos;i++)
	{
		dataRegister = data[i];
		serialToParallel();
	}

	store();
}

void SR74HC595::sendToShiftRegister(uint8_t data) // send data to shift register
{
	dataRegister = data;
	serialToParallel();
	store();
}