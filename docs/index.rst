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

`NVDIAドライバダウンロードのページ <https://www.nvidia.co.jp/Download/index.aspx?lang=jp/>`_ から自分のGPUデバイスを選択してインストールに進みます。「CUDA Toolkit」については「10.0」を選択してください。

次にダウンロードしたファイルを実行してNVIDIAドライバのインストーラを実行します。以下のコマンドは一例になります。ダウンロードしたファイル名に置き換えて実行してください。

.. code-block:: sh

   sh NVIDIA-Linux-x86_64-410.129-diagnostic.run
   
インストーラの選択に対して全て「YES」を選択してインストールを実行します。
以下のコマンドを実行して、図 3のような画面が表示されれば、正しくインストールされています。

.. code-block:: sh

   nvidia-smi
   
CUDAのインストール
'''''''''''''''''''''''''''''

GPUをプログラムで使用するためにCUDAをインストールします。
今回は、CUDA **10.0** のバージョンを使用します。
`ダウンロードページ <https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Linux&target_arch=x86_64&target_distro=CentOS&target_version=7&target_type=rpmlocal>`_ を開き「Linux」「x86_64」「CentOS」「7」「rpm(local) または rpm(network)」を選択してインストーラのダウンロードを行ってください。
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

再起動した後は以下のコマンドを実行してください。図 5のような画面が表示されれば、正しくインストールされています。

.. code-block:: sh

   nvcc -V
   
cuDNNのインストール
'''''''''''''''''''''''''''''

CUDAに引き続きGPUをプログラムで使用するためにcuDNNをダウンロードします。
なお、こちらについてはあらかじめNVIDIAアカウントを作成する必要があります。下記手順の途中でログインを要求されることがあるので未作成の場合は、そのタイミング作成してください。
今回はcuDNN **7.6.5** のバージョンを使用します。
`ダウンロードページ <https://developer.nvidia.com/rdp/cudnn-archive>`_ を開き、「Download cuDNN v7.6.5 (November 5th, 2019), for CUDA 10.0」「cuDNN Library for Linux」を選択してダウンロードしてください。
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

以下のコマンドを実行して図 7のようにdevice_typeに”GPU”がある場合は、pythonプログラムからGPUを認識することに成功しています。

.. code-block:: sh

   python
   # 以下pythonの対話モード
   >>> from tensorflow.python.client import device_lib
   >>> device_lib.list_local_devices()

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
