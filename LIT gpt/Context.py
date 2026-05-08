from Functions import clean

_history = []
MAX_MESSAGES = 3

def add(text):
	global _history
	_history.append(text)
	if len(_history) > MAX_MESSAGES:
		_history = _history[-MAX_MESSAGES:]

def get_words():
	words = []
	for msg in _history:
		words.extend(clean(msg))
	return words
