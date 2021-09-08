.. TEZip documentation master file, created by
   sphinx-quickstart on Thu Aug 12 16:14:39 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.



Welcome to TEZip's documentation!
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

はじめに
==============
本ドキュメントは、「大規模研究施設の整備・利活用のためのデータ圧縮ツール開発」（以下本件）において開発したシステムの環境構築手順及び操作手順について説明するものです。

システム概要
============
本システムは、以下3つの機構からなります。

* 学習機構
* 圧縮機構
* 解凍機構

学習機構
'''''''''
`PredNet <https://coxlab.github.io/prednet/>`_ を使用して時間経過によって物体が動く変化の学習を行います。
PredNetの学習方法に従い学習データをhkl形式に変換してから学習を行います。
学習したモデルをファイルに出力し、圧縮機構・解凍機構で使用します。
学習データのダウンロード・hklへの変換は別途プログラムを使用して用意します。
詳しくは5.2で説明します。

圧縮機構
''''''''''''''''''''''
学習機構で出力したモデルを使用して、時系列画像群を推論・差分を圧縮します。
元画像と推論結果の差分を求め、error-bounded quantization、Density-based Spatial Encoding、Partitioned Entropy Encodingの処理を施します。これらの処理は最終的に圧縮する時に圧縮率を高める効果があります。
圧縮にはzstdライブラリを使用してバイナリファイル(.dat)に出力します。
また、差分だけでなくキーフレーム画像もzstdを使用してバイナリファイル(.dat)に出力します。

解凍機構
''''''''''''''''''''''
学習機構で出力したモデルと圧縮機構で出力したバイナリファイル(.dat)を使用して、圧縮機構に入力した画像群を復元します。
キーフレームを入力として推論を行い、圧縮機構の推論結果を再現します。
Density-based Spatial Decoding、Partitioned Entropy Decodingの処理を圧縮機構の逆順に施すことで、元の差分を復元します。error-bounded quantizationの処理は非可逆圧縮になるため、解凍機構には含まれません。
推論結果と差分を足し合わせることで、元画像を復元し、出力します。

動作環境
========
今回はマシンの構築にAWSのEC2を使用しました。

EC2情報
'''''''''''
* AMI
   CentOS 7.9.2009 x86_64 - ami-00f8e2c955f7ffa9b
* インスタンスタイプ
   p2.xlarge
   
マシン情報概要
''''''''''''''

* 動作OS
   CentOS7

* 動作CPU
   Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz×4 
  
* 動作GPU
   NVIDIA K80(12GB)
   
* 動作メモリ
   64GB

環境構築手順
============

以下の手順で環境構築を行います

* NVIDIAドライバのインストール
* CUDAのインストール
* cuDNNのインストール
* 仮想環境の作成

NVIDIAドライバのインストール
'''''''''''''''''''''''''''''
NVIDIAのGPUを使用できるようにドライバを以下の手順に従ってインストールします。

標準ドライバの無効化
..........................
NVIDIAドライバのインストールの邪魔をしないように標準ドライバを切る必要があります。以下のコマンドを実行してください。

.. code-block:: sh

  lsmod | grep nouveau
  
その後、vimなどのテキストエディタを使用して以下のディレクトリにファイルを作成してください。

.. code-block:: sh

   /etc/modprobe.d/blacklist-nouveau.conf

作成したファイルには以下を記述して保存します。

.. code-block:: sh

   blacklist nouveau
   options nouveau modeset=0
   
 その後再起動をして、以下のコマンドを入力します。何も表示されなければ、無効化に成功しています。

.. code-block:: sh

   lsmod | grep nouveau
   
インストールの実行
..........................
NVIDIAドライバのインストールに必要なパッケージをインストールします。以下のコマンドを実行してください。

.. code-block:: sh

   yum -y install kernel-devel kernel-devel-$(uname -r) kernel-header-$(uname -r) gcc gcc-c++ make
  
次に自分のGPUデバイスの名前を確認します。以下のコマンドを実行して確認できます。

.. code-block:: sh

   lspci | grep -i nvidia

以下の図のような`NVDIAドライバダウンロードのページ <https://www.nvidia.co.jp/Download/index.aspx?lang=jp/>`_ から自分のGPUデバイスを選択してインストールに進みます。「CUDA Toolkit」については「10.0」を選択してください。

.. image:: ./img/img1.png

次にダウンロードしたファイルを実行してNVIDIAドライバのインストーラを実行します。以下のコマンドは一例になります。ダウンロードしたファイル名に置き換えて実行してください。

.. code-block:: sh

   sh NVIDIA-Linux-x86_64-410.129-diagnostic.run
   
インストーラの選択に対して全て「YES」を選択してインストールを実行します。
以下の図のような画面が表示されていればインストール完了となります。

.. image:: ./img/img2.png

以下のコマンドを実行して、以下の図のような画面が表示されれば、正しくインストールされています。

.. code-block:: sh

   nvidia-smi

.. image:: ./img/img3.png

CUDAのインストール
'''''''''''''''''''''''''''''

