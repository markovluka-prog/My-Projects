"""
Обучение модели на любом русском .txt файле.

Использование:
    python train_text.py путь/к/файлу.txt

Рекомендуемые тексты (бесплатно, публичное достояние):
    Война и мир (Толстой)              — az.lib.ru/t/tolstoj_lew_nikolaewich/
    Преступление и наказание (Достоевский) — az.lib.ru/d/dostoewskij_f_m/
    Рассказы (Чехов)                   — az.lib.ru/c/chehow_a_p/
    Евгений Онегин (Пушкин)            — az.lib.ru/p/pushkin_a_s/
"""

import sys
import os
import pickle
from unittest.mock import MagicMock

sys.modules['ui'] = MagicMock()
sys.modules['console'] = MagicMock()
sys.modules['dialogs'] = MagicMock()
sys.modules['scene'] = MagicMock()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import INIT
from Cooccurrence import Cooccurrence
from Transitions import Transitions
import Dictionary

# ============================================================
# РАСШИРЕНИЕ СЛОВАРЯ ИЗ 50k_words.txt
# ============================================================

WORDS_FILE = "50k_words.txt"
if os.path.exists(WORDS_FILE):
	with open(WORDS_FILE, encoding="utf-8") as f:
		extra_words = [line.strip().lower() for line in f if line.strip()]
	existing = Dictionary.Dictionary().load()
	combined = list(set(existing) | set(extra_words))
	with open("Dictionary.pkl", "wb") as f:
		pickle.dump(combined, f)
	print(f"Словарь расширен до {len(combined)} слов (из 50k_words.txt)")

# ============================================================
# ОБУЧЕНИЕ НА .TXT ФАЙЛЕ
# ============================================================

if len(sys.argv) < 2:
	print("Укажи файл: python train_text.py файл.txt")
	sys.exit(1)

filepath = sys.argv[1]
if not os.path.exists(filepath):
	print(f"Файл не найден: {filepath}")
	sys.exit(1)

with open(filepath, encoding="utf-8", errors="ignore") as f:
	lines = f.readlines()

total = len(lines)
trained = 0
skipped = 0

print(f"Файл: {filepath} ({total} строк)")
print("Начинаю обучение...\n")

for idx, line in enumerate(lines):
	sentence = line.strip()

	# Пропускаем слишком короткие строки (менее 3 слов)
	if len(sentence.split()) < 3:
		skipped += 1
		continue

	INIT.learn(sentence)
	trained += 1

	if trained % 500 == 0:
		print(f"  [{trained} предложений обработано / {idx+1} строк из {total}]")

print(f"\nГотово!")
print(f"  Обучено предложений:  {trained}")
print(f"  Пропущено строк:      {skipped}")

words = Dictionary.Dictionary().load()
cooc = Cooccurrence().load()
trans = Transitions().load()
print(f"  Слов в словаре:       {len(words)}")
print(f"  Слов в co-occurrence: {len(cooc)}")
print(f"  Слов в transitions:   {len(trans)}")
