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

def convert_tsv2csv (tgtfile, wfile):
  OVER_SIZE_LIMIT=200_000_000
  csv.field_size_limit(OVER_SIZE_LIMIT)
  

  with open(tgtfile) as f:
    #reader = csv.reader(f)
    reader = csv.reader(f, delimiter='\t')

    with open(wfile, 'w') as fw:
      writer = csv.writer(fw)
      writer.writerows(reader)
      #for row in reader:
        #writer.writerow(row)

    
    
def convert_csv2tsv (tgtfile):
  OVER_SIZE_LIMIT=200_000_000
  csv.field_size_limit(OVER_SIZE_LIMIT)
  
  with open(tgtfile) as f:
    reader = csv.reader(f)
    for row in reader:
      
      new = []
      for mem in row:
        mem = re.sub('\n', '', mem)
        mem = re.sub('\t', 'TAB', mem)
        mem = re.sub('〓', '、', mem)                  
        new.append(mem)
        
      line = '\t'.join(new)
      print(line)


def check_csv (tgtfile):
  '''
  Sophisticating input lines
  
  '''

  OVER_SIZE_LIMIT=200_000_000
  csv.field_size_limit(OVER_SIZE_LIMIT)
  
  with open(tgtfile) as f:
    reader = csv.reader(f)
    #reader = csv.reader(f, delimiter='\t')    
    for row in reader:

        new = []
        for mem in row:
          mem = re.sub('\n', '', mem)
          mem = re.sub('\t', 'TAB', mem)
          mem = re.sub('〓', '、', mem)          
          new.append(mem)
          
        line = '\t'.join(new)
        print(line)


def get_synonym(synonym, synonym_matome, synfile):
  '''
  Reading Synonym Dictionary

  synonym : dictionary : 
  synonym_matome : dictionary : 
  synfile : text : file name 
  '''
  with open(synfile) as f:
    for line in f:
      line = line.strip()
      row = line.split('\t')
      synonym_word = re.sub('"', '', row[0])
      attribute_id = row[1]
      dictionary_value_id = row[2]
      dictionary_value_name = re.sub('"', '', row[5].lower())

      #<--- 店舗入力表現->辞書エントリ のための辞書
      if synonym_word not in synonym_matome:
        synonym_matome[synonym_word] = {}
        #synonym[synonym_word].setdefault('att_id', attribute_id)

      if attribute_id not in synonym_matome[synonym_word]:
        synonym_matome[synonym_word][attribute_id] = dictionary_value_name

      if dictionary_value_name not in synonym_matome:
        synonym_matome[dictionary_value_name] = {}        

      # そのものも登録しておく（必要ないかもだけど一応）
      if attribute_id not in synonym_matome[dictionary_value_name]:
          synonym_matome[dictionary_value_name][attribute_id] = dictionary_value_name        

      #<--- 辞書エントリ->類義語展開 のための辞書
      if dictionary_value_name not in synonym:
        synonym[dictionary_value_name] = {}
        #synonym[synonym_word].setdefault('att_id', attribute_id)

      if attribute_id not in synonym[dictionary_value_name]:
        synonym[dictionary_value_name][attribute_id] = {}

      if synonym_word not in synonym[dictionary_value_name][attribute_id]:
        synonym[dictionary_value_name][attribute_id][synonym_word] = dictionary_value_id
        
      # そのものも登録しておく（必要ないかもだけど一応）
      if dictionary_value_name not in synonym[dictionary_value_name][attribute_id]:
        synonym[dictionary_value_name][attribute_id][dictionary_value_name] = dictionary_value_id


def get_att_val_dic(dic_val, file_valdic):
  '''
  Reading Attribute values
  format: attribute ID -> dictionary_value_name

  dic_val : dictionary : attribute value information
  file_valdic : text : file name
  '''
  with open(file_valdic) as f:
    for line in f:
      line = line.strip()
      row = line.split('\t')
      attribute_id = row[0]
      attribute_name = row[1]
      dictionary_value_id = row[5]
      dictionary_value_name = row[6].lower()

      if attribute_id not in dic_val:
        dic_val[attribute_id] = {}

      if dictionary_value_name not in dic_val[attribute_id]:
        dic_val[attribute_id][dictionary_value_name] = 1


