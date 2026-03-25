import console
class RootModel:
	def __init__(self, word_one, word_two, weight=1):
		self.weight = weight
		self.word_one = list(word_one.lower())
		self.word_two = list(word_two.lower())
	def find_the_same_letters(self, word_one, word_two):
		word_one = list(word_one)
		word_two = list(word_two)
		if len(word_one) > len(word_two):
			the_smallest = word_two
			the_biggest = word_one
		else:
			the_smallest = word_one
			the_biggest = word_two
		
		the_same_letters_zero = []
		the_same_letters_one = []
		used_big = set()
		for idx_small, i in enumerate(the_smallest):
			for idx_big, b in enumerate(the_biggest):
				if i == b and idx_big not in used_big:
					used_big.add(idx_big)
					the_same_letters_zero.append(idx_big)
					the_same_letters_one.append(idx_small)
					break
		return [the_same_letters_zero, the_same_letters_one]
	def ran(self):
		#ЗАПУСК
		the_same = self.find_the_same_letters(self.word_one, self.word_two)
		procent = self.line_times(the_same[0], the_same[1])
		return procent
	def use_coordinates(self, point_one, point_one_to, point_two, point_two_to):
		answer = self.lines_intersect_coords(point_one, 0, point_one_to, 1, point_two, 0, point_two_to, 1)
		return answer
	def lines_intersect_coords(self, x1, y1, x2, y2, x3, y3, x4, y4):
		D_det = (x2 - x1)*(y4 - y3) - (y2 - y1)*(x4 - x3)
		if x3 == x1 or x2 == x4:
			return False
		else:
			return D_det != 0
	def line_times(self, same_one, same_two):
		procents = 0
		for a in range(0, len(same_one)):
			kill = self.use_coordinates(same_one[a], same_two[a], same_one[a], same_two[a])
			if kill:
				procents += self.weight*2
			else:
				procents += self.weight
		return procents
if __name__ == '__main__':
	first_word = console.input_alert("Первое слово", "↓")
	second_word = console.input_alert("Второе слово", "↓")
	console.alert(f"Соотношение «{first_word}» и «{second_word}»", str(RootModel(first_word, second_word).ran())+"%")

