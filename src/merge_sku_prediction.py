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
    
  # 方法1: merge()を使用した結合
  # 共通カラムshop_id、item_id、inventory_idをキーとして
  # predテーブルのlabelカラムをskuテーブルに追加
  result = table_sku.merge(
    table_pred[['shop_id', 'item_id', 'inventory_id', 'prediction', 'score']],  # 必要なカラムのみ選択
    on=['shop_id', 'item_id', 'inventory_id'],  # 結合キー
    how='left'  # 左結合（テーブルAのすべての行を保持）
  )

  #print("結合結果:")
  #print(result.head())

  result.to_csv(out_file, index=False)
  

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
    
    
