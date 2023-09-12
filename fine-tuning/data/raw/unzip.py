import os

# 将同级目录中所有的.jar文件后缀名改为.zip
for file in os.listdir('.'):
    if file.endswith('.jar'):
        os.rename(file, file[:-4] + '.zip')

# 将所有.zip文件解压到同级目录下
for file in os.listdir('.'):
    if file.endswith('.zip'):
        os.system('unzip ' + file + ' -d ' + file[:-4])
