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
