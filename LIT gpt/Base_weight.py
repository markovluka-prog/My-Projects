import pickle
import os

class WordWeight:
	def __init__(self, text, filename="GPT.pkl"):
		self.filename = filename
		self.text = self.clean(text)
		self.weight = self.load()
		
	# очистка текста
	def clean(self, text):
		for z in [":", ",", ".", "!", "?", ";", "«", "»", ")", "(", "-"]:
			text = text.replace(z, "")
		return text.lower().split(" ")
		
	# загрузка списка рангов
	def load(self):
		if os.path.exists(self.filename):
			try:
				with open(self.filename, "rb") as f:
					return pickle.load(f)
			except:
				pass
				
		with open(self.filename, "wb") as f:
			pickle.dump([], f)
		return []
		
	# сохранение
	def save(self):
		with open(self.filename, "wb") as f:
			pickle.dump(self.weight, f)

	# поднять слово на одну позицию вверх
	def promote_one(self, word):
		# если нет — добавить в конец
		if word not in self.weight:
			self.weight.append(word)
			self.save()
			return
			
		idx = self.weight.index(word)
		
		# если слово уже на первом месте — ничего не делать
		if idx == 0:
			return
			
		# меняем местами слово и элемент выше
		self.weight[idx], self.weight[idx - 1] = self.weight[idx - 1], self.weight[idx]
		
		self.save()
		
	# обновить весь текст
	def update(self):
		for w in self.text:
			self.promote_one(w)
			
	# получить позицию слова
	def get_position(self, word):
		if word in self.weight:
			return self.weight.index(word)
		else:
			return None
		
	# основной метод
	def run(self):
		word = self.text[0]
		self.update()
		return self.get_position(word)+1
