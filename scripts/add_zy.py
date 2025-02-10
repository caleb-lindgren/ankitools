import pandas as pd
from dragonmapper import transcriptions

words = pd.read_csv("curr", sep="\t")

words = words.assign(simp=np.where(words.simp == "", words.simp, words.simp + "<br>"))
words = words.assign(zy=["　".join([transcriptions.to_zhuyin(syl) for syl in py.split(" ")]) for py in words.py])

words = words[["note", "trad", "simp", "py", "zy", "def", "tag"]]

words.to_csv("fixed.tsv", sep="\t", index=False)
