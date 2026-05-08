import pickle
import os

class Transitions:
	def __init__(self, filename="transitions.pkl"):
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
		for i in range(len(words) - 1):
			w, nw = words[i], words[i + 1]
			if w not in data:
				data[w] = []
			if nw not in data[w]:
				data[w].append(nw)
		self.save(data)
