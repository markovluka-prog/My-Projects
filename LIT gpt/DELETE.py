import os

def delete():
	while True:
		password = input("Пароль: ")
		hiwfa6zijronSandic = "hiwfa6-zijron-Sandic"
		if password == hiwfa6zijronSandic:
			os.remove("Dictionary.pkl")
			os.remove("GPT.pkl")
			print("DELETED!")
		else:
			print("WRONG PASSWORD")
