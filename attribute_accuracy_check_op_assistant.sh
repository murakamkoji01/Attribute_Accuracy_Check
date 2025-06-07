
DIC_SYN='dics/Synonym_dictionary0328.txt'
DIC_ATTVAL='dics/AttributeValues_20240416_081343.txt'
DIC_ATTID='dics/AttributeDefinition202404.tsv'
DIC_BRASER='dics/BrandSeries_dic2024apr2dec_v1.tsv'
DIC_CPATH='dics/Genre_list.tsv'

TGT_FILE='250516_attribute_accuracy_check_raw.csv'
OUT_FILE='250516_attribute_accuracy_check_highlight_braser.csv'

MODEL='attribute_accuracy_check_model0000'
MODEL_INPUT='250516_attribute_accuracy_check_highlight_braser_selected_tdata.csv'
PREDICTION_RESULT='250516_attribute_accuracy_check_highlight_braser_selected_tdata_predicted.csv'
INPUT_HANKO='250516_attribute_accuracy_check_highlight_braser_selected_fin.csv'
OUT_FILE_SELECTED='250516_attribute_accuracy_check_highlight_braser_selected_fin_selected.csv'

# check sku info (Add a few kinds of information, highlight, braser)
python3 src/check_att_csv_v3.py -syn ${DIC_SYN} -attid ${DIC_ATTID} -avalue ${DIC_ATTVALUE} -braser -braserdic ${DIC_BRASER} -high -f ${TGT_FILE} -o ${OUT_FILE} > tmp

# convert sku info to model input format
python3 src/mk_data.py -cpath ${DIC_CPATH} -f ${OUT_FILE} -o ${MODEL_INPUT} > tmp

# get prediction results
python3 src/attcheck_pipeline.py -model ${MODEL} -testfile ${MODEL_INPUT} > ${PREDICTION_RESULT}

# merge sku data and prediction results
python3 src/merge_sku_prediction.py -sku ${OUT_FILE_SELECTED} -pred ${PREDICTION_RESULT} -o ${INPUT_HANKO}

# choose lines for model evaluation
grep -E "(MANDATORY|OPTIONAL),(10|11|14|21|24|31|34|40|41|44)," ${INPUT_HAKO} > ${OUT_FILE_SELECTED}