def get_att_id(attid_dic, file_attiddic):
  '''
  Reading attribute names
  format : genre_id -> attribute_name -> 'MANDATORY|OPTIONAL' = 'MANDATORY|OPTIONAL'
           genre_id -> attribute_name -> 'id' = ID

  attid_dic : dictoinary :
  file_attiddic : text : file name
  '''
  #0  	genre_id	genre_name_path	attribute_spec_group_doc_name	attribute_spec_group_detail_doc_name	attribute_id	attribute_name	attribute_dictionary_id	rms_mandatory	rms_input_method	rms_recommend	attribute_data_type	attribute_max_length	attribute_date_format	rms_unit_usable	attribute_unit_name	attribute_unit_list	rms_multi_value_flg	rms_multi_value_limit	attribute_min_value	attribute_max_value	rms_sku_unify_flg	attribute_display_order	cr_date

  with open(file_attiddic) as f:
    for line in f:
      line = line.strip()
      row = line.split('\t')
      genre_id = str(row[1])
      attribute_id = row[5]
      attribute_name = row[6]
      rms_mandatory = row[8]

      if genre_id not in attid_dic:
        attid_dic[genre_id] = {}

      if attribute_name not in attid_dic[genre_id]:
        attid_dic[genre_id][attribute_name] = {}

      if 'id' not in attid_dic[genre_id][attribute_name]:
        attid_dic[genre_id][attribute_name]['id'] = attribute_id

      # store attribute style (mandatory/optional)
      if 'mandatory' not in attid_dic[genre_id][attribute_name]:
        if rms_mandatory == '必須':
          attid_dic[genre_id][attribute_name]['mandatory'] = 'MANDATORY'
        else:
          attid_dic[genre_id][attribute_name]['mandatory'] = 'OPTIONAL'

        #print(f'{genre_id}->{attribute_name}->mandatory = {attid_dic[genre_id][attribute_name]["mandatory"]}')
        


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
    

def my_normalize (string):
  '''
  Normalize : lower_case -> NFKC -> neologd -> unmask_space
  最大限正規化する
  - neologdnはアルファベットの大文字小文字の変換しないが日本語に強い
  - NFKCで変な(Composition)日本語を対処
  '''
  string = unicodedata.normalize('NFKC', str(string).lower())
  string = re.sub('\t', 'TAB', string)
  string = re.sub('\n', ' ', string)  
  string = re.sub('〓', '、', string)                    
  #string = string.lower()
  #print(f'lower+NFKC::{string}')
  string = re.sub(r'^"','',string)
  string = re.sub(r'"$','',string)  
  string = re.sub(r'\s+','<s>',string)
  string = re.sub(r'~','<k1>',string)
  string = re.sub(r'〜','<k2>',string)  
  #print(f'converted::{string}')  
  string = neologdn.normalize(string)
  #print(f'neologdn::{string}')
  string = re.sub(r'<s>',' ',string)
  string = re.sub(r'< s >',' ',string)
  string = re.sub(r'<k1>','~',string)
  string = re.sub(r'< k1 >','~',string)
  string = re.sub(r'<k2>','~',string)
  string = re.sub(r'< k2 >','~',string)    
  #print(f'final::{string}')
  
  return string


def get_resource_id (dic_val, synonym_matome, attribute_id, attribute_value):
  '''
  Find resource where attribute_value is existent
  
  0: attribute value not found in neither attribute dic or synonym dic
  1: attribute value found in only attribute dic
  2: attribute value found in only synonym dic
  3: attribute value found in both synonym dic and attribute dic
  '''
  flag = 0
  dictionary_value_name = attribute_value
  
  # attribute_valueが正しいのかチェック（属性値辞書とのマッチング）
  if attribute_id in dic_val and attribute_value in dic_val[attribute_id]:
    flag = 1
        
  # attribute_valueは店舗入力の値なので、それがattribute_value_nameを持つなら（入力値が何らかの類義語かどうか）標準形を取得
  if attribute_value in synonym_matome and attribute_id in synonym_matome[attribute_value]:
    flag = flag + 2
    dictionary_value_name = synonym_matome[attribute_value][attribute_id]
    #print(f'{attribute_value} -> {dictionary_value_name}')

  return flag, dictionary_value_name


