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
  Reading category path file
  
  Args:
     cinfo : dictionary : 
     cpath_file : text : file name 
  '''
  
  with open(cpath_file) as f:
    #reader = csv.reader(f)
    reader = csv.reader(f, delimiter='\t')
    
    for row in reader:
      cid = str(row[0])
      cpath = row[1]
      
      # category ID -> category path のための辞書
      if cid not in cinfo:
        cinfo[cid] = cpath


def main (tgt_file,out_file,file_cpath, flag):
  '''
  '''

  # Prepare synonym dictionary
  cinfo = dict()
  get_cpath(cinfo, file_cpath)
  test_length = len(cinfo)
  print('Cpath dic length: '+str(test_length), file=sys.stderr)

  info = dict()
  line_cnt = 0

  print(f'{tgt_file}', file=sys.stderr)

  df = pd.read_csv(tgt_file, low_memory=False, on_bad_lines='warn')
  print(f'input size(rows, columns):{df.shape}',file=sys.stderr)

  if 'answer' not in df.columns:
    df['answer'] = "NO_LABEL"
    
  # タブや改行を取り除く
  sources = ['item_name','caption','pc_caption','sku_info','attribute_value']
  for tgt in sources:
    df[tgt] = df[tgt].str.replace(r'\r', '', regex=True)
    df[tgt] = df[tgt].str.replace(r'[\r]', '', regex=True)
    df[tgt] = df[tgt].str.replace(r'\n', '', regex=True)
    df[tgt] = df[tgt].str.replace(r'[\n]', '', regex=True)
    df[tgt] = df[tgt].str.replace(r'\t', 'TAB', regex=True)
    df[tgt] = df[tgt].str.replace(r'[\t]', 'TAB', regex=True)
    
  data_header = df.columns
  output = []
  output.append(['shop_id', 'item_id', 'inventory_id', 'sentence1', 'sentence2', 'label'])
  
  for i in tqdm.tqdm(range(0, len(df.index))):
    line = []
    
    mid = str(df.loc[i, 'shop_id'])
    item_id = str(df.loc[i, 'item_id'])
    genre_id = str(df.loc[i, 'genre_id'])
    inventory_id = str(df.loc[i, 'inventory_id'])

    cpath = 'NOPATH'
    if genre_id in cinfo:
      cpath = cinfo[genre_id]
    else:
      cpath = 'NO_CPATH'

    # Normalize lower_case -> NFKC -> neologd -> unmask_space
    sku_info = check_symbols(str(df.loc[i, 'sku_info']))
    item_name = check_symbols(str(df.loc[i, 'item_name']))
    attribute_name = str(df.loc[i, 'attribute_name'])
    attribute_value = check_symbols(str(df.loc[i, 'attribute_value']))

    label = 'NO_LABEL'
    if 'new_answer' in df.columns:
      label = check_label(str(df.loc[i, 'new_answer']))
    elif 'answer':
      label = check_label(str(df.loc[i, 'answer']))
    elif flag != 'nolabel':
      print('ERROR:: No label in the data', file=sys.stderr)
      sys.exit()

    if label == "Unknown":
      continue

    label = check_symbols(str(label))
    
    line.append(mid)
    line.append(item_id)
    line.append(inventory_id)
    line.append(item_name)
    line.append(f'{sku_info}〓{attribute_name}〓{attribute_value}〓{cpath}')
    line.append(label)

    #print(f'{mid}\t{item_id}\t{inventory_id}\t{item_name}\t{sku_info}〓{attribute_name}〓{attribute_value}〓{cpath}\t{label}')
    
    output.append(line)


  print(f'{out_file}', file=sys.stderr)
  #df.to_csv(out_file, sep='\t', index=False)
  with open(out_file, 'w', newline='\n') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)    
    writer.writerows(output)


def check_label(label):

  if label.lower() == 'unknown':
    label = 'Unknown'
  elif label.lower() == 'correct':
    label = 'Correct'
  elif label.lower() == 'incorrect':
    label = 'Incorrect'

  return label

def check_symbols(line):
    """
    Process a string by removing surrounding quotes, replacing double quotes with single quotes,
    and replacing '〓' characters with '、'.
    
    Args:
        line (str): The input string to process
        
    Returns:
        str: The processed string
    """
    if line.startswith('"'):
        line = line[1:]  # Remove leading quote
        if line.endswith('"'):
            line = line[:-1]  # Remove trailing quote
        line = line.replace('""', '"')  # Replace double quotes with single quotes
    
    # added 09/08/2024
    line = line.replace('〓', '、')
    line = line.replace('\r', '')
    
    return line  

    
if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', required=True)    # Target Data file
  parser.add_argument('-o', '--outfile', required=False)    # Target Data file  
  parser.add_argument('-cpath', '--cpath', required=False)    # Synonym dictionary
  parser.add_argument('-nolabel', '--nolabel', action='store_true')    # flag for highlighting
  parser.add_argument('-norm', '--normalize', action='store_true') # flag for full-normalization
  args = parser.parse_args()

  tgt_file = args.file
  out_file = args.outfile
  file_cpath = args.cpath

  flag = 'withLabel'
  if args.nolabel:
    flag = 'nolabel'
    
  main(tgt_file,out_file, file_cpath, flag) # メイン
    
    