GPUをプログラムで使用するためにCUDAをインストールします。
今回は、CUDA **10.0** のバージョンを使用します。
以下の図のような`ダウンロードページ <https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Linux&target_arch=x86_64&target_distro=CentOS&target_version=7&target_type=rpmlocal>`_ を開き「Linux」「x86_64」「CentOS」「7」「rpm(local) または rpm(network)」を選択してインストーラのダウンロードを行ってください。

.. image:: ./img/img4.png

次にダウンロードしたファイルを実行してCUDA10.0のインストーラを実行します。以下のコマンドを実行してください。

.. code-block:: sh

   sudo yum -y install epel-release
   sudo rpm -i cuda-repo-rhel7-10-0-local-10.0.130-410.48-1.0-1.x86_64.rpm
   yum clean all
   yum install cuda

その後、以下のコマンドを実行してパスを通します。結果を反映するために、実行した後は再起動をしてください。

.. code-block:: sh

   echo ' PATH=”/usr/local/cuda-10.0/bin${PATH:+:${PATH}}"' >> ~/.bashrc
   echo 'export LD_LIBRARY_PATH=”/usr/local/cuda-10.0/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"' >> ~/.bashrc

再起動した後は以下のコマンドを実行してください。以下の図のような画面が表示されれば、正しくインストールされています。

.. code-block:: sh

   nvcc -V

.. image:: ./img/img5.png

cuDNNのインストール
'''''''''''''''''''''''''''''

CUDAに引き続きGPUをプログラムで使用するためにcuDNNをダウンロードします。
なお、こちらについてはあらかじめNVIDIAアカウントを作成する必要があります。下記手順の途中でログインを要求されることがあるので未作成の場合は、そのタイミング作成してください。
今回はcuDNN **7.6.5** のバージョンを使用します。
以下の図のような`ダウンロードページ <https://developer.nvidia.com/rdp/cudnn-archive>`_ を開き、「Download cuDNN v7.6.5 (November 5th, 2019), for CUDA 10.0」「cuDNN Library for Linux」を選択してダウンロードしてください。

.. image:: ./img/img6.png

ダウンロードが完了したら、解凍してファイルを適当な場所に配置します。以下のコマンドを実行してください。

.. code-block:: sh

   tar zxf cudnn-10.0-linux-x64-v7.6.5.32.tgz
   sudo cp -a cuda/include/* /usr/local/cuda/include/
   sudo cp -a cuda/lib64/* /usr/local/cuda/lib64/
   sudo ldconfig

仮想環境の作成
'''''''''''''''''''''''''''''

Python環境を切り分け、管理しやすくするため、仮想環境を使用します。
今回は「pyenv」を使用して、その中に「anaconda」をインストールして使用します。

pyenvのインストール
..........................

pyenvをインストールして「pyenv」コマンドを有効にします。以下のコマンドを実行した後、再起動をしてください。

.. code-block:: sh

   git clone https://github.com/yyuu/pyenv.git ~/.pyenv
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
   echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc

pyenvを使用する場合は、pipを使用してライブラリをインストールします。その際にzipファイルの解凍を行う場合があるため、zipコマンドがない場合はインストールしておく必要があります。以下のコマンドを実行してインストールできます。

.. code-block:: sh

   yum -y install zip unzip bzip2
   
anacondaのインストール
..........................

pyenvの中にanacondaをインストールして仮想環境を作成します。「pyenv install -l」でインストールできる環境の一覧を表示できます。今回は「anaconda3-4.3.1」を使用します。仮想環境作成のコマンドは以下になります。

.. code-block:: sh

   eval "$(pyenv init -)"
   pyenv install anaconda3-4.3.1

