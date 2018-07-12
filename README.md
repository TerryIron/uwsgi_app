# uwsgi_app README

## Requirements(软件需求)
* Python 2.7+

## Getting Started(如何部署启动)
### Virtualenv(python虚拟环境安装)
* 进入安装目录
```
cd <directory containing this file>
```

* 安装依赖包
```
$VENV/bin/pip install -e .
```

* 安装开发环境
```
$VENV/bin/python setup.py develop
```

* 启动服务 
```
# 启动正式版本
./run_ini.sh
# 启动开发版本
./run_ini.sh -d
```

## Coding Started(如何提交代码)
* 进入安装目录
```
cd <directory containing this file>
```

* 格式化代码
```
./reformat
```

* 提交代码
```
git pull origin master; git push origin master
```