def simple_refer_brand_dic(opt_f):
    """
    Simple reference to brand dictionary
    """
    print("CHECK", file=sys.stderr)
    
    reverse = {
        'ブランド名': 'シリーズ名',
        'シリーズ名': 'ブランド名'
    }
    
    hash_dict = {}
    hash2_dict = {}
    read_dic(hash_dict, hash2_dict, opt_f)

    
    for line in sys.stdin:
        line = line.strip()
        tmp = line.split('\t')
        if len(tmp) < 2:
            continue
        
        att_name = tmp[0]
        att_value = tmp[1].lower()
        
        if att_name.startswith('attribute'):
            print(f"{att_name}\t{att_value}\tsuggestion\tpast_records")
            continue
        
        if att_name != "ブランド名" and att_name != "シリーズ名":
            print(f"{line}\tnone\tnone")
            continue
        
        if att_value in hash2_dict:
            dic_info = hash2_dict[att_value]
            dic_info = dic_info.replace('Positive', 'Correct').replace('Negative', 'Incorrect')
            
            info = {}
            for entry in dic_info.split(','):
                parts = entry.split(':')
                if len(parts) >= 2:
                    att_name_entry, polarity = parts[:2]
                    key = f"{att_name_entry}:{polarity}"
                    freq = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                    info[key] = freq
            
            brand_confuse = "TRUE" if ('ブランド名:Correct' in info and 'ブランド名:Incorrect' in info) else "FALSE"
            series_confuse = "TRUE" if ('シリーズ名:Correct' in info and 'シリーズ名:Incorrect' in info) else "FALSE"
            
            out = ""
            # Both brand and series have Correct/Incorrect
            if brand_confuse == "TRUE" and series_confuse == "TRUE":
                out = "シリーズ名またはブランド名"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            elif brand_confuse == "TRUE":
                out = "ブランド名"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            elif series_confuse == "TRUE":
                out = "シリーズ名"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            
            if 'シリーズ名:Correct' in info:
                if 'ブランド名:Correct' in info:
                    out = "シリーズ名またはブランド名？"
                else:
                    out = "シリーズ名"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            
            if 'ブランド名:Correct' in info:
                out = "ブランド名"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            
            if 'シリーズ名:Incorrect' in info:
                if 'ブランド名:Incorrect' in info:
                    out = "シリーズ名でもブランド名でもない"
                else:
                    out = "シリーズ名ではない"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            
            if 'ブランド名:Incorrect' in info:
                out = "ブランド名ではない"
                print(f"{line}\t{out}\t{dic_info}")
                continue
            
            print(f"{line}\tCHECK\t{dic_info}", file=sys.stderr)
        else:
            print(f"{line}\tnone\tnone")


def read_dic(hash_dict, hash2_dict, f_ref):
  """
    Read dictionary file and populate hash_dict and hash2_dict
    format : dictinary[entry][att_name][polarity] = freq
    
  """
  try:
    with open(f_ref, 'r', encoding='utf-8') as fp:
      for line in fp:
        line = line.strip()
        if not line:
          continue
        
        parts = line.split('\t')
        if len(parts) < 2:
          continue
        
        entry, info = parts
        entry = entry.strip('"')
        hash2_dict[entry] = info
        
        for tgt in info.split(','):
          parts = tgt.split(':')
          if len(parts) < 3:
            continue

          att_name, polarity, freq = parts
          freq = int(freq) if freq.isdigit() else 1
          
          if polarity == "Positive":
            polarity = "Correct"
          elif polarity == "Negative":
            polarity = "Incorrect"

          if entry not in hash_dict:
            hash_dict[entry] = {}
            if att_name not in hash_dict[entry]:
              hash_dict[entry][att_name] = {}
              if polarity not in hash_dict[entry][att_name]:
                hash_dict[entry][att_name][polarity] = 0
                
                hash_dict[entry][att_name][polarity] += freq
                
    size = len(hash_dict)
    print(f"Dic Size : {size}", file=sys.stderr)
  except Exception as e:
    print(f"Error reading dictionary: {e}", file=sys.stderr)


