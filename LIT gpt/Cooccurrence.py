import pickle
import os

class Cooccurrence:
	def __init__(self, filename="cooccurrence.pkl"):
		self.filename = filename

	def load(self):
		if os.path.exists(self.filename):
			try:
				with open(self.filename, "rb") as f:
					return pickle.load(f)
			except:
				pass
		return {}

	def save(self, data):
		with open(self.filename, "wb") as f:
			pickle.dump(data, f)

	def update(self, words):
		data = self.load()
		for i, w1 in enumerate(words):
			if w1 not in data:
				data[w1] = {}
			for j, w2 in enumerate(words):
				if i != j:
					data[w1][w2] = data[w1].get(w2, 0) + 1
		self.save(data)

	def scores_for(self, query_words):
		data = self.load()
		scores = {}
		for w in query_words:
			if w in data:
				for word, count in data[w].items():
					scores[word] = scores.get(word, 0) + count
		return scores
