# redis-quick-setup
quick setup redis cluster and redis sentinel.

# 主要目的

此项目主要目的是快速在本地搭建 redis cluster 集群 和 redis sentinel (master-slaves) 服务.

# 脚本使用方法

> 建议在执行脚本前 先查看其中的逻辑, 根据需要修改

## 准备工作

1. [下载 redis 源码](https://redis.io/download), 解压 , 源码目录名称改为 `redis` .
   
2. 编译 redis 源码 (make)

## 使用脚本


### setup-cluster.py

下载脚本 放在与 `redis` 目录同级的目录中.

执行以下命令

```bash
python setup-cluster.py
```

**作用**

1. 脚本会自动创建 一个目录:`redis-cluster`, 内部包含默认的所有配置(脚本已经自动进行配置)
2. 启动所有 redis 实例
3. 执行 cluster meet 组建集群
4. (根据 master 数量)平分 16384 的槽位, 并 进行 addslots (**此步骤耗时较长**)
5. 对从节点进行 replicate

默认三个节点, 端口 分别是 7001, 7002, 7003

### setup-sentinel.py

下载脚本 放在与 `redis` 目录同级的目录中.

执行以下命令

```bash
python setup-sentinel.py
```

**作用**

1. 脚本会自动创建目录 : `redis-sentinel`, 内部包含 redis 和 sentinel 的配置(脚本已经自动进行配置)
2. 启动所有 redis 实例 (1 master, N slaves)
3. 启动所有 sentinels 示例

redis 默认端口 6001(master), 6002 (slave), 6003 (slave)
sentinel 默认端口 26001, 26002, 26003



