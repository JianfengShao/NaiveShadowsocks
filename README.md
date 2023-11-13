# Build your on Shadowsocks

---

Shadowsocks的极简实现，个人测试可用（2023年11月），项目仅出于个人学习网络知识而编写。

所用Python版本为3.8+，基于asyncio的最新语法实现协程。

项目参考了[Lightsocks-Python](https://github.com/linw1995/lightsocks-python)。

由于时间原因，目前只是粗糙实现，计划后续加入代码实现原理讲解，以及相应功能补充。

## 安装
直接从Github克隆即可，Python无需安装其他包。

Python版本: 3.8+，无其他要求

## 使用
### 1. 设置相关配置

编辑配置文件（配置文件所在位置： ./utils/config.py）
- 配置文件中的server_ip需要修改为你自己代理服务器的IP，事例中的server_ip仅是随机生成的IP的地址
- 其他配置根据个人喜好
- 完成配置文件的设置后，修改系统Sock5代理，ip为local_ip，port为local_port

```python
server_ip = "164.132.150.65"  # 代理服务器地址
server_port = 6120  # 代理服务器监听端口
local_ip = "127.0.0.1"  # 本地主机地址
local_port = 1080  # 本地主机监听端口

BUFFER_SIZE = 1024
```

### 2. 运行 NaiveShadowsocks

NaiveeShadowsocks需要在本地主机和服务器同时运行服务。
使用流程如下

- 运行nsserver（第一次运行会在当前目录生成password.json)
- 运行nslocal（第一次运行时需要将在服务器中生成的password.json拷贝到本地主机)

#### nsserver

运行在海外服务器的Shadowsocks客户端

```python
python
nsserver.py
```

#### nslocal

运行在本地主机的Shadowsocks客户端

```python
python
nslocal.py
```
