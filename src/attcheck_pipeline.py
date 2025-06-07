import os
import re
from tqdm import tqdm
from transformers import pipeline
from datasets import Dataset
import torch
import datasets
import pandas as pd
import demoji
import unicodedata
import argparse

# Ensure reproducibility
seed = 1
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)

def preprocessing(_in):
    '''
    Pre-processing (normalization)
    '''
    _in = re.sub(r'https?://[w/:%#$&?()~.=+-…]+', '', _in) #画像へのリンクを削除
    _in = re.sub(r'@[w/:%#$&?()~.=+-…]+', '',_in) #'@'によるメンションを削除
    _in = re.sub(r'#(\w+)','',_in) #ハッシュタグ(半角)を削除
    _in = re.sub(r'＃(\w+)','',_in) #ハッシュタグ(全角)を削除
    _in = demoji.replace(_in,'') #🐶のような絵文字を削除

    _in = _in.replace('...','')
    _in = _in.lower()
    _in = re.sub('^"+','',_in)
    _in = re.sub('"+$','',_in)

    # スペースは意味があるので考慮して正規化
    _in = re.sub(r'\s+','<s>',_in)
    ##_in = neologdn.normalize(_in)
    _in = re.sub(r'<s>',' ',_in)
    _in = re.sub(r'< s >',' ',_in)

    return _in

def main(mymodel, file_test):
    '''
    Classify input to the category (Correct/Incorrect)

    
    test data
    format:
    1. sentence1 = raw tweet
    2. sentence2 = services
    3. label = label (0,1,2,3))
    file_test='training_data_c8c10c44_all_nrm_updated_unq_4class_nr60k_test.csv'
    file_test='testfile.csv'
    '''
    
    classifier=pipeline(task="text-classification", model=mymodel, device="cuda:0")

    # Read input
    df_test=pd.read_csv(file_test)
    sentence1 = df_test['sentence1'].tolist()
    sentence1 = [preprocessing(s) for s in tqdm(sentence1)]
    df_test['sentence1'] = sentence1

    # Pands -> Daasets
    dataset_test=Dataset.from_pandas(df_test)

    class_labels = ['Correct','Incorrect']

    if 'label' in df_test:
        print ('shop_id\titem_id\tinventory_id\tsentence1\tsentence2\tgtruth\tprediction\tscore')
    else:
        print ('shop_id\titem_id\tinventory_id\tsentence1\tsentence2\tprediction\tscore')
        
    for i,example in enumerate(dataset_test):
        sentence1 = example['sentence1']
        sentence2 = example['sentence2']
        shop_id = example['shop_id']
        item_id = example['item_id']
        inventory_id = example['inventory_id']
        
        pred_result = classifier({"text": example['sentence1'], "text_pair": example['sentence2']})
        predict_label = pred_result['label']
        score = round(pred_result['score'], 3)

        if 'label' in df_test:
            gtruth_name = df_test.at[i,'label']
            print(f'{shop_id}\t{item_id}\t{inventory_id}\t{sentence1}\t{sentence2}\t{gtruth_name}\t{predict_label}\t{score}')

        else:
            print(f'{shop_id}\t{item_id}\t{inventory_id}\t{sentence1}\t{sentence2}\t{predict_label}\t{score}')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-testfile', '--testfile', required=False)    # flag for data preparation(csv->tsv)
    parser.add_argument('-dotest', '--dotest', action='store_true')    # flag for data preparation(csv->tsv)
    parser.add_argument('-model', '--model', required=False)    # flag for data preparation(csv->tsv)            
    args = parser.parse_args()

    f_test = args.testfile
    model = args.model

    main(model,f_test)
