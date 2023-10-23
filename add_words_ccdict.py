import datetime
import os
import pandas as pd
import re
import sys

from dragonmapper import transcriptions

CCDICT_PATH = os.path.join("dict", "MoEDICT", "MoEDict-05-Simp03-cards.txt")
CCDICT_ADDITIONS_PATH = os.path.join("dict", "ccdict_additions.tsv")

INPUT_CHAR_TYPE = "trad" # else "simp"

# Load words to add and check for duplicates
file_path = sys.argv[1]

with open(file_path, "r") as file_obj:
    words = file_obj.read().splitlines()

words = pd.Series(words)
if words.duplicated().any():
    raise ValueError(f"Input list has duplicates:\n{words[words.duplicated(keep=False)]}")

# Load CCDICT and additions
ccdict = pd.read_csv(CCDICT_PATH, sep="\t", names=["char", "py", "def"])
char_split = ccdict.char.str.split("[", n=1, expand=True)
ccdict = ccdict.assign(
    trad=char_split[1].str.split("]", n=1, expand=True)[0],
    simp=char_split[0],
).\
drop(columns="char")[["trad", "simp", "py", "def"]]

additions = pd.read_csv(CCDICT_ADDITIONS_PATH, sep="\t")
ccdict_comb = pd.concat([ccdict, additions], axis="index")

# Resolve words not found
def add_entry(word, comb, adds):

    comb = comb.copy(deep=True)
    adds = adds.copy(deep=True)

    pinyin_match = r"\b[A-Za-z][a-z]*[1-5]\b"
    pinyin_replace_nums = lambda x: transcriptions.to_pinyin(x[0]) if transcriptions.is_pinyin(x[0]) else x[0]

    try:
        defi = input(f"{word} not found. Please enter definition, any pinyin must be space-delimited: ")
    except UnicodeDecodeError:
        print("UnicodeDecodeError")
        defi = ""
    while True:
        defi = re.sub(pinyin_match, pinyin_replace_nums, defi)
        try:
            defi_success = input(f"Definition will be created as '{defi}'. Approve? ([y]/n): ")
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            print("UnicodeDecodeError")
            defi_success = "n"
        if defi_success in ["", "y"]:
            break
        try:
            defi = input(f"Please re-enter definition for {word}, any pinyin must be space-delimited: ")
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            defi = ""

    try:
        py = input(f"Please enter space-delimited pinyin for {word}: ")
    except UnicodeDecodeError:
        print("UnicodeDecodeError")
        py = ""
    while True:
        py = re.sub(pinyin_match, pinyin_replace_nums, py)
        try:
            py_success = input(f"Pinyin will be entered as '{py}'. Approve? ([y]/n): ")
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            py_success = "n"
        if py_success in ["", "y"]:
            break
        try:
            py = input(f"Please re-enter space-delimited pinyin for {word}: ")
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            py = ""

    alt_type = "simplified" if INPUT_CHAR_TYPE == "trad" else "traditional"
    alt_error = False
    try:
        alt = input(f"Please enter {alt_type} characters for {word}: ")
    except UnicodeDecodeError:
        alt_error = True
        print("UnicodeDecodeError")
    while True:
        if not alt_error:
            if alt == "":
                alt = word
            try:
                alt_success = input(f"{alt_type.title()} characters will be entered as '{alt}'. Approve? ([y]/n): ")
            except UnicodeDecodeError:
                print("UnicodeDecodeError")
                alt_success = "n"
            if alt_success in ["", "y"]:
                break
        alt_error = False
        try:
            alt = input(f"Please re-enter {alt_type} characters for {word}: ")
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            alt_error = True

    new_entry = pd.DataFrame({
        "trad": [word if INPUT_CHAR_TYPE == "trad" else alt],
        "simp": [word if INPUT_CHAR_TYPE == "simp" else alt],
        "py": [py],
        "def": [defi],
    })

    comb = pd.concat([comb, new_entry], axis="index")
    adds = pd.concat([adds, new_entry], axis="index")

    return comb, adds

entry_added = False
for word in words.values:
    if word not in ccdict_comb[INPUT_CHAR_TYPE].values:
        ccdict_comb, additions = add_entry(word, ccdict_comb, additions)
        entry_added = True

if entry_added:
    additions.to_csv(CCDICT_ADDITIONS_PATH, sep="\t", index=False)

# Get the words we want
words = ccdict_comb.set_index(INPUT_CHAR_TYPE).loc[words, :].reset_index(drop=False)

# Resolve duplicates
dups_list = words[INPUT_CHAR_TYPE].duplicated(keep=False)

if dups_list.any():
    dups = words.loc[dups_list, :]
    dups.index.name = "orig_idx"

    keep_orig_idcs = []
    for dup in dups[INPUT_CHAR_TYPE].unique():
        sel = dups.loc[dups[INPUT_CHAR_TYPE] == dup, :].reset_index(drop=False)
        with pd.option_context('display.max_rows', None, 'display.min_rows', None, "display.unicode.east_asian_width", True):
            try:
                keep_idx = int(input(f"Duplicates found for {dup}:\n\n{sel[['trad', 'simp', 'py', 'def']]}\n\nPlease enter the number of which duplicate to keep: "))
            except:
                print("ERROR!!")
                keep_idx = 0
            while True:
                keep = sel.iloc[[keep_idx], :]
                try:
                    keep_success = input(f"This entry will be kept:\n\n{keep[['trad', 'simp', 'py', 'def']]}\n\nApprove? ([y]/n): ")
                except UnicodeDecodeError:
                    print("UnicodeDecodeError")
                    keep_success = "n"
                if keep_success in ["", "y"]:
                    break
                try:
                    keep_idx = int(input(f"Please re-enter the number of which duplicate to keep: "))
                except:
                    print("ERROR!!")
                    keep_idx = 0

        keep_orig_idcs.append(sel.loc[keep_idx, "orig_idx"])

    orig_drop = dups.index[~dups.index.isin(keep_orig_idcs)]
    words = words.drop(index=orig_drop)

output_list = words.to_csv(sep="\t", index=False).split("\n")

# Get tags
try:
    tags = input("Please enter space-delimited tags to assign to these cards: ")
except UnicodeDecodeError:
    print("UnicodeDecodeError")
    tags = ""
while True:
    try:
        tags_success = input("Tags will be:\n" + "\n".join(tags.split(" ")) + "\nApprove? ([y]/n): ")
    except UnicodeDecodeError:
        print("UnicodeDecodeError")
        tags_success = "n"
    if tags_success in ["", "y"]:
        break
    try:
        tags = input("Please re-enter space-delimited tags to assign to these cards: ")
    except UnicodeDecodeError:
        print("UnicodeDecodeError")
        tags = ""
    

# Add headers
output_list[0] = "#columns:" + output_list[0]
output_list = [f"#tags:{tags}"] + output_list
output_list = ["#notetype:中文詞彙"] + output_list
output_list = ["#separator:Tab"] + output_list

# Save
output_text = "\n".join(output_list)

with open(f"new_words_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt", "w") as output_obj:
    output_obj.write(output_text)