その後、以下のコマンドで仮想環境に入ります。

.. code-block:: sh

   pyenv rehash
   pyenv global anaconda3-4.3.1

以下のバージョンを確認するコマンドを実行して、以下の表示が確認できれば仮想環境に入れています。

.. code-block:: sh

   python -V
   Python 3.6.0 :: Anaconda 4.3.1 (64-bit)

必要なライブラリのインストール
..........................

pyenv + anacondaで環境に入った後は、pipを使用して必要なライブラリをインストールします。まずは以下のコマンドでpipのアップデートをします。

.. code-block:: sh

   pip install --upgrade pip
   
次に以下のコマンドで必要なライブラリをインストールします。

.. code-block:: sh

   pip install tensorflow-gpu==1.15
   pip install keras==2.2.4
   pip install hickle==4.0.1
   pip install numba==0.52.0
   pip install zstd==1.4.5.1
   pip install Pillow==8.0.1
   pip install scipy==1.2.0
   pip install h5py==2.10.0
   pip install cupy-cuda100==8.4.0
   pip install numpy==1.19.5

付録のKittiデータを使用した学習データ作成のサンプルプログラムを動かす場合には、以下のライブラリを追加でインストールしてください。

.. code-block:: sh

   pip install requests==2.25.1
   pip install bs4
   pip install imageio==2.9.0

以下のコマンドを実行して以下の図のようにdevice_typeに”GPU”がある場合は、pythonプログラムからGPUを認識することに成功しています。

.. code-block:: sh

   python
   # 以下pythonの対話モード
   >>> from tensorflow.python.client import device_lib
   >>> device_lib.list_local_devices()

.. image:: ./img/img7.png

環境構築で発生する不具合に対するヘルプ
'''''''''''''''''''''''''''''

環境によっては、これまでの記述内容だけではうまくいかないケースがあります。
ここではテスト用環境構築中に起きた不具合と、その対応策について記述します。同様の不具合が発生した場合は参考にしてください。

pip installでエラーが発生してインストールできない
..........................

実行時の権限の状態によっては、「pip install」をしたときにエラーが起こる場合があります。pipが既存のライブラリとの依存関係を調べアップデートしようとします。その際に、前のバージョンをアンインストールする権限が無いため、起こるエラーです。
その場合には「--ignore-installed」をオプションに付けることで、インストール済みのライブラリとの依存関係を無視してインストールすることができます。
コマンド例としては以下の通りです

.. code-block:: sh

   pip install tensorflow-gpu==1.15 --ignore-installed

ファイル書き込み権限が無くファイルを出力できない
..........................

実行時の権限の状態によっては、仮想環境のpythonからファイルの出力が行えない場合があります。その際、「sudo python」で管理者権限で実行すると、仮想環境以外にpythonがインストールされている場合、そちらが呼び出されます。
「sudo python」から仮想環境のpythonを呼び出すためには以下の手順が必要になります。

1. vimなどで「/etc/sudoers」を開く
2. Default secure_pathに「pyenv保存場所/.pyenv」と「pyenv保存場所/.pyenv/bin」を追加する
3. 注意が出て保存できない場合があるため、vimの場合「:wq!」で強制的に保存する
4. 再起動する

手順2の例として、pyenvを「/home/pi」に保存した場合は以下のように変更します。

.. code-block:: sh
   
   #変更前
   Default secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
   
   #変更後
   Default secure_path="/home/pi/.pyenv/shims:/home/pi/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

Pythonの対話モードでGPUを認識するのにコンソール実行では認識しない
..............................................................................

pythonの対話モードで実行した場合は図 7のようにGPUを認識しているのに、5.3.2，5.4.2，5.5.2を実行した際に「CPU MODE」になってしまう場合があります。その際はNVIDIAドライバが誤った設定でインストールされてしまっている可能性があります。一度NVIDIAドライバをアンインストールして、再度インストールし直してください。
NVIDIAドライバをアンインストールするコマンドは以下になります。

.. code-block:: sh
   
  sudo /usr/bin/nvidia-uninstall
  
コマンドを実行すると、インストール時と同様にGUI式の画面になるため、指示に従ってアンインストールしてください。再度インストールする際は4.1.2でダウンロードしたインストーラを使用してください。

操作方法
============

本システムは「tezip.py」が実行プログラムの本体となります。
引数の使い分けによって、学習機構・圧縮機構・解凍機構の実行を切り替えます。
各種機構実行時に正しくGPUを認識している場合は「GPU MODE」、GPUを認識していない場合は「CPU MODE」という表示がされ、GPU・CPUの使用を自動で切り替えます。GPUメモリのサイズの関係プログラムが動かせなくなる状況を回避するために、GPUを使用しない強制CPUモードにするオプションもあります。詳しくはそれぞれの機構の引数の説明を参照してください。
また、「tezip.py」とは別に、「train_data_create.py」という学習データ作成プログラムがあります。こちらも合わせて記述します。(付録にKittiデータを使用した学習データ作成のサンプルプログラムもあります。学習データを用意できない場合は、こちらを使用してください。)

対応画像のフォーマット
'''''''''''''''''''''''''''''

