import os, pickle

class Dictionary:
	def load(self):
		if os.path.exists("Dictionary.pkl"):
			try:
				with open("Dictionary.pkl", "rb") as f:
					return pickle.load(f)
			except:
				pass
				
		with open("Dictionary.pkl", "wb") as f:
			pickle.dump([], f)
		return []
		
	# сохранение
	def save(self, add=[]):
		answer = self.load() + add
		with open("Dictionary.pkl", "wb") as f:
			pickle.dump(answer, f)