def match_attribute_braser(braser_dic, braser2_dic, attribute_name, attribute_value, i, df):
  '''
  Match brand/series dictionary
  
  '''
  att_name = attribute_name
  att_value = attribute_value.lower()
  #print(f'att:{att_name}==>val:{att_value}')
  
  if att_value in braser2_dic:
    dic_info = braser2_dic[att_value]
    dic_info = dic_info.replace('Positive', 'Correct').replace('Negative', 'Incorrect')
    #print(f'dicinfo:{dic_info}')
    info = dict()
    for entry in dic_info.split(','):
      parts = entry.split(':')
      if len(parts) >= 2:
        att_name_entry, polarity = parts[:2]
        key = f"{att_name_entry}:{polarity}"
        freq = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        info[key] = freq
        #print(f'{key}-->{freq}')
        
    brand_confuse = "TRUE" if ('ブランド名:Correct' in info and 'ブランド名:Incorrect' in info) else "FALSE"
    series_confuse = "TRUE" if ('シリーズ名:Correct' in info and 'シリーズ名:Incorrect' in info) else "FALSE"

    df.loc[i, 'past_records'] = dic_info
    out = ""
    # Both brand and series have Correct/Incorrect
    if brand_confuse == 'TRUE' and series_confuse == 'TRUE':
      df.loc[i, 'suggestion'] = 'シリーズ名またはブランド名'
    elif brand_confuse == 'TRUE':
      df.loc[i, 'suggestion'] = 'ブランド名'
    elif series_confuse == 'TRUE':
      df.loc[i, 'suggestion'] = 'シリーズ名'

    if 'シリーズ名:Incorrect' in info:
      if 'ブランド名:Incorrect' in info:
        df.loc[i, 'suggestion'] = 'シリーズ名でもブランド名でもない'
      else:
        df.loc[i, 'suggestion'] = 'シリーズ名ではない'
    elif 'ブランド名:Incorrect' in info:
      df.loc[i, 'suggestion'] = 'ブランド名ではない'

    if 'シリーズ名:Correct' in info:
      if 'ブランド名:Correct' in info:
        df.loc[i, 'suggestion'] = 'シリーズ名またはブランド名？'
      else:
        df.loc[i, 'suggestion'] = 'シリーズ名'
    elif 'ブランド名:Correct' in info:
      df.loc[i, 'suggestion'] = 'ブランド名'

    #past_record = df.loc[i, 'past_records']
    #suggestion = df.loc[i, 'suggestion']    
    #print(f'FIN:: {past_record}/{suggestion}\n')
    
  else:
    df.loc[i, 'suggestion'] = 'none'
    df.loc[i, 'past_record'] = 'none'    


def get_target(tgt_file):

  rows = []
  
  # TSVファイルを開いて行ごとに処理
  with open(tgt_file, 'r', encoding='utf-8') as f:
    tsv_reader = csv.reader(f, delimiter='\t')
        
    # 最初の行をヘッダーとして読み込む
    headers = next(tsv_reader)
        
    # 残りの行をデータとして読み込む
    for row in tsv_reader:
      rows.append(row)

    # 最大の列数を特定
    max_cols = max(len(row) for row in rows)
    max_cols = max(max_cols, len(headers))

     # ヘッダーの長さが足りない場合は拡張
    if len(headers) < max_cols:
      num = len(row)
      print(f'LEN:{num}:{max_cols} / {row}', file=sys.stderr)
      headers.extend([f'column_{i+1}' for i in range(len(headers), max_cols)])
    
    # 各行のデータ長を最大列数に合わせる（足りない部分はNoneで埋める）
    padded_rows = [row + [None] * (max_cols - len(row)) for row in rows]
    
    # DataFrameを作成
    df = pd.DataFrame(padded_rows, columns=headers)

    return df
    
    
    