本システムでは画像の読み込みに「Pillow」を使用しています。Pillowでは以下のような画像が対応フォーマットとしてあります(一部抜粋)。

* bmp
* jpg
* jpg 2000
* png
* ppm

「Pillow」が対応している全てのフォーマットについては　`Pillowのドキュメントページ <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html>`_ より確認できます。

学習データ作成プログラム
'''''''''''''''''''''''''''''

学習データ作成プログラムは「train_data_create.py」になります。PredNetの学習データ作成プログラムに基づき、学習用の画像をhkl形式にして、一つのファイルにダンプします。

フォルダのアーキテクチャ
..........................

学習用画像のフォルダのアーキテクチャは以下のようにしてください。
**<>** で囲まれた階層のフォルダが一つの時系列を表しています。
**""** で囲まれた画像ファイルが、最下層の画像ファイルになります。ソートして順番に読み込むため、画像ファイル名は時系列順に数字を付けることをお勧めします。またその際、数字の桁数が統一されるように、頭に0を付けて調整してください。

例：「image_***.png」という名前で100枚の画像
「image_0000.png」「image_0001.png」「image_0002.png」…「image_0098.png」「image_0099.png」「image_0100.png」
桁数が統一されていない場合、pythonのソート順の問題で「1」の次に「10」が読み込まれてしまいますので注意してください。

.. code-block:: sh
   
   引数で指定した入力画像のフォルダ
   ├─<sequence_1 >
   │     ├─"image_0000.png"
   │     ├─"image_0001.png"
   │      …
   ├─<sequence_2 >
   │     ├─"image_0000.png"
   │     ├─"image_0001.png"
   │     …
   ├─<sequence_3 >
   │     ├─"image_0000.png"
   │     ├─"image_0001.png"
   │     …
    ….

プログラムの実行
..........................

学習データ作成プログラムを実行する流れは以下の通りです。

1. 「仮想環境の作成」のセクションで作成した仮想環境に入ります
2. 本システムのsrcディレクトリに入ります
3. Pythonコマンドでtrain_data_create.pyを実行します。(実行例や引数については以下の「コマンドの実行例と引数」のセクションを参照)

コマンドの実行例と引数
^^^^^^^^^^^^^^^^^^^^^

以下のコマンドを実行してください

.. code-block:: sh
   
  python train_data_create.py 学習用画像ディレクトリ 出力ディレクトリ
 
各引数の意味は以下の通りです。

.. csv-table:: 
   :header: "引数", "意味", "設定例"
   :widths: 10, 25, 15

   "第一引数", Hklファイルにダンプしたい学習用画像が入ったディレクトリパス ,"./data"
   "第二引数", Hklファイルの出力先のディレクトリパス ,"./data_hkl"

実行例として、hklへのダンプを行う場合は以下のコマンドになります。

.. code-block:: sh
   
  python train_data_create.py ./data ./data_hkl
  
出力ファイル
..........................

以下のファイルが指定した出力先ディレクトリに出力されます。

* X_train.hkl
* X_val.hkl
* sources_train.hkl
* sources_val.hkl

「X_***.hkl」は画像データをダンプしたもの、「sources_***.hkl」はディレクトリのアーキテクチャ情報を保存したものになります。
なお、ファイル名は固定値で学習機構から参照されるため、変更しないでください。

学習機構
'''''''''''''''''''''''''''''

学習機構を動かすための流れは以下の通りです。

1. 「仮想環境の作成」の項目で作成した仮想環境に入ります
2. 本システムのsrcディレクトリに入ります
3. Pythonコマンドでtezip.pyを「-l」を入れて実行します。(実行例や引数については参照)

