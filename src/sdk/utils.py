import re
from typing import Dict, Union


def strip_string(text: str) -> str:
	return text.replace(',', '').strip()


def get_weekday(time: str) -> list:
	base_days = {'понедельник': 0, 'вторник': 1, 'сред': 2, 'четверг': 3, 'пятниц': 4, 'суббот': 5, 'воскресень': 6}
	return [next(iter([base_days[j] for j in base_days if x.find(j) != -1])) for x in time.split() if
			len([j for j in base_days if x.find(j) != -1]) != 0]


async def get_operation_regularity(text: str) -> Dict[str, Union[str, list]]:
	day_match = re.match(r'^(?P<intensive>\S.* день)', text)
	week_match = re.match(r'^(?P<intensive>\S.* неделю) (?P<at>в|во) (?P<time>\S.*)', text)
	week_other_match = re.match(r'^(каждый|каждую|каждое) (\D+)(,| |и)*$', text)
	month_patterns = [r'^(каждое) (\S.*) (числа|число)', r'^(?P<intensive>\S.* месяц) (\S.*) (числа|число)']
	month_matches = list(filter(None, [re.match(x, text) for x in month_patterns]))

	if day_match is not None:
		return {
			'type': 'every_day',
			'days': []
		}
	elif week_match is not None:
		intensive, at, time = week_match.groups()
		return {
			'type': 'every_week',
			'days': get_weekday(time)
		}
	elif len(month_matches) > 0:
		_, time, *_ = next(iter(month_matches)).groups()
		days = ['last' if strip_string(x).find('последн') != -1 else int(strip_string(x)) for x in time.split() if
				strip_string(x).isdigit() or strip_string(x).find('последн') != -1]
		return {
			'type': 'every_month',
			'days': days
		}
	elif week_other_match is not None:
		intensive, time, _ = week_other_match.groups()
		return {
			'type': 'every_week',
			'days': get_weekday(time)
		}