def main (tgt_file,out_file,file_syn,file_valdic,file_attiddic,file_braser,flag_highlight,flag_braser):
  '''
  '''

  # Prepare synonym dictionary
  synonym = dict()
  synonym_matome = dict()  
  get_synonym(synonym, synonym_matome, file_syn)
  test_length = len(synonym)
  print('Synonym dic length: '+str(test_length), file=sys.stderr)

  test_length_matome = len(synonym_matome)
  print('Synonym_matome dic length: '+str(test_length_matome), file=sys.stderr)  

  # Prepare Attribute:Value dictionary  
  dic_val = dict()
  get_att_val_dic(dic_val, file_valdic)

  # Prepare Attribute Definition dictionary  
  attid_dic = dict()
  get_att_id(attid_dic, file_attiddic)
  test_length_attid = len(attid_dic)
  print('attid_dic length: '+str(test_length_attid), file=sys.stderr)

  # Prepare Brand-Series dictionary
  braser_dic = dict()
  braser2_dic = dict()
  read_dic(braser_dic, braser2_dic, file_braser)

  
  info = dict()
  line_cnt = 0

  print(f'{tgt_file}', file=sys.stderr)

  data = []
  
  OVER_SIZE_LIMIT=200_000_000
  csv.field_size_limit(OVER_SIZE_LIMIT)  
  #with open(tgt_file) as f:
    #reader = csv.reader(f)
  #  rows = csv.reader(f, delimiter='\t')
  #  for row in rows:
  #    data.append(row)
  #df = pd.DataFrame(data)
  #mylist = "/".join (df.columns)
  #print(f'{mylist}', file=sys.stderr)

  # データを格納するリスト
  rows = []
  headers = None

  #df = get_target(tgt_file)
  

  #names = ['shop_id', 'item_id', 'inventory_id', 'sku_info', 'genre_id', 'gn1', 'ran_code', 'attribute_id', 'attribute_name', 'attribute_value', 'attribute_unit', 'item_name', 'item_url', 'caption', 'pc_caption', 'image_url', 'tmp']
  #df = pd.read_csv(tgt_file, sep='\t', low_memory=False)
  #df = pd.read_csv(tgt_file, sep='\t', low_memory=False, on_bad_lines='warn')
  df = pd.read_csv(tgt_file, low_memory=False, on_bad_lines='warn')
  
  #df = pd.read_csv(tgt_file, sep='\t', header=0, names=names, low_memory=False)
  #df = pd.read_csv(tgt_file, sep='\t', names=names, low_memory=False)  
  #df = pd.read_csv(tgt_file, low_memory=False)
  #df = pd.read_csv(tgt_file, low_memory=False)
  #df = df[0].str.split('\t', expand=True)
  
  # タブや改行を取り除く
  sources = ['item_name','caption','pc_caption','sku_info','attribute_value']
  for tgt in sources:
    df[tgt] = df[tgt].astype(str).replace(r'\r\n', '', regex=True)
    df[tgt] = df[tgt].astype(str).replace(r'\r', '', regex=True)
    df[tgt] = df[tgt].astype(str).replace(r'\n', '', regex=True)            
    df[tgt] = df[tgt].astype(str).replace(r'[\n]', '', regex=True)
    df[tgt] = df[tgt].astype(str).replace(r'\t', 'TAB', regex=True)    
    df[tgt] = df[tgt].astype(str).replace(r'[\t]', 'TAB', regex=True)
    #df[tgt] = df[tgt].str.replace(r'[\t]', 'TAB', regex=True)
    
  df.insert(0, '000', '000') #<-ほんとはいらない
  df.insert(0, '0', '0') # 辞書マッチ結果格納用 
  df.insert(0, '00', '00') # Regex/Tokenizationマッチフラグ用
  df.insert(0, 'M/O', 'mo') # Mandatory/Optional フラグ用

  
  if flag_highlight:
    df['highlight_info'] = 'none'

  if flag_braser:
    df['suggestion'] = 'none'
    df['past_records'] = 'none'
    
  data_header = df.columns
  
  for i in tqdm.tqdm(range(0, len(df.index))):    

    genre_id = str(df.loc[i, 'genre_id'])
    gn1 = str(df.loc[i, 'gn1'])
    attribute_name = df.loc[i, 'attribute_name']
    
    # Normalize lower_case -> NFKC -> neologd -> unmask_space
    caption = my_normalize(df.loc[i, 'caption'])
    pc_caption = my_normalize(df.loc[i, 'pc_caption'])
    sku_info = my_normalize(df.loc[i, 'sku_info'])
    item_name = my_normalize(df.loc[i, 'item_name'])
    attribute_value = my_normalize(df.loc[i, 'attribute_value'])

    # checking attribute_value
    attribute_value = re.sub(r'\.0+','',attribute_value)            

    # Matching Brand/Series dictionary for only 'ブランド名' or 'シリーズ名'
    if flag_braser:
      if attribute_name == 'ブランド名' or attribute_name == 'シリーズ名': 
        match_attribute_braser(braser_dic, braser2_dic, attribute_name, attribute_value, i, df)
    
    #print(f'title:{item_name}')
    #print(f'sku_info:{sku_info} / {df.loc[i,"sku_info"]}')      
    #print(f'att_name:{attribute_name}')
    #print(f'att_val:{attribute_value}')
    #print(f'caption:{caption}')
    #print(f'pc_caption:{pc_caption}')      

    line_cnt += 1

    # L1-genre
    l1_genre = "NONE"
    if gn1:
      L1_genre = gn1
    else:
      L1_genre = genre_name_path.split('>>')[0]

    # attribute_id とジャンルにおいてその属性がMandatory/Optionalかを取得
    attribute_id = "NONE"
    flag_mandatory = 'UNKNOWN'
    if attribute_id == 'NONE':
      if genre_id in attid_dic and attribute_name in attid_dic[genre_id]:
        attribute_id = attid_dic[genre_id][attribute_name]['id']
        flag_mandatory = attid_dic[genre_id][attribute_name]['mandatory']
        #print(f'======> {flag_mandatory}/{attribute_id}')
        df.loc[i, 'M/O'] = flag_mandatory
        
    # 属性値の参照可能辞書の認識
    # 0: not found in neither attribute dic/synonym dic / 1: found in only attribute dic
    # 2: found only synonym dic / 3: found in both attribute dic/synonym dic
    dictionary_value_name = attribute_value
    flag_match_dic, dictionary_value_name = get_resource_id (dic_val, synonym_matome, attribute_id, attribute_value)
    df.loc[i, '0'] = flag_match_dic
    
    # 辞書エントリのSynonymの存在を認識
    # title: 1 / caption: 2 / pc_caption: 3 / sku_info: 4 x (regex/token)

    # Regexベースで属性値を（item_name, SKU_info、caption、pc_caption）から認識
    flag_match_regex, matched_word, match_object = match_attval_regex(synonym, dictionary_value_name, attribute_id, item_name, caption, pc_caption, sku_info)
    #print(f'=====>id:{flag_match_regex} / {matched_word} / {item_name} / {attribute_id}')

    if flag_highlight:
      # マッチ文字列を最後尾カラムに付け足す場合
      sources = ['NONE','item_name','caption','pc_caption','sku_info']
      source = sources[flag_match_regex]
      #line = line + '\t' + matched_word + ":" + source
      matched_word = re.sub(r'\\','',matched_word)
      #line = line + '\t' + matched_word
      df.loc[i, 'highlight_info'] = matched_word

    # tokenizationxベース
    flag_match_token = match_attval_tokenization(synonym, dictionary_value_name, attribute_id, item_name, caption, pc_caption, sku_info)      

    #print('---->'+attribute_value+'\t'+item_name)
    df.loc[i, '00'] = str(flag_match_token)+str(flag_match_regex)

  print(f'{out_file}')
  df.to_csv(out_file, index=False)

  
