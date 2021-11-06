import os
import re
import csv

import argparse

from t5.evaluation import metrics

from constraint_checking import TreeConstraints

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

def compute_tree_acc(inputs, outputs):

    correct = 0
    num_examples = len(inputs)
    for inp, output in zip(inputs, outputs):
        if tree_match(src=inp, tgt=output):
            correct += 1

    return (correct, num_examples, round(correct/ num_examples * 100.0, 2))

def evaluate(input_path,
             prediction_path,
             input_col_idx = 2,
             pred_col_idx = 3,
             target_col_idx = 3):

    print("Running evaluation!")

    # Read inputs from input_path
    input_data = [datum for datum in csv.reader(open(input_path, 'r'), delimiter="\t")]
    inputs = [datum[input_col_idx] for datum in input_data]

    # Read targets and predictions from prediction_path
    prediction_data = [datum for datum in csv.reader(open(prediction_path, 'r'), delimiter="\t")]
    predictions = [datum[pred_col_idx] for datum in prediction_data]
    targets = [datum[target_col_idx] for datum in prediction_data]

    # Compute Tree Accuracy for targets
    treeacc_tgt = compute_tree_acc(inputs=inputs, outputs=targets)
    print("Tree Acc. (Target): ", treeacc_tgt)

    # Compute Tree Accuracy for model predictions
    treeacc_preds = compute_tree_acc(inputs=inputs, outputs=predictions)
    print("Tree Acc. : (Model predictions)", treeacc_preds)

    # Compute BLEU scores
    # Process targets and model predictions to drop structural annotations
    mod_targets = [get_text(tree=target) for target in targets]
    mod_predictions = [get_text(tree=pred) for pred in predictions]

    scores = metrics.bleu(targets=mod_targets, predictions=mod_predictions)
    print("BLEU score : ", scores["bleu"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="General utils!")
    parser.add_argument('--datadir', type=str, default="../data/weather")
    args = parser.parse_args()

    evaluate(input_path=os.path.join(args.datadir, "train.tsv"),
             prediction_path=os.path.join(args.datadir, "train.tsv"))