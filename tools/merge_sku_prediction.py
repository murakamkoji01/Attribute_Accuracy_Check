import os
import re
import sys
import argparse
import pandas as pd
import csv
import MeCab as mc
import tqdm
import neologdn
import unicodedata

def get_cpath(cinfo, cpath_file):
  '''
  Reading catehory path file

  cinfo : dictionary : 
  cpath_file : text : file name 
  '''

  with open(cpath_file) as f:
    #reader = csv.reader(f)
    reader = csv.reader(f, delimiter='\t')

    for row in reader:
      cid = str(row[0])
      cpath = row[1]
      
      #<--- categor ID -> category path のための辞書
      if cid not in cinfo:
        cinfo[cid] = cpath


def full_normalize (tgtfile):

  line_cnt = 0
  with open(tgt_file) as f:
    lines = f.readlines()
    #for line in f:
    for line in tqdm.tqdm(lines):
      line = line.strip()

      row = line.split('\t')
      length = len(row)
      out = []
      out.append(row.pop(0)) # "Mandatory|Optional"
      out.append(row.pop(0)) # flag1: title/sku/caption/pccpation
      out.append(row.pop(0)) # matched dictionary information
      
      for idx in range(len(row)):
        # sku_info, attribute_value, item_name, caption, pc_caption
        if idx == 4 or idx == 9 or idx == 10 or idx == 12 or idx == 13:

        # sku_info, attribute_value, item_name, caption, pc_caption (if "attribute_format" is between atribute_value and item_name)
        #if idx == 4 or idx == 9 or idx == 11 or idx == 13 or idx == 14:        
          out.append(my_normalize(row[idx]))
        else:
          out.append(row[idx])

      final = "\t".join(out)
      print(f'{final}')
    

def main (tgt_file,pred_file,out_file):
  '''
  Merge prediction result to sku original lines

  Args:
     tgt_file : file (sku original)
     pred_file : file of the prediction result
     out_file : file for output

  Returns:
  '''


  # CSVファイルを読み込み
  table_sku = pd.read_csv(tgt_file, low_memory=False, on_bad_lines='warn')
  table_pred = pd.read_csv(pred_file, sep='\t', low_memory=False, on_bad_lines='warn')

  key_columns = ['shop_id', 'item_id', 'inventory_id']
  target_column = ['prediction']
  # Predテーブルから必要なカラムのみを選択
  #columns_to_merge = key_columns + [target_column]
  #table_pred_subset = table_pred[columns_to_merge].copy()

  # 重複を除去（同じキーで異なる値がある場合は最初の値を使用）
  #table_pred_subset = table_pred_subset.drop_duplicates(subset=key_columns, keep='first')
    
  # 方法1: merge()を使用した結合
  # 共通カラムshop_id、item_id、inventory_idをキーとして
  # predテーブルのlabelカラムをskuテーブルに追加
  result = table_sku.merge(
    table_pred[['shop_id', 'item_id', 'inventory_id', 'prediction', 'score']],  # 必要なカラムのみ選択
    on=['shop_id', 'item_id', 'inventory_id'],  # 結合キー
    how='left'  # 左結合（テーブルAのすべての行を保持）
  )

  # 結合を実行
  #result = table_sku.merge(
  #  table_pred_subset,
  #  on=key_columns,
  #  how='left',
  #  suffixes=('', '_from_pred')
  #)

  print("結合結果:")
  print(result.head())

  result.to_csv(out_file, index=False)
  
  #with open(out_file, 'w', newline='\n') as f:
  #  #writer = csv.writer(f, delimiter='\t', quoting=3)
  #  writer = csv.writer(f, delimiter='\t',quoting=csv.QUOTE_MINIMAL)
  #  #writer = csv.writer(f, delimiter='\t',quoting=csv.QUOTE_MINIMAL)    
  #  writer.writerows(output)


def check_label(label):

  if label.lower() == 'unknown':
    label = 'Unknown'
  elif label.lower() == 'correct':
    label = 'Correct'
  elif label.lower() == 'incorrect':
    label = 'Incorrect'

  return label


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-sku', '--skufile', required=True)    # Target Data file
  parser.add_argument('-pred', '--prediction', required=True)    # Synonym dictionary
  parser.add_argument('-o', '--outfile', required=True)    # Target Data file  
  parser.add_argument('-nolabel', '--nolabel', action='store_true')    # flag for highlighting
  parser.add_argument('-norm', '--normalize', action='store_true') # flag for full-normalization
  args = parser.parse_args()

  tgt_file = args.skufile
  out_file = args.outfile
  pred_file = args.prediction
  #file_cpath = args.cpath

  main(tgt_file,pred_file,out_file) # メイン
    
    
