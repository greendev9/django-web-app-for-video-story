from django import template
import decimal

register = template.Library()


@register.filter
def add_decimal(num_1, num_2):
	return decimal.Decimal(num_1) + decimal.Decimal(num_2)

@register.filter
def times(num):
	print(num)
	return range(num)

@register.filter
def subtract(num, num2):
	print(num, num2)
	return num2 - num

@register.filter
def get_position(positions, index):
	return positions[index]