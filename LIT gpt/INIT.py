import Functions, console, dialogs
from Functions import clean
import Dictionary

def answer(text):
	question = clean(text)
	
	weights = {}
	for i in question:
		weights[i] = Functions.WeightCheck(i)
		
	root_model = {}
	for i in Dictionary.Dictionary().load():
		root_model[i] = 0
	for i in question:
		second_dict = {}
		second_dict = Functions.RootModel(question, weights[i])
		root_model = Functions.add_two_dicts(root_model, second_dict)
	root_model_items = list(root_model.values())
	root_model_words = list(root_model.keys())
	
	answers = []
	for i in root_model_items:
		answer = root_model_words[root_model_items.index(Functions.ChooseTheBiggest(root_model_items))]
		answers.append(answer)
		root_model_items[root_model_items.index(Functions.ChooseTheBiggest(root_model_items))] = -1000000000000000000000
	n = max(2, len(question))
	return " ".join(answers[:n])

def learn(text):
	text = " ".join(Functions.clean(text))
	x = Functions.LoadDict(text)
