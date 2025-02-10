import datetime
import os
import pandas as pd
import re
import sys

from dragonmapper import transcriptions

# Load CCDICT and additions
CCDICT_PATH = os.path.join("dict", "MoEDICT", "MoEDict-05-Simp03-cards.txt")
CCDICT_ADDITIONS_PATH = os.path.join("dict", "ccdict_additions.tsv")

ccdict = pd.read_csv(CCDICT_PATH, sep="\t", names=["char", "py", "def"])
char_split = ccdict.char.str.split("[", n=1, expand=True)
ccdict = ccdict.assign(
    trad=char_split[1].str.split("]", n=1, expand=True)[0],
    simp=char_split[0],
).\
drop(columns="char")[["trad", "simp", "py", "def"]]

additions = pd.read_csv(CCDICT_ADDITIONS_PATH, sep="\t")
ccdict_comb = pd.concat([ccdict, additions], axis="index")

# Get just trad and simp columns and drop resultant duplicates
ccdict_comb = ccdict_comb[["trad", "simp"]].\
drop_duplicates(keep="first").\
rename(columns={"simp": "simpf"})

# Fix
words = pd.read_csv("curr", sep="\t", na_filter=False)

words = words.merge(
    right=ccdict_comb,
    how="left",
    on="trad",
)

words = words[["note", "trad", "simp", "simpf", "py", "zy", "def", "tag"]]

output_list = words.to_csv(sep="\t", index=False).split("\n")

# Add headers
output_list[0] = "#columns:" + output_list[0]
output_list = ["#tags column:8"] + output_list
output_list = ["#notetype column:1"] + output_list
output_list = ["#html:true"] + output_list
output_list = ["#separator:tab"] + output_list

# Save
output_text = "\n".join(output_list)

with open("fixed.tsv", "w") as output_obj:
    output_obj.write(output_text)