def match_attval_regex(synonym, dictionary_value_name, attribute_id, item_name, caption, pc_caption, sku_info):
  '''
  Find attribute value in information sources (item_name, sku_info, caption and pc_caption)

  synonym : dictonary : synonym dic
  dicionary_value_name : text : attribute value
  attribute_id : int : attribute ID
  item_name : text : item name
  caption : text : caption
  pc_caption : text : pc_caption

  outout:
  1 : attribute value found in item_name
  2 : attribute value found in caption
  3 : attribute value found in pc caption
  4 : attribute value found in sku_info
  0 : attribute value not found in item_name/caption/pc_caption/sku_info
  '''

  cands = []
  cands.append(re.escape(dictionary_value_name))

  # making a list including merchants' input attribute value and its synonyms
  if dictionary_value_name in synonym and attribute_id in synonym[dictionary_value_name]:
    for synonym in synonym[dictionary_value_name][attribute_id]:
      #print(f'target : {synonym}')
      cands.append(re.escape(synonym))

  ##print(f'===>{cands}')
      
  # information sources are in ordering : (1)item_name (2)sku_info (3)caption (4)pc_caption
  res = 0
  for entry in cands:
    obj = re.search(entry, item_name)
    if obj:
      res = 1
      ###print(f'BINGO:{entry} ==> {item_name}')
      return res,entry,obj

  for entry in cands:
    obj = re.search(entry, sku_info)
    if obj:
      res = 4
      return res,entry,obj

  for entry in cands:    
    obj = re.search(entry, pc_caption)
    if obj:
      res = 3
      return res,entry,obj

    obj = re.search(entry, caption)
    if obj:
      res = 2
      return res,entry,obj
  
  return 0,"none","none"


