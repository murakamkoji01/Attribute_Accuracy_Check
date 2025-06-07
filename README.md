# Attribute_Accuracy_Check
[CAMD] Attribute Accuracy Check : Total analysis 

## 概要
店舗入力された属性値を、CAMDで所有する言語資源と照合して存在を認識する．これにより、アノテーションをする際に予め着目する情報に当たりを付けられることから、スムーズな作業を期待できる．入力となる商品（SKU）の各入力に対して、以下の点に着目する．
* 入力列中の属性が必須か任意か
* 入力列中の属性値がCAMDの持つどの辞書（属性値、同義語）に存在するか
* 入力列中の属性値が他の情報（SKU情報、商品タイトル、商品説明）に存在するか
  * アノテーション時のハイライト
* 入力列中のブランドもしくはシリーズ名の属性値の扱い（ブランドとシリーズの間の曖昧性解消）
* 入力列中の属性値が正しいかどうかの判定

## ファイル構成（主要なスクリプト）
* requirements.txt
  * pipでインストールするライブラリを記述
 
* src/check_attribute_values.py
  * メインスクリプト
  
## 言語資源
以下の言語資源を利用する．

* 属性値辞書
  * ファイル（https://rak.app.box.com/file/1502983967919）の"Attribute Dictionary Association"タブの情報を利用
  
* 属性定義
  * ファイル（https://rak.app.box.com/file/1505740782593?s=qm9vrrjg246vrwxjmmo8xc7xesp7o6f1）
  
* 同義語辞書
  * ファイル（https://rak.app.box.com/file/1485399286888）

* ジャンル情報辞書
  * ファイル（https://rak.box.com/s/b0v5qwgrp4z0w2uonikku3lqq968engb）

* ブランド名・シリーズ名曖昧性解消用辞書
  * ファイル（https://rak.box.com/s/b0v5qwgrp4z0w2uonikku3lqq968engb）

## インストール

1. メインリポジトリ
   1. `$ git clone https://ghe.rakuten-it.com/koji-murakami/Attribute_Accuracy_Check.git`

2. 言語知識
   1. BOXディレクトリのファイルを全てコピー
   2. 全てのファイルをtsvに変換
    
3. インストールが必要なツール
   1. MeCab + IPA Dictionary （適宜インストール）

   2. mecab-ipadic-NEologd
      1. `$ git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git`
      2. `$ cd mecab-ipadic-neologd`
      3. `$ ./bin/install-mecab-ipadic-neologd -n`
      4. インストール先の確認：`$ echo ``mecab-config --dicdir``"/mecab-ipadic-neologd"`

4. pipによるライブラリのインストール
   1. 多くのライブラリはpip経由でインストール可能なので以下のコマンド：`$ pip install -r requrements.txt` 
   2. MeCabが適切にインストールされているか、以下の手順でエラーが出ないことを確認：．`$ python3 -c "import MeCab"`


## システムの使い方
1. 対象データの準備
   1. 対象データは/sample以下のもの、もしくはこのファイルの形式（https://rak.app.box.com/file/1544370493913） : ${FILE1}とする
   2. シェルスクリプトの編集
     * 各ファイル名を入力
   3. シェルスクリプトの実行
      * ./attribute_accuracy_check_op_assistant.sh

2. 言語資源との照合と店舗入力値の認識
   1. 属性値辞書（${DIC_ATTVAL}）、属性定義（${DIC_ATTID}）、同義語辞書（${DIC_SYN}）、ジャンル情報辞書(${DIC_CPATH})、ブランド名シリーズ名曖昧性解消辞書(${DIC_BRASER})の確認
   2. メインスクリプト内のneologd辞書のパスの確認

3. 処理
   * 処理(A)：通常処理
      * `python3 -syn {$FILE_SYN} -attid ${FILE_ATTID} -avalue ${FILE_ATTID} -f ${FILE2} > ${FILE3}`

   * 処理(B)：入力属性値が商品情報中の文字列とマッチする際にハイライトする(`<highlight>${TOKEN}</highlight>`となる)（注意）下記課題参照のこと
      * `python3 -highlight -syn {$FILE_SYN} -attid ${FILE_ATTID} -avalue ${FILE_ATTID} -f ${FILE2} > ${FILE4}`


## 付与される情報について
1. 付与される情報
   * 基本的に元ファイルの先頭に3カラム増える
   1. 第1カラム：店舗入力の属性が必須(MANDATORY)か任意(OPTIONAL)か
   2. 第2カラム：店舗入力の属性値がどこに存在したか
      * 正規表現ベースとトークナイズによる辞書ベースがある
      * 出力は2桁の数字、1桁目は辞書ベース、2桁目が正規表現ベース

      | ID | 言語資源 |
      |:--:|:---------|
      | 1  | タイトルに属性値を認識 |
      | 2  | captionに属性値を認識 |
      | 3  | pc_captionに属性値を認識 |
      | 4  | sku_infoに属性値を認識 |
      | 0  | 属性値が非認識 |
      
      * 複数の位置に認識されることが考えられるが、1 -> 4 -> 3 -> 2の優先度で検索している
      * "04"の場合、辞書ベースでは属性値が発見されなかったが、正規表現ではsku_infoに属性値を認識した、という意味になる
   3. 第3カラム：店舗入力の属性値がどの辞書に存在したか
      | ID | 言語資源 |
      |:--:|:---------|      
      | 1  | 同義語辞書に属性値が登録 |
      | 2  | 属性値辞書に属性値が登録 |
      | 3  | 同義語辞書、属性値辞書の両方に属性値が登録 |
      | 0  | 同義語辞書、属性値辞書のどちらにも属性値が未登録 |

## 課題・問題点
* 何故かかなり重い．MeCabを使っているので完全な文字処理よりは時間がかかるがどこかでおかしな処理をしているかも
* 辞書によって振る舞いは変わる
  * 予備実験で、IPD-dic, Unidic, NEologd辞書を比較
  * ユーザ辞書を作ってブランド等を登録するとさらに精度が上がるがこれはToDo
  * unidicの場合短単位なのでブランド名等が複数トークンになる場合が散見
  * IPA-dicの場合だとカタカナの複数トークンの列に弱いのでブランド名が埋もれる場合が散見
  * 現状はNEologd辞書を利用
 
* ハイライト
  * (1)タイトル、(2)SKU_info、(3)pc_caption、(4)captionの順で入力値を検索し、見つかった時点で次の情報には移らない（処理速度の問題）
  * (1)正規化＋Tokenization、(2)正規表現によりマッチを試みており、(1)の場合、正規化により元文字列と文字列長が変わることがあるため現状未対応
    * 正規表現で入力文字列が見つからず、正規化＋Tokenizationによってのみ入力文字列が見つかった時のみ影響（例えばSKU_info中のカラー名が半角カタカナで、入力値は全角カタカナだった場合など）
    * ある月のデータ（8月）だと、58,863行中103行のみが影響

* 正規表現処理の影響
  * サイズ（S/M/L）や小桁の数字が入力値の場合、どうしても騙されることがあるので注意すること（複雑な処理はしていない）

* その他
  * 原産国／製造国　は日本国内産の場合は現状属性値辞書、同義語辞書でカバーできている範囲のみ対応しており、地方、都道府県、都市名などにより国内産と判断可能になる場合には対応してない
