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

TEZip overview

==============

This system consisits of three mechanisms.

1. Learning mechanism
2. Compression mechanism
3. Decompression mechanism

 

Learning mechanism

``````````````````

`PredNet <https://coxlab.github.io/prednet/>`_ is used to learn the change in the movement of an object over time.
According to the learning method of PredNet, the learning data is converted into the hkl format and then learned.
The learned model is output to a file. This file is used by the compression mechanism and decompression mechanism.
Use another program to download the training data and convert it to hkl.

 

Compression mechanism

``````````````````````

Using the model output by the learning mechanism, the results of inference and difference of time series images are compressed.
After deriving the difference between the original image and the inference result,error-bounded quantization, Density-based Spatial Encoding, and Partitioned Entropy Encoding are processed. These processes have the effect of increasing the compression rate when compressing.
Use the zstd library to compress and output to a binary file (.dat).

And,differences and keyframe images are also output to a binary file (.dat) using the zstd library.

 

Decompression mechanism

`````````````````````````

Using the model output by the learning mechanism and the binary file (.dat) output by the compression mechanism, the image group input to the compression mechanism is restored.
By inferring by inputting keyframes, the inference result of the compression mechanism is reproduced.
The processing of Density-based Spatial Decoding and Partitioned Entropy Decoding is performed in the reverse order of the compression mechanism, and the original difference is restored.
Since the error-bounded quantization process is lossy compression, it is not included in the decompression mechanism.
The inference result and the difference are added to restore the original image and output it.

Operating environment
========
In this case, we used AWS EC2 to build the machine.

EC2 Information
'''''''''''
* AMI
   CentOS 7.9.2009 x86_64 - ami-00f8e2c955f7ffa9b
* Instance Type
   p2.xlarge
   
マシン情報概要
''''''''''''''

* Operating Systems
   CentOS7

* CPU
   Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz×4 
  
* GPU
   NVIDIA K80(12GB)
   
* Memory
   64GB

Environment construction procedure
============

Follow the steps below to build the environment.

* Install the NVIDIA driver
* Install CUDA
* Install cuDNN
* Create a virtual environment

Install the NVIDIA driver
'''''''''''''''''''''''''''''
Follow the steps below to install the driver so that you can use NVIDIA's GPU.

Disable the standard driver
..........................
You need to turn off the standard driver so that it does not interfere with the installation of the NVIDIA driver. Please execute the following command.

.. code-block:: sh

  lsmod | grep nouveau
  
Then, use a text editor such as vim to create a file in the following directory.

.. code-block:: sh

   /etc/modprobe.d/blacklist-nouveau.conf

Write the following settings in the file you created and save it.

.. code-block:: sh

   blacklist nouveau
   options nouveau modeset=0
   
Then reboot and run the following command. If nothing is displayed, the disabling has been successful.

.. code-block:: sh

   lsmod | grep nouveau
   
Running the installation
..........................
Install the package required to install the NVIDIA driver. Execute the following command.

.. code-block:: sh

   yum -y install kernel-devel kernel-devel-$(uname -r) kernel-header-$(uname -r) gcc gcc-c++ make
  
Then, check the name of your GPU device. You can check it by running the following command.

.. code-block:: sh

   lspci | grep -i nvidia

From the`NVDIA driver download page <https://www.nvidia.co.jp/Download/index.aspx?lang=jp/>`_ as shown in the following figure, select your GPU device and proceed to installation.For **CUDA Toolkit**, please select **10.0**.

.. image:: ./img/img1.png

Next, run the downloaded file to run the NVIDIA driver installer.The following command is an example.Please replace the file name with the one you have downloaded and run it.

.. code-block:: sh

   sh NVIDIA-Linux-x86_64-410.129-diagnostic.run
   
Select "YES" for all of the installer's selections to execute the installation.
The installation is complete when the screen shown in the following figure is displayed.

.. image:: ./img/img2.png

Execute the following command, and if the screen shown in the figure below is displayed, it has been installed correctly.
Select "YES" for all of the installer's selections to execute the installation.

.. code-block:: sh

   nvidia-smi

.. image:: ./img/img3.png

