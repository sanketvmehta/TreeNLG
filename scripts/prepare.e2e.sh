#!/bin/bash
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

cd $(dirname $0)/..

src=mr
tgt=ar
prep=data-prep/e2e
orig=data/E2E_compositional

mkdir -p $prep

echo -e "show data sample...\n"
awk -F '\t' 'NR==1 {print $1}' $orig/train.tsv ; echo ""
awk -F '\t' 'NR==1 {print $2}' $orig/train.tsv ; echo ""
awk -F '\t' 'NR==1 {print $3}' $orig/train.tsv ; echo ""
awk -F '\t' 'NR==1 {print $3}' $orig/train.tsv | \
  sed 's/\[\w\+//g' | sed 's/\]//g' | awk '{$1=$1;print}' ; echo ""

echo "creating train..."
awk -F '\t' '{print $2}' $orig/train.tsv > $prep/tmp.train.$src
awk -F '\t' '{print $3}' $orig/train.tsv > $prep/tmp.train.$tgt
echo "creating valid..."
awk -F '\t' '{print $2}' $orig/val.tsv   > $prep/valid.$src-$tgt.$src
awk -F '\t' '{print $3}' $orig/val.tsv   > $prep/valid.$src-$tgt.$tgt
echo "creating test..."
awk -F '\t' '{print $2}' $orig/test.tsv  > $prep/test.$src-$tgt.$src
awk -F '\t' '{print $3}' $orig/test.tsv  > $prep/test.$src-$tgt.$tgt
echo "creating test.disc..."
awk -F '\t' '{print $2}' $orig/disc_test.tsv  > $prep/test.disc.$src-$tgt.$src
awk -F '\t' '{print $3}' $orig/disc_test.tsv  > $prep/test.disc.$src-$tgt.$tgt

echo -e "\nproprecessing..."
fairseq-preprocess \
  --source-lang $src --target-lang $tgt \
  --trainpref $prep/tmp.train \
  --destdir $prep \
  --dataset-impl raw \

rm $prep/tmp.*
