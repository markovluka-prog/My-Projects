import Functions
from Functions import clean
import Dictionary
from Transitions import Transitions
from Cooccurrence import Cooccurrence
import Context

def answer(text):
	question = clean(text)
	n = max(6, len(question) * 2)

	# Основной scoring — co-occurrence по словам вопроса
	scores = Cooccurrence().scores_for(question)

	# Буст от контекста (последние 3 сообщения, вес 0.3)
	context_words = Context.get_words()
	if context_words:
		context_scores = Cooccurrence().scores_for(context_words)
		for w, s in context_scores.items():
			scores[w] = scores.get(w, 0) + s * 0.3

	# Fallback на буквенное сравнение если co-occurrence пустой
	if not scores:
		weights = {}
		for i in question:
			weights[i] = Functions.WeightCheck(i)
		root_model = {w: 0 for w in Dictionary.Dictionary().load()}
		for i in question:
			root_model = Functions.add_two_dicts(root_model, Functions.RootModel(question, weights[i]))
		scores = root_model

	# Убираем из кандидатов слова самого вопроса
	for w in question:
		scores.pop(w, None)

	if not scores:
		return " ".join(question)

	# Первое слово — лучший матч
	first_word = max(scores, key=scores.get)
	answers = [first_word]
	used = set(question) | {first_word}
	current_word = first_word

	# Цепочка: следующее слово только из разрешённых переходов
	transitions = Transitions().load()
	cooc = Cooccurrence()
	for _ in range(n - 1):
		allowed = transitions.get(current_word)
		chain_scores = cooc.scores_for([current_word])

		if allowed:
			candidates = [w for w in allowed if w not in used]
		else:
			candidates = [w for w in chain_scores if w not in used]

		if not candidates:
			break

		next_word = max(candidates, key=lambda w: chain_scores.get(w, 0))
		answers.append(next_word)
		used.add(next_word)
		current_word = next_word

	# Запомнить вопрос в контексте
	Context.add(text)

	return " ".join(answers)

def learn(text):
	words = Functions.clean(text)
	Functions.LoadDict(" ".join(words))
	Transitions().update(words)
	Cooccurrence().update(words)