Install CUDA
'''''''''''''''''''''''''''''

Install CUDA to use the GPU in your programs.
In this case, we will use the CUDA **10.0** version.
Open`the download page <https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Linux&target_arch=x86_64&target_distro=CentOS&target_version=7&target_type=rpmlocal>`_ shown in the figure below and select "Linux", "x86_64", "CentOS", "7", "rpm(local)" or "rpm(network)" to download the installer.

.. image:: ./img/img4.png

Next, run the downloaded file to run the CUDA 10.0 installer. Please run the following command.

.. code-block:: sh

   sudo yum -y install epel-release
   sudo rpm -i cuda-repo-rhel7-10-0-local-10.0.130-410.48-1.0-1.x86_64.rpm
   yum clean all
   yum install cuda

Then, run the following command to pass it through. To reflect the result, please reboot after running it.

.. code-block:: sh

   echo ' PATH=”/usr/local/cuda-10.0/bin${PATH:+:${PATH}}"' >> ~/.bashrc
   echo 'export LD_LIBRARY_PATH=”/usr/local/cuda-10.0/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"' >> ~/.bashrc

After rebooting, please execute the following command. If the screen shown in the figure below appears, the software has been installed correctly.

.. code-block:: sh

   nvcc -V

.. image:: ./img/img5.png

Install cuDNN
'''''''''''''''''''''''''''''

Following CUDA, we will download cuDNN to use GPU in our programs.
You will need to create an NVIDIA account in advance. You may be asked to log in during the following procedure, so if you haven't created one, please do so at that time.
This time, we will use cuDNN **7.6.5** version.
Go to`the download page <https://developer.nvidia.com/rdp/cudnn-archive>`_ shown in the figure below and select "Download cuDNN v7.6.5 (November 5th, 2019), for CUDA 10.0" and "cuDNN Library for Linux" to download.

.. image:: ./img/img6.png

After the download is complete, unzip the file and place it in an appropriate location. Execute the following command.

.. code-block:: sh

   tar zxf cudnn-10.0-linux-x64-v7.6.5.32.tgz
   sudo cp -a cuda/include/* /usr/local/cuda/include/
   sudo cp -a cuda/lib64/* /usr/local/cuda/lib64/
   sudo ldconfig

Create a virtual environment
'''''''''''''''''''''''''''''

To separate the Python environment and make it easier to manage, we will use a virtual environment.
In this case, we will use "pyenv". We will install and use "anaconda" in it.


Install pyenv
..........................

Install pyenv and enable the "pyenv" command. Execute the following command and then reboot.

.. code-block:: sh

   git clone https://github.com/yyuu/pyenv.git ~/.pyenv
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
   echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc

If you are using pyenv, use pip to install the library. This may involve unzipping the zip file, so if you do not have the zip command, you will need to install it. You can install it by running the following command

.. code-block:: sh

   yum -y install zip unzip bzip2
   
Install anaconda
..........................

Install anaconda in pyenv to create a virtual environment. You can run the command "pyenv install -l" to see a list of environments that can be installed. This time, we will use "anaconda3-4.3.1". The command to create a virtual environment is as shown below.

.. code-block:: sh

   eval "$(pyenv init -)"
   pyenv install anaconda3-4.3.1

After that, you can enter the virtual environment by executing the following command.

.. code-block:: sh

   pyenv rehash
   pyenv global anaconda3-4.3.1

Run the following command to check the version, and if you see the following message, you have entered the virtual environment.

.. code-block:: sh

   python -V
   Python 3.6.0 :: Anaconda 4.3.1 (64-bit)

Install the required libraries
..........................

pyenv + anaconda で環境に入った後は、pipを使用して必要なライブラリをインストールします。まずは以下のコマンドでpipのアップデートをします。

.. code-block:: sh

   pip install --upgrade pip
   
Next, run the following command to install the necessary libraries.

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

If you want to run the sample program for creating training data using Kitti data in the appendix, please install the following libraries additionally.

.. code-block:: sh

   pip install requests==2.25.1
   pip install bs4
   pip install imageio==2.9.0

If you run the following command and see "GPU" in the device_type field in the figure below, your Python program has successfully recognized the GPU.

.. code-block:: sh

   python
   # python interactive mode below
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