def match_attval_tokenization(synonym, dictionary_value_name, attribute_id, item_name, caption, pc_caption, sku_info):
  '''
  Find attribute value in information sources (item_name, sku_info, caption and pc_caption)
  Tokenization by MeCab and word-based matching
  
  synonym : dictonary : synonym dic
  dicionary_value_name : text : attribute value
  attribute_id : int : attribute ID
  item_name : text : item name
  caption : text : caption
  pc_caption : text : pc_caption

  outout:
  1 : attribute value found in item_name
  2 : attribute value found in caption
  3 : attribute value found in pc caption
  4 : attribute value found in sku_info
  0 : attribute value not found in item_name/caption/pc_caption/sku_info
  '''

  cands = []
  cands.append(re.escape(dictionary_value_name))
  #print(f'dictionary_value_name:{dictionary_value_name}')
  
  # making a list including merchants' input attribute value and its synonyms
  if dictionary_value_name in synonym and attribute_id in synonym[dictionary_value_name]:
    for synonym in synonym[dictionary_value_name][attribute_id]:
      cands.append(re.escape(synonym))

  # Tokenizing attribute value candidates
  cands_wakati = []
  for entry in cands:
    ##cands_wakati.append(re.escape(get_wakati(neologdn.normalize(entry))))
    cands_wakati.append(re.escape(get_wakati(neologdn.normalize(unicodedata.normalize('NFKC', entry.lower())))))
    #print(f'{entry} --> {cands_wakati}')

  res = 0
  # information sources are in ordering : (1)item_name (2)sku_info (3)caption (4)pc_caption
  if check_word(item_name,cands_wakati):
    res = 1
    return res

  if check_word(sku_info,cands_wakati):
    res = 4
    return res  

  if check_word(pc_caption,cands_wakati):
    res = 3
    return res

  if check_word(caption,cands_wakati):
    res = 2
    return res  

  return res


