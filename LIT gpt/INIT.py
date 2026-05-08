import Functions
from Functions import clean
import Dictionary

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

	# Шаг 2: цепочка — каждое следующее слово выбирается по предыдущему
	for _ in range(n - 1):
		weight = Functions.WeightCheck(current_word)
		chain_scores = Functions.RootModel([current_word], weight)

		next_word = max(
			(w for w in chain_scores if w not in used),
			key=chain_scores.get,
			default=None
		)

		if next_word is None:
			break

		answers.append(next_word)
		used.add(next_word)
		current_word = next_word

	return " ".join(answers)

def learn(text):
	text = " ".join(Functions.clean(text))
	x = Functions.LoadDict(text)