入力ファイル
..........................

* 学習画像データ(X_train.hkl)
* 学習中の検証画像データ(X_val.hkl)
* 学習画像のディレクトリのアーキテクチャ情報(sources_train.hkl)
* 学習中の検証画像のディレクトリのアーキテクチャ情報(sources_val.hkl)

コマンドの実行例と引数
..........................

以下のコマンドを実行してください。

.. code-block:: sh
   
   python tezip.py -l 出力ディレクトリ 学習用データのディレクトリ

各引数の意味は以下の通りです。

.. csv-table:: 
    :header: 引数名, 引数の意味, 入力の数, 入力の意味, 例
    :widths: 10, 15, 10, 25, 15
    
    -l,学習機構を実行,2,"| 1：モデルの出力先ディレクトリのパス
    | 2：学習用データ(.hkl)ディレクトリのパス","| ./model
    | ./tarin_data"
    -f,強制CPUモードのフラグ,0,"「-f」を実行時につけることで、GPUを無効化し、強制的にCPUで実行します","-f"
    -v,画面出力のフラグ,0,"「-v」を実行時につけることで、学習中のlossやエポックなどの学習状況をコンソールに出力します","-v"

実行例は以下の通りです

.. code-block:: sh
   
  python tezip.py -l ./model ./tarin_data

出力ファイル
..........................

以下のファイルが指定した出力先ディレクトリに出力されます。

* モデル構造ファイル（prednet_model.json）
* 重みファイル（prednet_weights.hdf5）
 
圧縮機構
'''''''''''''''''''''''''''''

圧縮機構を動かすための流れは以下の通りです。

1. 「仮想環境の作成」の項目で作成した仮想環境に入ります
2. 本システムのsrcディレクトリに入ります
3. Pythonコマンドでtezip.pyを「-c」を入れて実行します。(実行例や引数については参照)

入力ファイル
..........................

本プログラムでは、学習機構によって出力された以下のファイルが必要です。

* 学習機構によって出力されたモデル構造ファイル（prednet_model.json）
* 学習機構によって出力された学習済みモデルの重みファイル（prednet_weights.hdf5）
* 圧縮対象の画像ファイル群

ソートして順番に読み込むため、圧縮対象の画像ファイル名は時系列順に数字を付けることをお勧めします。またその際、数字の桁数が統一されるように、頭に0を付けて調整してください。
例：「image_***.jpg」という名前で100枚の画像
「image_0000.jpg」「image_0001.jpg」「image_0002.jpg」…「image_0098.jpg」「image_0099.jpg」「image_0100.jpg」
桁数が統一されていない場合、pythonのソート順の問題で「1」の次に「10」が読み込まれてしまいますので注意してください。

コマンドの実行例と引数
..........................

.. code-block:: sh
   
  python tezip.py -c モデルのディレクトリ 圧縮対象画像のディレクトリ 出力ディレクトリ -p ウォームアップ枚数 -wまたは-t  [-w 1枚のキーフレームから推論する枚数 ,-t キーフレーム切り替えのMSEの閾値]  -m エラーバウンド機構名 -b エラーバウンド機構の閾値

各引数の意味は以下の通りです。

.. csv-table:: 
    :header: 引数名, 引数の意味, 入力の数, 入力の意味, 例
    :widths: 10, 15, 10, 25, 15
    
    -c,圧縮機構を実行,3,"| 1：学習済みモデルのディレクトリのパス
    | 2：圧縮対象画像のディレクトリのパス
    | 3：圧縮データの出力先ディレクトリのパス","| ./model
    | ./image_data
    | ./comp_data"
    -w,キーフレーム切り替えの基準の指定,1,"| SWP(Static Window-based Prediction)で実行1枚のキーフレームから何枚推論するかを指定
    | -tと同時に指定した場合はエラー終了となる","-w 5"
    -t,キーフレーム切り替えの基準の指定,1,"| DWP(Dynamic Window-based Prediction)で実行切り替えの基準となるMSE(Mean Square Error)の閾値を指定
    | -wと同時に指定した場合はエラー終了となる","-t 0.02"
    -p,ウォームアップの画像枚数,1,LSTMの記録用に、最初にキーフレームから連続で推論する枚数の指定枚数が多いほどkey_frame.datのサイズが大きくなり、entropy.datのサイズが小さくなる可能性が高くなります。ただし、DWPで実行した際に、0や1にすると、MSEが大きくなり、逆に最終的なキーフレーム数が多くなってしまう可能性があります。,3
    -m,エラーバウンド機構の選択,1,"| エラーバウンド機構の選択以下の4種から選択します
    | abs：absolute error bound
    | rel：relative bound ratio
    | absrel：上記2つを両方実行
    | pwrel：point wise relative error bound
    | 複数選択したり、存在しないものを選択したりした場合はエラー終了します","| abs
    | rel
    | absrel
    | pwrel"
    -b,エラーバウンド機構の閾値,"| 「-m」がabsrelの場合：2
    | それ以外の場合：1","| エラーバウンド機構の許容範囲の閾値を指定「-m」でabsrelを指定した場合は値を2つ入力します。
    | 1つ目：absの閾値
    | 2つ目：relの閾値
    | それ以外は値を1つ入力します。「-m」で指定したものに適切でない個数の入力が与えられた場合はエラー終了します。入力に「0」が含まれている場合はエラーバウンド機構は実行されず、完全非可逆圧縮のデータとなります","| -m abs -b 5
    | -m rel -b 0.1
    | -m absrel -b 5 0.1
    | -m pwrel -b 0.1"
    -f,強制CPUモードのフラグ,0,「-f」を実行時につけることで、GPUを無効化し、強制的にCPUで実行します,-f
    -v,画面出力のフラグ,0,「-v」を実行時につけることで、推論後のMSEの値や圧縮処理にかかった時間など実行中の状況をコンソールに出力します,-v
    -n,圧縮処理のEntropy Codingを無効にするフラグ,0,「-n」を実行時につけることで、圧縮処理として実行されるEntropy Codingを行わずに出力します。Entropy Codingは場合によっては有効に働かず、逆に画像サイズが大きくなる場合が発生する可能性があるためです,-n

実行例は以下の通りです

.. code-block:: sh
   
  python tezip.py -c ./model ./image_data ./comp_data -p 3 -w 5 -m pwrel -b 0.1


出力ファイル
..........................

以下のファイルが指定した出力先ディレクトリに出力されます。

* キーフレームファイル（key_frame.dat）
* 実画像と推論結果の差分（entropy.dat）
* 圧縮前の画像名が記録されたテキストファイル(filename.txt)

ファイル名は、固定値で解凍機構から参照されるため、変更しないでください。



解凍機構
'''''''''''''''''''''''''''''

