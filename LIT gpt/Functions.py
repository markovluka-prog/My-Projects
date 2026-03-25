import Base_weight
import Root_model
import Dictionary
#============================================================
def clean(text):
		for z in [":", ",", ".", "!", "?", ";"]:
			text = text.replace(z, "")
		return text.lower().split(" ")
#============================================================
def add_two_dicts(first_dict, second_dict):
	answer = {}
	for a in first_dict:
		p = first_dict[a] + second_dict[a]
		answer[a] = p
	return answer
#============================================================
def RootModel(text, weight):
	choising = []
	for a in text:
		choising.append({})
		for b in Dictionary.Dictionary().load():
			choising[text.index(a)][b] = Root_model.RootModel(a, b, weight).ran()
	answer = {}	
	for a in Dictionary.Dictionary().load():
		p = 0
		for b in choising:
			p = p + b[a]
		answer[a] = p
	return answer
#============================================================
def ChooseTheBiggest(list):
	for i in list:
		if i == 0:
			list[list.index(i)] = -1000000000000
	return sorted(list)[len(list)-1]
#============================================================
def WeightCheck(text):
	answer = Base_weight.WordWeight(text).run()
	return answer
#============================================================	
def LoadDict(list):
	dictionary = Dictionary.Dictionary().load()
	for i in Base_weight.WordWeight(list).clean(list):
		if not i in dictionary:
			Dictionary.Dictionary().save([i])
	return dictionary 
