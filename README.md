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
./run_ini.sh
```