解凍機構を動かすための流れは以下の通りです。

1. 「仮想環境の作成」の項目で作成した仮想環境に入ります
2. 本システムのsrcディレクトリに入ります
3. Pythonコマンドでtezip.pyを「-u」を入れて実行します。(実行例や引数については参照)

入力ファイル
..........................

本プログラムでは、学習機構・圧縮機構によって出力された以下のファイルが必要です。

* 学習機構の出力
   
  * モデル構造ファイル（prednet_model.json）
  * 学習済みモデルの重みファイル（prednet_weights.hdf5）

* 圧縮機構の出力

  * キーフレームファイル（key_frame.dat）
  * 実画像と推論結果の差分（entropy.dat）
  * 圧縮前の画像名が記録されたテキストファイル(filename.txt)

コマンドの実行例と引数
..........................

以下のコマンドを実行してください。

.. code-block:: sh
   
  python tezip.py -u モデルのディレクトリ 圧縮データのディレクトリ 出力ディレクトリ

各引数の意味は以下の通りです。

.. csv-table:: 
    :header: 引数名, 引数の意味, 入力の数, 入力の意味, 例
    :widths: 10, 15, 10, 25, 15
    
    -u,学習機構を実行,3,"| 1：学習済みモデルのディレクトリのパス
    | 2：圧縮データ(.dat)等のディレクトリのパス
    | 3：解凍データの出力先ディレクトリのパス","| ./model
    | ./comp_data
    | ./uncomp_data"
    -f,強制CPUモードのフラグ,0,"「-f」を実行時につけることで、GPUを無効化し、強制的にCPUで実行します","-f"
    -v,画面出力のフラグ,0,"「-v」を実行時につけることで、解凍中の処理時間をコンソールに出力します","-v"
    
実行例は以下の通りです。

.. code-block:: sh
   
  python tezip.py -u ./model ./comp_data ./uncomp_data

出力ファイル
..........................

