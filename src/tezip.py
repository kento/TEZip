import argparse
import train 
import compress
import decompress
import os

from tensorflow.python.client import device_lib


def main(arg):

  if arg.force:
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

  # GPUの有無を確認
  devices = device_lib.list_local_devices()
  GPU_flag = False

  for device in devices:
    if device.device_type == 'GPU':
      GPU_flag = True

  if GPU_flag:
    print('GPU MODE')
  else:
    print('CPU MODE')

  if (arg.learn != None and arg.compress != None) or (arg.compress != None and arg.uncompress != None) or (arg.learn != None and arg.uncompress != None):
    print('ERROR')
    print('Please select only one of learn or compress or uncompress.')
    print('Command to check the options is -h or --help')
  
  elif arg.learn != None:
    print('train mode')
    train.run(arg.learn[0], arg.learn[1], arg.verbose)

  elif arg.compress != None:
    print('compress mode')
    if arg.preprocess != None:
      if arg.window == None and arg.threshold == None:
        print('ERROR')
        print('Please specify the window size(-w or --window) or MSE threshold(-t or --threshold) option!')
        print('Select window size for SWP and MSE threshold for DWP.')
      elif arg.window != None and arg.threshold != None:
        print('ERROR')
        print('Please select only one of window size(-w or --window) or MSE threshold(-t or --threshold)!')
        print('Select window size for SWP and MSE threshold for DWP.')
      else:
        print(arg.mode[0])
        if arg.mode[0] == 'abs' or arg.mode[0] == 'rel' or arg.mode[0] == 'absrel' or arg.mode[0] == 'pwrel':
          if arg.bound != None and len(arg.bound) != 0:
            if ((arg.mode[0] == 'abs' or arg.mode[0] == 'rel' or arg.mode[0] == 'pwrel') and len(arg.bound) == 1) or (arg.mode[0] == 'absrel' and len(arg.bound) == 2):
              if arg.window != None:
                compress.run(arg.compress[0], arg.compress[1], arg.compress[2], arg.preprocess[0], arg.window[0], arg.threshold, arg.mode[0], arg.bound, GPU_flag, arg.verbose, arg.no_entropy)
              elif arg.threshold != None:
                compress.run(arg.compress[0], arg.compress[1], arg.compress[2], arg.preprocess[0], arg.window, arg.threshold[0], arg.mode[0], arg.bound, GPU_flag, arg.verbose, arg.no_entropy)
              else:
                print('unexpected error')
            else:
              print('ERROR')
              print('If the -m or --mode is \'abs\' or \'rel\' or \'pwrel\', enter one for -b or --bound. : value')
              print('If the -m or --mode is \'absrel\', enter two in -b or --bound. : abs_value rel_value')
          else:
            print('ERROR')
            print('Please specify the -b or --bound option!')
            print('error bound value.')
        else:
          print('ERROR')
          print('Please specify the -m or --mode correctly!')
          print('\'abs\' or \'rel\' or \'absrel\' or \'pwrel\'.')
    else:
      print('ERROR')
      print('Please specify the -p or --preprocess option!')
      print('warm up num.')
  
  elif arg.uncompress != None:
    print('uncompress mode')
    decompress.run(arg.uncompress[0], arg.uncompress[1], arg.uncompress[2], GPU_flag, arg.verbose)
  
  else:
    print('ERROR')
    print('Please mode select!')
    print('learn or compress or uncompress.')
    print('Command to check the options is -h or --help')


if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='TEZIP', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-l', '--learn', type=str, nargs=2, metavar=('model', 'dir'), dest='learn')
  parser.add_argument('-c', '--compress', type=str, nargs=3, metavar=('model', 'dir', 'file'), dest='compress')
  parser.add_argument('-u', '--uncompress', type=str, nargs=3, metavar=('model', 'file', 'dir'), dest='uncompress')
  parser.add_argument('-p', '--preprocess', type=int, nargs=1, metavar=('warm_up_num'), dest='preprocess')
  parser.add_argument('-w', '--window', type=int, nargs=1, metavar=('window_size'), dest='window')
  parser.add_argument('-t', '--threshold', type=float, nargs=1, metavar=('MSE_threshold'), dest='threshold')
  parser.add_argument('-m', '--mode', type=str, nargs=1, metavar=('mode'), dest='mode')
  parser.add_argument('-b', '--bound', type=float, nargs='*', metavar=('value'), dest='bound', default=None)
  parser.add_argument('-f', '--force', action='store_true')
  parser.add_argument('-v', '--verbose', action='store_true')
  parser.add_argument('-n', '--no_entropy', action='store_false')
  args = parser.parse_args()
  main(args)