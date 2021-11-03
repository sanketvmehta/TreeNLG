import os
import re
import csv
import argparse
from collections import defaultdict

from copy import deepcopy
from constraint_checking import TreeConstraints

uniq_args = ['__ARG_TEMP__',
        '__ARG_TEMP_SUMMARY__',
        '__ARG_TEMP_LOW__',
        '__ARG_TEMP_LOW_SUMMARY__',
        '__ARG_TEMP_HIGH__',
        '__ARG_TEMP_HIGH_SUMMARY__',
        '__ARG_TEMP_UNIT__',
        '__ARG_COLLOQUIAL__',
        '__ARG_CITY__',
        '__ARG_REGION__',
        '__ARG_COUNTRY__',
        '__ARG_BAD_ARG__',
        '__ARG_TIME__',
        '__ARG_START_TIME__',
        '__ARG_END_TIME__',
        '__ARG_DAY__',
        '__ARG_START_DAY__',
        '__ARG_END_DAY__',
        '__ARG_WEEKDAY__',
        '__ARG_START_WEEKDAY__',
        '__ARG_END_WEEKDAY__',
        '__ARG_MONTH__',
        '__ARG_START_MONTH__',
        '__ARG_END_MONTH__',
        '__ARG_YEAR__',
        '__ARG_START_YEAR__',
        '__ARG_END_YEAR__',
        '__ARG_WIND_SPEED__',
        '__ARG_PRECIP_CHANCE__',
        '__ARG_PRECIP_CHANCE_SUMMARY__',
        '__ARG_PRECIP_AMOUNT__',
        '__ARG_PRECIP_AMOUNT_UNIT__']

SLOT_VALUE_REGEX = r"\[{}[A-Za-z0-9_<>():'Îãáíúóô.,\'\- ]+\]"

def get_text(tree):

    tokens = [token for token in tree.split(' ') if not (token.startswith('[') or token == ']')]
    return ' '.join(tokens)

def tree_match(src, tgt):

    src_tree = TreeConstraints(src.strip(), False)
    tgt_nt = re.compile(r'(\[\S+|\])').findall(tgt.strip())

    for i, w in enumerate(tgt_nt):
        if not src_tree.next_token(w, i):
            break
    else:
        if src_tree.meets_all():
            return True
    return False

def lexicalize_response(idx, lex_input, delex_response, uniq_args):

    args_values = {}
    count_equal = 0
    count_unequal = 0
    lex_response = deepcopy(delex_response)

    for arg_value in uniq_args:
        src_values = re.findall(SLOT_VALUE_REGEX.format(arg_value), lex_input.strip())
        tgt_values = re.findall(SLOT_VALUE_REGEX.format(arg_value), delex_response.strip())

        if len(src_values) == 0 or len(tgt_values) == 0:
            # arg_value is not present so skip
            continue
        elif len(src_values) == 1 or len(tgt_values) == 1 or len(set(src_values)) == 1:
            # Check whether all arg_values are same or we have single src_value or tgt_value
            src_arg_value = src_values[0].replace(f"[{arg_value} ","").replace(" ]","")
            tgt_arg_value = tgt_values[0].replace(f"[{arg_value} ", "").replace(" ]", "")
            args_values[f"{tgt_arg_value}@1"] = src_arg_value

            # replace with arg_value
            lex_response = lex_response.replace(f" {tgt_arg_value} ", f" {src_arg_value} ")
        elif len(src_values) == len(tgt_values):
            # We have equal number of src_values and tgt_values
            count_equal += 1
            count = 0

            for src_value, tgt_value in zip(src_values, tgt_values):
                src_arg_value = src_value.replace(f"[{arg_value} ", "").replace(" ]", "")
                tgt_arg_value = tgt_value.replace(f"[{arg_value} ", "").replace(" ]", "")
                lex_response = lex_response.replace(f" {tgt_arg_value} ", f" {src_arg_value} ", 1)
                args_values[f"{tgt_arg_value}@{count}"] = src_arg_value
                count += 1

        elif len(set(src_values)) == len(tgt_values):
            # We have equal number of (distinct) src_values and tgt_values
            # count_unequal += 1
            count = 0

            unq_src_values = []
            for src_value in src_values:
                if src_value not in unq_src_values:
                    unq_src_values.append(src_value)
            for src_value, tgt_value in zip(unq_src_values, tgt_values):
                src_arg_value = src_value.replace(f"[{arg_value} ", "").replace(" ]", "")
                tgt_arg_value = tgt_value.replace(f"[{arg_value} ", "").replace(" ]", "")
                lex_response = lex_response.replace(f" {tgt_arg_value} ", f" {src_arg_value} ", 1)
                args_values[f"{tgt_arg_value}@{count}"] = src_arg_value
                count += 1
        else:
            count_unequal += 1

    return lex_response, args_values, count_equal, count_unequal

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="General utils!")
    parser.add_argument('--datadir', type=str)
    args = parser.parse_args()

    train_data = [datum for datum in csv.reader(open(os.path.join(args.datadir, "train.tsv"), 'r'), delimiter="\t")]
    val_data = [datum for datum in csv.reader(open(os.path.join(args.datadir, "val.tsv"), 'r'), delimiter="\t")]
    test_data = [datum for datum in csv.reader(open(os.path.join(args.datadir, "test.tsv"), 'r'), delimiter="\t")]

    count = 0
    for datum in train_data:
        if tree_match(src=datum[2], tgt=datum[3]):
            count += 1
    print("[Train] Tree Accuracy: ", count, len(train_data), (count/ len(train_data))*100.0)

    count = 0
    for datum in val_data:
        if tree_match(src=datum[2], tgt=datum[3]):
            count += 1
    print("[Val] Tree Accuracy: ", count, len(val_data), (count / len(val_data)) * 100.0)

    count = 0
    for datum in test_data:
        if tree_match(src=datum[2], tgt=datum[3]):
            count += 1
    print("[Test] Tree Accuracy: ", count, len(test_data), (count / len(test_data)) * 100.0)

    count = 0
    for idx, datum in enumerate(test_data):

        lex_response, args_values, count_equal, count_unequal = lexicalize_response(idx=idx,
                                                                      lex_input=datum[2],
                                                                      delex_response=datum[3],
                                                                      uniq_args=uniq_args)
        if count_unequal > 0:
        # if 'ARG' in lex_response:
        # if '<number>' in get_text(lex_response):
            count += 1
            print("[Idx]: ", idx)
            print("[Input]: ", datum[2])
            print("-"*10)
            print("[Output]: ", lex_response)
            print("-" * 10)
            print("[Output]: ", get_text(lex_response))
            print("-" * 10)
            print("[Org Output]: ", datum[3])
            print("\n" + "*"*10 + "\n")

    print("Count: ", count)