以下のファイルが指定した出力先ディレクトリに出力されます。

* 圧縮した画像ファイル群

付録
=============

Kittiデータを使用した学習データ作成のサンプルプログラム
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

学習データ作成のサンプルプログラムは「kitti_train_data_create.py」になります。PredNetの学習データ作成プログラムに基づき、kittiデータセットの大量の画像を学習用のhkl形式にして、一つのファイルにダンプします。

システム概要
............

学習データ作成プログラムは以下の2つのブロックからなります。

* 画像データのダウンロード・解凍
* データのダンプ(hklファイルに変換)

データのダウンロードには、200GB程度の容量が必要になります。ダウンロード直後のzipファイルが165GB、解凍後は30GBという内訳になります。
データのダンプは、ダウンロード後のデータをそのまま実行すると、1248×376サイズの画像を42128枚メモリに格納する必要があります。環境によってはメモリ不足により、以下のようなエラーを出す場合があります。その場合は、画像枚数を減らしてから実行してください。

.. code-block:: sh
   
  numpy.core._exceptions.MemoryError: Unable to allocate 55.2 GiB for an array with shape (42128, 376, 1248, 3) and data type uint8
  
フォルダのアーキテクチャ
..........................

ダウンロードしたkittiデータのアーキテクチャは以下のようになっています。
<>で囲まれたの階層のフォルダが一つの時系列を表しています。「city」「residential」「road」についてはkittiデータのカテゴリの分類になります。今回のPredNetへの使用には特に影響はありません。
データを減らす場合は<>で囲まれたフォルダから削除してください。
ただし、「city/2011_09_26_drive_0005_sync」は学習中の検証データに割り当てられているため、削除しないようにしてください。
データを入れ替える場合は、""で囲まれた最下層の画像ファイルだけを入れ替えて、フォルダ構成はそのままにするようにしてください。
追加する場合は、同じようなフォルダの階層構造にして、赤字から追加してください。

.. code-block:: sh
   
   raw
   ├─city
   │    ├─<2011_09_26_drive_0001_sync>
   │    │    └─2011_09_26
   │    │         └─2011_09_26_drive_0001_sync
   │    │              └─image_03
   │    │                   └─data
   │    │                        ├─"0000000000.png"
   │    │                        ├─"0000000001.png"
   │    │                         …
   │    ├─<2011_09_26_drive_0002_sync>
   │     …
   ├─residential
   │    ├─<2011_09_26_drive_0001_sync>
   │     …
   └─road
      ├─<2011_09_26_drive_00015_sync>
          …

プログラムの実行
..........................

学習データ作成プログラムを実行する流れは以下の通りです。

1. 「仮想環境の作成」の項目で作成した仮想環境に入ります
2.	本システムのsrcディレクトリに入ります
3.	Pythonコマンドでkitti_train_data_create.pyを実行します。(実行例や引数については以下の「コマンドの実行例と引数」の項目参照)


コマンドの実行例と引数
^^^^^^^^^^^^^^^^^^^^^

以下のコマンドを実行してください。

.. code-block:: sh

   python kitti_train_data_create.py 出力ディレクトリ -d -p

各引数の意味は以下の通りです。

.. csv-table:: 
    :header: 引数, 意味, 設定例
    :widths: 15, 25, 15
    
    第一引数,Hklファイルの出力先のディレクトリパス,./data
    -d,Kittiデータセットのダウンロードを行うフラグ,-d
    -p,画像データ群をhklに変化する処理を行うフラグ。-dの出力ディレクトリと-pの入出力ディレクトリは共通になります,-p
    
実行例として、データをダウンロードして、そのままhklへのダンプを行う場合は以下のコマンドになります。

.. code-block:: sh

   python kitti_train_data_create.py ./data -d -p
   
出力ファイル
..........................

以下のファイルが指定した出力先ディレクトリに出力されます。

* 画像データのダウンロード・解凍
  
  * raw.zip
  * rawディレクトリ(中身の概要は5.2.1を参照)

* データのダンプ(hklファイルに変換)
  
  * X_train.hkl
  * X_val.hkl
  * sources_train.hkl
  * sources_val.hkl

「X_***.hkl」は画像データをダンプしたもの、「sources_***.hkl」はディレクトリのアーキテクチャ情報を保存したものになります。
なお、ファイル名は固定値で学習機構から参照されるため、変更しないでください。
