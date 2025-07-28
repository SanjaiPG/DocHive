
#include "stm32f4xx.h"

void ADC_init(void);
void ADC_conversion(void);
int ADC_read(void);
int ADCdata;
int main(void)	{
	ADC_init();
	
	while(1)
	{
		ADC_conversion();
		ADCdata = ADC_read();
	}	
}

void ADC_init(void)
{
	RCC->AHB1ENR |= (1<<0); // Enable clock source for PORT A
	GPIOA->MODER |= (3<<0); // Pa0 pin as an Analog
	RCC->APB2ENR |= (1<<8);  // Enable clock source for ADC1
	ADC1->CR1 |= (1<<24);  //  set 10 bit ADC
	ADC1->CR2 &= ~(1<<0);  //  ADC disable
	ADC1->SQR3 |= 0; // Enable ADC 0th Channel
	ADC1->CR2 |=  (1<<0);  // ADC ON
	
}

void ADC_conversion(void)
{
	ADC1->CR2 |= (1<<30); // Start  ADC conversion
	
}

int ADC_read(void)
{
	while(!(ADC1->SR & (1<<1))) {} // wait for conversion to be complete
		return (ADC1-> DR);
		
}
