import Functions
from Functions import clean
import Dictionary
from Transitions import Transitions

def answer(text):
	question = clean(text)
	n = max(2, len(question))

	# Шаг 1: оцениваем весь словарь по вопросу → выбираем первое слово
	weights = {}
	for i in question:
		weights[i] = Functions.WeightCheck(i)

	root_model = {w: 0 for w in Dictionary.Dictionary().load()}
	for i in question:
		root_model = Functions.add_two_dicts(root_model, Functions.RootModel(question, weights[i]))

	first_word = max(root_model, key=root_model.get)
	answers = [first_word]
	used = {first_word}
	current_word = first_word

	# Шаг 2: цепочка — следующее слово только из разрешённых переходов
	transitions = Transitions().load()
	for _ in range(n - 1):
		weight = Functions.WeightCheck(current_word)
		chain_scores = Functions.RootModel([current_word], weight)

		allowed = transitions.get(current_word)
		if allowed:
			candidates = [w for w in chain_scores if w not in used and w in allowed]
		else:
			candidates = [w for w in chain_scores if w not in used]

		if not candidates:
			break

		next_word = max(candidates, key=chain_scores.get)
		answers.append(next_word)
		used.add(next_word)
		current_word = next_word

	return " ".join(answers)

def learn(text):
	words = Functions.clean(text)
	Functions.LoadDict(" ".join(words))
	Transitions().update(words)