def check_word(source, cands_wakati):
  '''
  Match tokenized candidate with tokens in sources (item_naem/SKU_info/caption/pc_caption)
  '''
  source = re.sub(r'\s+','<s>',source)
  #source_wakati = get_wakati(neologdn.normalize(source))
  source_wakati = get_wakati(neologdn.normalize(unicodedata.normalize('NFKC', source.lower())))
  source_wakati = re.sub(r'<s>',' ',source_wakati)
  source_wakati = re.sub(r'< s >',' ',source_wakati)
  #source_wakati = get_wakati(source)  

  for cand_wakati in cands_wakati:
    # cand is single word, just try to match with word in source
    #print(f'single word : {cand_wakati} :: {source_wakati}')
    if not ' ' in cand_wakati:
      for word in source_wakati.split(' '):
        if cand_wakati == word:
          return True

    # cand is based on multi-words, make patterns to match words in source
    # 多分Ngram作るよりRegexの方が速い
    else:
      #print(f'multi : try: {entry_wakati}')
      pattern1 = cand_wakati+' '
      pattern2 = ' '+cand_wakati
      pattern3 = ' '+cand_wakati+' '
      
      if re.search(pattern1, source_wakati):
        return True
      elif re.search(pattern2, source_wakati):
        return True
      elif re.search(pattern3, source_wakati):
        return True
      #else:
        #print('False')        

  return False


def get_wakati (input_line):
  '''                                                                                                                                                                                                                                  
  分かち書きする
  '''
  t = mc.Tagger('-Owakati -d /opt/homebrew/lib/mecab/dic/mecab-ipadic-neologd/')
  #t = mc.Tagger('-Owakati -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd/')  
  #t = mc.Tagger('-Owakati -d /usr/local/lib/mecab/dic/unidic/')
  #t = mc.Tagger('-Owakati -d /usr/local/lib/mecab/dic/ipadic/')  
  wakati = t.parse(input_line)
  wakati = wakati.rstrip()

  return wakati

    
def check_value(value):
  '''
  '''
  #if re.search('\(|\)', value):
  if re.search('(|)', value):    
    return 'none'
  else:
    return 'valid'
  

if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', required=True)    # Target Data file
  parser.add_argument('-o', '--outfile', required=False)    # Target Data file  
  parser.add_argument('-prep', '--preprocessing', action='store_true')    # flag for data preparation
  parser.add_argument('-csv2tsv', '--csv2tsv', action='store_true')    # flag for data preparation(csv->tsv)
  parser.add_argument('-tsv2csv', '--tsv2csv', action='store_true')    # flag for data preparation(tsv->csv)
  parser.add_argument('-syn', '--synonym', required=False)    # Synonym dictionary
  parser.add_argument('-avalue', '--attvalue', required=False)    # AttributeValue dictonary
  parser.add_argument('-attid', '--attid', required=False)    # AttributeID dictionary
  parser.add_argument('-braserdic', '--braserdic', required=False)    # Synonym dictionary  
  parser.add_argument('-high', '--highlight', action='store_true')    # flag for highlighting
  parser.add_argument('-braser', '--braser', action='store_true')    # flag for highlighting  
  parser.add_argument('-norm', '--normalize', action='store_true') # flag for full-normalization
  args = parser.parse_args()

  tgt_file = args.file
  out_file = args.outfile
  file_syn = args.synonym
  file_valdic = args.attvalue
  file_attiddic = args.attid
  file_braserdic = args.braserdic
  flag_highlight = args.highlight
  flag_braser = args.braser

  if args.preprocessing:
    check_csv (tgt_file)   # データ整形の場合
  elif args.csv2tsv:
    convert_csv2tsv (tgt_file)
  elif args.normalize:
    full_normalize (tgt_file)
  elif args.tsv2csv:
    convert_tsv2csv (tgt_file,out_file)
  else :
    main(tgt_file,out_file,file_syn,file_valdic,file_attiddic,file_braserdic,flag_highlight,flag_braser) # メイン
    
    
