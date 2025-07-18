# 自动化运维在容器化场景中的最佳实践

## 注意 ⚠️

- _斜体表示引用_
- **未经允许，禁止转载**

## Prerequisite

- 熟悉 Linux 系统的基本配置和命令
- 了解或使用过 Python 更佳

## 课程目录

| 日程    | 时间 | 课程              | 内容                                     |
| ----- | -- | --------------- | -------------------------------------- |
| 第 1 天 | 上午 | [运维基础](#1-运维基础) | [1.1 自动化运维概述](#11-自动化运维概述)             |
|       |    |                 | [1.2 Python 和系统运维](#12-python-和系统运维)   |
|       | 下午 |                 | [1.3 容器技术和自动化运维](#13-容器技术和自动化运维)       |
| 第 2 天 | 上午 |                 | [1.4 K8S 和自动化运维](#14-k8s-和自动化运维)       |
|       |    | [配置管理](#2-配置管理) | [2.1 自动化运维框架](#21-自动化运维框架)             |
|       |    |                 | [2.2 Fabric](#22-fabric)               |
|       | 下午 |                 | [2.3 Ansible 基础](#23-ansible-基础)       |
|       |    |                 | [2.4 Ansible 和容器技术](#24-ansible-与容器技术) |
| 第 3 天 | 上午 |                 | [2.5 Ansible 与云平台](#25-ansible-与云平台)   |
|       |    | [任务管理](#3-任务管理) | [3.1 版本控制](#31-版本控制)                   |
|       |    |                 | [3.2 Jenkins+Zuul](#32-jenkinszuul)    |
|       | 下午 |                 | [3.3 Drone](#33-drone)                 |
|       |    |                 | [3.4 CI-CD](#34-ci-cd)                 |
| 第 4 天 | 上午 | [监控计量](#4-监控计量) | [4.1 监控框架对比](#41-监控框架对比)               |
|       |    |                 | [4.2 Promtheus](#42-prometheus)        |
|       |    |                 | [4.3 Alertmanager](#43-alertmanager)   |
|       |    |                 | [4.4 Grafana](#44-Grafana)             |
|       | 下午 | [日志分析](#5-日志分析) | [5.1 Fluentd](#51-Fluentd)             |
|       |    |                 | [5.2 ElasticSearch](#52-ElasticSearch) |
|       |    |                 | [5.3 Kibana](#53-Kibana)               |
|       |    |                 | [5.4 其它的日志收集和分析方案](#54-其它的日志收集和分析方案)   |

其它：[6. 问题排查案例](#6-问题排查案例)

## 1. 运维基础

[返回目录](#课程目录)

### 1.1 自动化运维概述

[返回目录](#课程目录)

当我们讨论“自动化运维”，我们在讨论什么？

- 数据中心自动化（DCA）？
- 开发运营一体化（DevOps）？

Redhat
对“自动化运维“的定义：[_the use of software to create repeatable instructions and processes to replace or
reduce human interaction with IT
systems._](https://www.redhat.com/en/topics/automation/whats-it-automation)
**使用软件创建可重复的指令和过程，以取代或减少与 IT 系统的人机交互。自动化软件在这些指令、工具和框架的限制下工作，以执行任务，几乎不需要人工干预**。

自动化运维包括：

- **自动化**
  - 应用的自愈
  - 资源的自动弹性缩放
  - 无人工干预下的安装部署
  - 不影响业务的升级和回滚
  - 自服务化的资源和权限获取
  - 基于机器学习的监控、日志分析、告警和预警
- **配置管理**
- **监控**

自动化应用于：

- **基础设施即代码**：通过自动化代码在各类基础设施平台（依据各类模版）管理资源
- **配置管理**：应用所需的配置（不同的设置、文件系统、端口、用户等等）
- **应用编排**：应用可能会被部署在不同的云平台上
- **IT 迁移**：数据或软件从一个系统（操作系统、云平台）转移到另一个系统
- **安全与合规**：流程标准化与审计

未来的自动化形态：

- _From bare metal to middleware, apps, security, updating, notifications, failover, predictive
  analytics, and decisions being made with no direct oversight._
  从裸机到中间件的自动化、应用程序、安全性、更新、通知、故障切换、预测分析，以及在没有直接监督的情况下做出的决策。
- _A security risk being automatically detected, reported, patched, tested, and deployed while your
  IT staff are asleep. Your system could self-heal, gather relevant information to discover if and
  where an attack came from, notify the correct people—all without losing uptime._ 在 IT
  员工睡觉时自动检测、报告、修补、测试和部署安全风险。您的系统可以自我修复，收集相关信息以发现攻击是否以及来自何处，并在不损失正常运行时间的情况下通知所有相关的人。

**自动化运维技术栈**：

- Linux 基础：bash / vim / systemd
- 企业级应用服务管理：文件服务 / Web 服务 / DNS 等
- 流程管理：版本控制 / review / 任务管理 / 工单系统 / 制品仓库
- 中间件服务：数据库、缓存、消息队列、LB、VIP、Cluster
- 云平台：OpenStack / KVM / EXSI / K8S / Docker
- 运维框架：Ansible / Fabric / Puppet / Chef
- 监控和日志： Zabbix / SkyWalking / GAP / EFK
- 编程：Python / Java / Web Service Framwork
- 数据分析和机器学习：Numpy / Pandas / Sklearn / TF / PyTorch

运维技术的判断标准：八荣八耻

- 以可配置为荣，以硬编码为耻
- 以互备为荣，以单点为耻
- 以随时重启为荣，以不能迁移为耻
- 以整体交付为荣，以部分交付为耻
- 以无状态为荣，以有状态为耻
- 以标准化为荣，以特殊化为耻
- 以自动化工具为荣，以手动和人肉为耻
- 以无人值守为荣，以人工介入为耻

### 1.2 Python 和系统运维

[返回目录](#课程目录)

#### 1.2.1 无处不在的 Bash

[返回目录](#课程目录)

[bash 编程快速入门](shell-quick-start.md)

- 作业：[字符串处理、流程控制、数值计算](/src/automation/automation.sh)

#### 1.2.2 简单强大的 Python

[返回目录](#课程目录)

##### 1.2.2.1 Windows 环境中 Python 安装和调试

[返回目录](#课程目录)

参考：[Python 安装](Installation-Python.md)

- 作业：部署完成 Python

  ```console
  $ python --version
  Python 3.9.7

  $ pip --version
  pip 22.0.3 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)

  $ python
  Python 3.9.7 (default, Sep  3 2021, 12:37:55)
  [Clang 12.0.5 (clang-1205.0.22.9)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  ```

  ```python
  >>> print(2**64)
  18446744073709551616

  >>> print('hello, world')
  hello, world

  >>> exit()
  ```

参考：[VSCode 部署](Installation-VSCode.md)

- 作业：VSCode 对 Python 程序进行断点调试

##### 1.2.2.2 Linux 环境中 Python 安装和调试

[返回目录](#课程目录)

**基础环境安装**，参考：[Github](https://github.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#111-%E5%86%85%E6%A0%B8%E5%8D%87%E7%BA%A7)
或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#111-%E5%86%85%E6%A0%B8%E5%8D%87%E7%BA%A7)

- 作业：升级内核到 5.4
- 作业：升级 Python 到 3.8
- 作业：升级 Git 到 2 版本

**VSCode 安装 Remote 插件**

- 作业：VSCode 远程访问 Linux 服务器上的代码

[virtualenv 环境](https://pypi.org/project/virtualenv)

```bash
python3 -m pip install virtualenv
# python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple virtualenv
```

```console
$ python3 -m virtualenv --version
virtualenv 20.7.0 from /usr/local/lib/python3.9/site-packages/virtualenv/__init__.py

$ python3 -m virtualenv .venv
created virtual environment CPython3.9.7.final.0-64 in 869ms
  creator CPython3Posix(dest=/Users/wuwenxiang/local/github-99cloud/lab-openstack/.venv, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/Users/wuwenxiang/Library/Application Support/virtualenv)
    added seed packages: pip==22.1.2, setuptools==62.2.0, wheel==0.37.1
  activators BashActivator,CShellActivator,FishActivator,PowerShellActivator,PythonActivator

$ . .venv/bin/activate

(.venv) $ python3 --version
Python 3.9.7

(.venv) $ pip --version
pip 22.1.2 from /Users/wuwenxiang/local/github-99cloud/lab-openstack/.venv/lib/python3.9/site-packages/pip (python 3.9)
```

##### 1.2.2.3 Python 和自动化运维

[返回目录](#课程目录)

参考：[Python 入门](we-know-python.md)

对于自动化运维，你应该掌握的 Python 知识：

- 基础语法：分支结构、循环、函数、类、异常处理
- 基本对象类型和数据结构：变量和对象、数字、字符串（正则表达式）、元组、列表、集合、字典
- 与 Bash 交互：`-c`，`sys.argv`，`os.system`，`subprocess.check_output`，标准输入输出重定向
- 文件和目录：目录遍历、临时文件
- 数据库：SqlAlchemy
- Web 客户端：requests、json
- 其它客户端：mail / ssh / office 等
- 系统相关模块：psutil / IPy 等

作业：

1. [文件和字符串处理](python-exec-public.py#L628-666)
2. [数据库相关](python-exec-public.py#L1669-2010)
3. [Excel 处理](python-exec-public.py#L2377-2407)
4. [系统相关模块](python-exec-public.py#L2086-2375)
5. [文件目录、子进程、FTP、SSH](/src/automation/automation.py)
6. [XML 解析](python-exec-public.py#L2012-2074)
7. [结构化数据爬取](python-exec.py)
8. [非结构化数据爬取](python-exec-public.py#L1483-1511)
9. [科学计算和机器学习](python-exec-public.py#L2445-3195)

### 1.3 容器技术和自动化运维

[返回目录](#课程目录)

#### 1.3.1 Linux 容器和 Docker

[返回目录](#课程目录)

参考：[Github](https://github.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#211-linux-%E5%AE%B9%E5%99%A8%E5%92%8C-docker)
或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#211-linux-%E5%AE%B9%E5%99%A8%E5%92%8C-docker)

- 作业：安装 Docker
- 作业：熟悉 Docker 命令

#### 1.3.2 Docker 和 Containerd

[返回目录](#课程目录)

参考
[Github](https://github.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#22-containerd)
或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#22-containerd)

- 作业：安装 Containerd
- 作业：熟悉 crictl / ctr / nerdctr 命令

### 1.4 K8S 和自动化运维

[返回目录](#课程目录)

#### 1.4.1 K8S 部署

[返回目录](#课程目录)

组件和基本架构，参考：[Github](https://github.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#3-k8s-%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E7%AE%A1%E7%90%86)
或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#3-k8s-%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E7%AE%A1%E7%90%86)

部署单节点
K8S，参考：[Github](https://github.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#3111-%E5%8D%95%E8%8A%82%E7%82%B9%E9%9B%86%E7%BE%A4%E9%83%A8%E7%BD%B2)
或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#3111-%E5%8D%95%E8%8A%82%E7%82%B9%E9%9B%86%E7%BE%A4%E9%83%A8%E7%BD%B2)，注意：Containerd
如果已经部署好的话，前面部署 Containerd 的步骤可以跳过，直接部署 K8S 即可。

- 作业：完成 K8S 单节点部署

#### 1.4.2 将应用部署到 K8S

参考：[Github](http://github.com/99cloud/training-kubernetes/blob/master/doc/class-01-Kubernetes-Administration.md#29-%E5%90%AF%E5%8A%A8%E4%B8%80%E4%B8%AA-pod)
或
[Gitee](https://gitee.com/dev-99cloud/training-kubernetes/blob/master/doc/class-01-Kubernetes-Administration.md#29-%E5%90%AF%E5%8A%A8%E4%B8%80%E4%B8%AA-pod)

- 作业：完成 K8S 应用部署和发布

## 2. 配置管理

[返回目录](#课程目录)

### 2.1 自动化运维框架

[返回目录](#课程目录)

常见的自动化运维框架包括：

- [Ansible](https://docs.ansible.com/ansible/2.9/index.html)
- [Fabric](https://github.com/fabric/fabric)
- [SaltStack](https://docs.saltproject.io/en/getstarted/)
- [Chef](https://www.chef.io/solutions)
- [Puppet](https://puppet.com/)

| **对比维度** | **Ansible**      | **Puppet**              | **Chef**                 | **SaltStack**     | **Fabric**       |
| -------- | ---------------- | ----------------------- | ------------------------ | ----------------- | ---------------- |
| **架构**   | 无代理（SSH）         | 客户端 - 服务器（Agent-Server） | 客户端 - 服务器（Client-Server） | 混合架构（代理 / 无代理）    | 无架构（直接 SSH）      |
| **配置语言** | YAML（Playbook）   | Puppet DSL（特定领域语言）      | Ruby DSL（Recipe）         | YAML/Python       | Python 脚本        |
| **状态管理** | 支持（声明式）          | 强支持（状态驱动，自动修复）          | 支持（资源定义）                 | 支持（States）        | 不支持（仅执行命令）       |
| **学习曲线** | 低（YAML 易读，语法简单）  | 中高（DSL 需专门学习）           | 中（需懂 Ruby 基础）            | 中（模块多，概念稍复杂）      | 极低（Python 基础即可）  |
| **并发性能** | 中等（依赖 SSH 并发）    | 高（Agent 缓存机制）           | 中高（Client 本地执行）          | 极高（ZeroMQ 异步通信）   | 低（串行 / 简单并行）     |
| **适用规模** | 中小到大型（万级节点需优化）   | 大型（企业级，十万级节点）           | 中大型（开发主导的复杂环境）           | 超大型（实时监控 + 大规模部署） | 小型（临时任务 / 小规模节点） |
| **典型场景** | 配置管理、应用部署、容器集成   | 长期基础设施稳定管理（如 IDC）       | 开发与运维协同（CI/CD 流程）        | 实时操作、云平台管理、监控     | 临时脚本执行、批量命令      |
| **生态集成** | 强（容器、GitOps、云厂商） | 强（企业级工具链，如 Foreman）     | 强（开发工具链，如 Jenkins）       | 强（云、监控、网络设备）      | 弱（仅基础命令扩展）       |

如何选择？

**选 Ansible**：

- 团队追求 “低门槛”“快速上手”，无需维护客户端；
- 需结合容器（Docker/K8s）、GitOps 等现代运维场景；
- 场景以 “一次性任务编排” 或 “轻量级配置管理” 为主。

**选 Puppet**：

- 企业级大规模基础设施（如十万级服务器），需长期稳定的状态管理；
- 强调 “自动化修复”（如配置漂移后自动恢复）。

**选 Chef**：

- 团队以开发人员为主，熟悉 Ruby 语言；
- 场景需高度定制化逻辑（如复杂的应用部署流程）。

**选 SaltStack**：

- 需实时监控目标节点状态，或超大规模节点（如云计算数据中心）；
- 追求极致并发性能（如秒级操作上万节点）。

**选 Fabric**：

- 仅需执行简单批量命令（如日志收集、临时脚本）；
- 团队缺乏自动化工具经验，需快速落地小任务。

### 2.2 Fabric

[返回目录](#课程目录)

参考：[Github](http://github.com/99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#fabric-quick-start--catalog-)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#fabric-quick-start--catalog-)

- 作业：SSH 免密登录配置
- 作业：Fabric 基本操作

### 2.3 Ansible 基础

[返回目录](#课程目录)

Ansible 的独特优势​：

1. 无代理架构：减少目标节点资源占用，避免 “客户端故障影响整体” 的风险；​
2. 语法友好：YAML 格式接近自然语言，运维、开发、产品均可参与编写；​
3. 生态灵活性：与容器（Docker/K8s）、云平台（AWS/Azure）、GitOps（GitLab CI）无缝集成，适配现代运维趋势；​
4. 模块丰富：内置数千模块（涵盖系统、网络、数据库等），且支持 Python 自定义模块，扩展成本低。​

综上，Ansible 凭借 “简单、灵活、易集成” 的特点，成为当前自动化运维的主流选择，尤其适合中小团队快速落地自动化流程。

Ansible 原理：

![](images/ansible-architecture.png)

#### 2.3.1 关于 Ansible 你需要知道的二三事

Ansible
案例，参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#ansible-as-a-plus--catalog-)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#ansible-as-a-plus--catalog-)

Ansible = Ansible Core + Ansible 组件库

版本选择：[Ansible 发行和维护](https://docs.ansible.org.cn/ansible/latest/reference_appendices/release_and_maintenance.html)

#### 2.3.2 Ansible 安装

对 Ubuntu 22.04

```bash
apt update -y
apt install ansible
ansible --version
```

可以看到：

```console
ansible 2.10.8
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3/dist-packages/ansible
  executable location = /usr/bin/ansible
  python version = 3.10.12 (main, May 27 2025, 17:12:29) [GCC 11.4.0]
```

如果要指定版本，可以用 pip 安装

```console
# pip3 install virtualenv

# python3 -m virtualenv .venv
created virtual environment CPython3.10.12.final.0-64 in 1299ms
  creator CPython3Posix(dest=/root/.venv, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, via=copy, app_data_dir=/root/.local/share/virtualenv)
    added seed packages: pip==25.1.1, setuptools==80.9.0
  activators BashActivator,CShellActivator,FishActivator,NushellActivator,PowerShellActivator,PythonActivator

# . .venv/bin/activate

(.venv) ~# which python
/root/.venv/bin/python

(.venv) ~# which pip
/root/.venv/bin/pip

(.venv) ~# pip install "ansible==2.10.7" -i https://mirrors.aliyun.com/pypi/simple/
```

#### 2.3.2 配置 SSH

生成 SSH key

```console
root@devopslab020:~/.ssh# ls
authorized_keys  known_hosts

root@devopslab020:~/.ssh# ssh-keygen 
Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /root/.ssh/id_rsa.
Your public key has been saved in /root/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:41njTMl+VNsh/gjSojuolLSGiKXA2lQPU/Ds6co3YFg root@devopslab020
The key's randomart image is:
+---[RSA 2048]----+
|    ...          |
|     +           |
|    + o      ... |
|.  .E= . ......o.|
|..o+  + So*o... .|
|==+ =. ..Ooo. o  |
|=..* .o.o + .. . |
|  o. oo..  .     |
|   .+. o.        |
+----[SHA256]-----+

root@devopslab020:~/.ssh# ls
authorized_keys  id_rsa  id_rsa.pub  known_hosts
```

注意：

1. public key -> server side authorized_keys
2. private key -> client side
3. [Generator for PuTTY on Windows](https://www.ssh.com/ssh/putty/windows/puttygen)

把 public key 写入服务端的 ~/.ssh/authorized_keys，确保 ssh 能够免密登陆

服务端的 SSH 配置

```console
# cat /etc/ssh/sshd_config | tail -n 5

UseDNS no
ClientAliveInterval 120
ClientAliveCountMax 720
GSSAPIAuthentication no

# systemctl restart ssh
```

客户端 SSH 配置

```conf
# cat ~/.ssh/config 
Host *
    KexAlgorithms +diffie-hellman-group1-sha1
    HostKeyAlgorithms +ssh-rsa,ssh-dss
    PubkeyAcceptedKeyTypes +ssh-rsa,ssh-dss
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null

Host test1
    HostName        localhost
    User            root

Host test2
    HostName        localhost
    User            root
```

补充：SSH Proxy

```
ProxyCommand    ssh fq -W %h:%p
ProxyCommand    bash -c 'h=%h;ssh bastion -W ${h##prefix-}:%p'
```

#### 2.3.3 Hello, Ansible

配置 hosts.ini

```ini
# cat hosts.ini 
[webservers]
test1
test2
```

ping 这一组 webservers 服务器

```bash
ansible webservers -m ping -i hosts.ini
```

输出：

```console
# ansible webservers -m ping -i hosts.ini

test1 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
test2 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
```

最佳实践：

1. hosts.ini 还可以配置 ssh 相关的参数，但尽量不要，让 ssh 配置都放在 ~/.ssh/config 里，配置免密登陆后，ansible 会自动使用 ssh 登陆
2. 可以在 hosts.ini 里配置 ansible 相关的参数，如 ansible_python_interpreter 等，但尽量不要，越简单越好，尽量和 python 版本无关。
3. ping 是 ansible 内置的动作，用来测试连接是否正常，也可以用来测试 ansible 配置是否正确。大部分内置命令是幂等的，但也有些不是，比如 shell。
4. 这里直接运行 ansible，但实际更常用的是 ansible-playbook，把要执行的命令放在 playbook 里，playbook 是 ansible 的剧本文件，用 YAML
   格式编写。

#### 2.3.4 YAML

[YAML 基本语法](https://docs.ansible.com/ansible/2.9/reference_appendices/YAMLSyntax.html)

- YAML 是数据结构，包含字符串、数字、布尔、列表、字典五种类型
- YAML 和 JSON 可以对应互相转化

其它 YAML 的快速入门，参考：

- [w3cnote YAML 介绍](https://www.runoob.com/w3cnote/yaml-intro.html)
- [redhat what's YAML](https://www.redhat.com/en/topics/automation/what-is-yaml)

#### 2.3.5 Ansible 快速参考

**Ansible 核心命令**

| 命令                  | 功能描述                                                                 | 示例                                                                                            |
| ------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `ansible`           | 执行临时命令，快速在远程主机上执行单一任务（如 ping、shell 命令）。                              | `ansible webservers -m pingansible dbservers -a "df -h"`                                      |
| `ansible-playbook`  | 执行 Playbook 文件，批量执行预定义的任务序列。                                         | `ansible-playbook deploy.yml -i hosts.ini`                                                    |
| `ansible-galaxy`    | 管理 Ansible 角色和集合，可从 [Galaxy](https://galaxy.ansible.com/) 下载或上传共享内容。 | `ansible-galaxy install geerlingguy.nginxansible-galaxy collection install community.general` |
| `ansible-doc`       | 查看模块文档和用法示例。                                                         | `ansible-doc fileansible-doc -s copy`（仅显示参数摘要）                                                |
| `ansible-vault`     | 加密 / 解密敏感数据（如密码、密钥），保护 Playbook 中的机密信息。                              | `ansible-vault encrypt group_vars/production/secrets.ymlansible-vault view secrets.yml`       |
| `ansible-inventory` | 查看或调试主机清单（inventory）的结构和变量。                                          | `ansible-inventory --list -i hosts.iniansible-inventory --graph`                              |

**常用模块（非完整列表）**

| 模块名               | 功能描述                                              | 适用场景                                                                                            |
| ----------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `ping`            | 测试与目标主机的连通性（基于 Python），验证 SSH 配置和 Python 环境。      | 检查主机是否可达：`ansible all -m ping`                                                                  |
| `shell`/`command` | 在远程主机执行 shell 命令（`shell` 支持管道和变量，`command` 直接执行）。 | 执行系统命令：`ansible web -m shell -a "ls -l /tmp"`                                                   |
| `copy`            | 将文件从控制节点复制到远程主机，支持权限和内容替换。                        | 分发配置文件：`ansible web -m copy -a "src=nginx.conf dest=/etc/nginx/"`                               |
| `file`            | 管理文件 / 目录属性（权限、所有者、状态等）。                          | 创建目录：`ansible all -m file -a "path=/data state=directory mode=0755"`                            |
| `template`        | 基于 Jinja2 模板生成配置文件，动态填充变量。                        | 生成个性化配置：`ansible web -m template -a "src=app.conf.j2 dest=/etc/app.conf"`                       |
| `yum`/`apt`       | 包管理模块，用于安装、升级或删除软件包（分别适用于 RHEL 和 Debian 系）。       | 安装 Nginx：`ansible web -m yum -a "name=nginx state=present"`                                     |
| `service`         | 管理系统服务（启动、停止、重启、设置开机自启）。                          | 重启服务：`ansible all -m service -a "name=httpd state=restarted enabled=yes"`                       |
| `user`/`group`    | 创建或管理用户和用户组。                                      | 创建 deploy 用户：`ansible all -m user -a "name=deploy groups=sudo append=yes"`                      |
| `git`             | 从 Git 仓库克隆或更新代码。                                  | 部署应用：`ansible app -m git -a "repo=https://github.com/example.git dest=/opt/app version=master"` |
| `uri`             | 发送 HTTP 请求，用于 API 调用或检查服务状态。                      | 检查网站状态：`ansible localhost -m uri -a "url=http://example.com return_content=yes"`                |
| `debug`           | 调试模块，打印变量值或临时信息。                                  | 输出变量：`ansible all -m debug -a "var=ansible_facts"`                                              |

**其他实用命令**

| 命令                | 功能描述                                     |
| ----------------- | ---------------------------------------- |
| `ansible-config`  | 查看或配置 Ansible 的运行参数（如并发数、SSH 超时）。        |
| `ansible-console` | 交互式执行命令，类似 shell 终端，但针对多主机批量操作。          |
| `ansible-pull`    | 在远程主机上直接拉取并执行 Playbook（反向操作，适用于无中心节点场景）。 |

**如何查找更多模块？**

**官方文档**：[Ansible Modules 文档](https://docs.ansible.com/ansible/latest/collections/index.html)

**命令行查询**：

```
ansible-doc -l  # 列出所有可用模块
ansible-doc <模块名>  # 查看特定模块的详细文档
```

建议结合具体场景选择合适的模块，并通过 `ansible-doc` 深入了解参数用法。

#### 2.3.6 动态 inventory

创建文件 dynamic_host.py

```python
#!/usr/bin/env python3
import json

# 模拟从CMDB获取的主机数据
def get_hosts_data():
    return {
        "webservers": {
            "hosts": ["test1", "test2"],
            "vars": {
                "http_port": 80,
                "env": "production"
            }
        },
        "dbservers": {
            "hosts": ["test2"],
            "vars": {
                "db_port": 5432,
                "engine": "postgresql"
            }
        },
    }

if __name__ == "__main__":
    print(json.dumps(get_hosts_data()))

# import json
# import requests

# class CMDBInventory:
#     def __init__(self):
#         self.api_url = "https://cmdb.example.com/api/servers"
#         self.token = "your_api_token"
#         self.inventory = {"_meta": {"hostvars": {}}}
        
#     def get_cmdb_data(self):
#         headers = {"Authorization": f"Bearer {self.token}"}
#         response = requests.get(self.api_url, headers=headers)
#         return response.json()
        
#     def parse_data(self, cmdb_data):
#         # 将CMDB数据转换为Ansible Inventory格式
#         for server in cmdb_data.get("servers", []):
#             hostname = server["hostname"]
#             groups = server["groups"]
            
#             # 添加到组
#             for group in groups:
#                 if group not in self.inventory:
#                     self.inventory[group] = {"hosts": []}
#                 self.inventory[group]["hosts"].append(hostname)
                
#             # 添加主机变量
#             self.inventory["_meta"]["hostvars"][hostname] = {
#                 "ansible_host": server["ip_address"],
#                 "os_family": server["os_family"],
#                 "env": server["environment"]
#             }
            
#     def run(self):
#         cmdb_data = self.get_cmdb_data()
#         self.parse_data(cmdb_data)
#         print(json.dumps(self.inventory, indent=2))

# if __name__ == "__main__":
#     CMDBInventory().run()
```

验证动态清单输出

```bash
# 加执行权限

chmod +x dynamic_host.py

# 执行脚本查看JSON输出
./dynamic_inventory.py --list

# 查看特定主机信息（需实现--host参数）
./dynamic_inventory.py --host web1.example.com
```

使用动态清单

```bash
# 使用动态清单脚本执行命令（需赋予执行权限）
ansible all -m ping -i ./dynamic_host.py
```

#### 2.3.7 版本兼容性

```yaml
# playbook.yml
- name: 安装Apache
  hosts: all
  tasks:
    - name: 在RHEL 7及以下使用yum
      yum:
        name: httpd
        state: present
      when: ansible_distribution_major_version|int <= 7
    
    - name: 在RHEL 8及以上使用dnf
      dnf:
        name: httpd
        state: present
      when: ansible_distribution_major_version|int >= 8
```

执行：

```bash
# 在Ansible 2.9下执行（yum模块为主）
ansible-playbook playbook.yml -i hosts.ini

# 在Ansible 2.16下执行（支持dnf模块）
ansible-playbook playbook.yml -i hosts.ini
```

类似的还有，ec2 模块变成 aws_ec2_instance 模块

```yaml
# compatible_playbook.yml
- name: 启动EC2实例
  hosts: localhost
  tasks:
    - name: 启动EC2（旧版）
      ec2:
        instance_type: t2.micro
        image: ami-123456
        region: us-east-1
        state: present
      when: ansible_version.full is version('2.10', '<')
    
    - name: 启动EC2（新版）
      aws_ec2_instance:
        instance_type: t2.micro
        image_id: ami-123456
        region: us-east-1
        state: running
      when: ansible_version.full is version('2.10', '>=')
```

#### 2.3.8 Playbook 语法基础

打印变量类型 & 长行字符串

```yaml
# quotes_demo.yml
- name: YAML引号测试
  hosts: localhost
  gather_facts: no
  vars:
    bool_1: yes       # 布尔值True
    bool_2: "yes"     # 字符串"yes"
    bool_3: 'yes'     # 字符串'yes'
    bool_4: "True"    # 字符串"True"
    bool_5: True      # 布尔值True
  tasks:
    - name: 打印变量类型和值
      debug:
        msg: |
          bool_1: {{ bool_1 }} (类型: {{ bool_1 | type_debug }})
          bool_2: {{ bool_2 }} (类型: {{ bool_2 | type_debug }})
          bool_3: {{ bool_3 }} (类型: {{ bool_3 | type_debug }})
          bool_4: {{ bool_4 }} (类型: {{ bool_4 | type_debug }})
          bool_5: {{ bool_5 }} (类型: {{ bool_5 | type_debug }})
```

```bash
ansible-playbook quotes_demo.yml

# 如果 hosts 用 inventory.ini 配置，需要指定 -i 参数
# ansible-playbook quotes_demo.yml -i inventory.ini
```

特殊字符串 & 遍历

```yaml
# special_chars.yml
- name: 特殊字符测试
  hosts: localhost
  gather_facts: no
  vars:
    path1: /data/logs   # 无需引号
    path2: /data/logs/  # 无需引号
    regex: '^[0-9]+$'   # 必须使用引号，避免YAML解析错误
    host: "server:port" # 包含冒号时需要引号
  tasks:
    - name: 打印变量
      debug:
        var: "{{ item }}"
      loop:
        - path1
        - path2
        - regex
        - host
```

任务的执行顺序：pre_tasks、tasks、post_tasks

```yaml
# task_order.yml
- name: 任务执行顺序测试
  hosts: localhost
  gather_facts: yes
  
  pre_tasks:
    - name: 前置任务1
      debug:
        msg: "这是pre_tasks中的第一个任务"
    
    - name: 前置任务2
      debug:
        msg: "这是pre_tasks中的第二个任务"
  
  tasks:
    - name: 主任务1
      debug:
        msg: "这是主tasks中的第一个任务"
    
    - name: 主任务2
      debug:
        msg: "这是主tasks中的第二个任务"
  
  post_tasks:
    - name: 后置任务1
      debug:
        msg: "这是post_tasks中的第一个任务"
    
    - name: 后置任务2
      debug:
        msg: "这是post_tasks中的第二个任务"
```

错误处理

```yaml
# error_handling.yml
- name: 异常处理测试
  hosts: localhost
  gather_facts: no
  
  pre_tasks:
    - name: 前置任务
      debug:
        msg: "执行前置任务"
  
  tasks:
    - name: 触发错误
      command: /bin/false
      ignore_errors: true
    
    - name: 继续执行
      debug:
        msg: "错误被忽略，继续执行"
  
  post_tasks:
    - name: 后置任务
      debug:
        msg: "执行后置任务（无论是否出错）"
```

调试复杂的的嵌套 YAML 结构

```yaml
# nested_structure.yml
- name: 嵌套结构测试
  hosts: localhost
  gather_facts: no
  vars:
    # 多级字典嵌套
    users:
      admin:
        name: "系统管理员"
        groups:
          - sudo
          - wheel
        permissions:
          files:
            - /etc/hosts
            - /etc/sudoers
          commands:
            - /bin/systemctl
      developer:
        name: "开发人员"
        groups:
          - dev
          - docker
        permissions:
          files:
            - /var/www/html
          commands:
            - /usr/bin/git
            - /usr/bin/docker
  
  tasks:
    - name: 打印嵌套结构
      debug:
        var: users
    
    - name: 遍历用户和权限
      debug:
        msg: "用户 {{ item.key }} 属于组 {{ item.value.groups }}"
      loop: "{{ users.items() }}"
```

yaml-lint 工具

```bash
# 安装yaml-lint
pip install yamllint

# 检查YAML文件格式
yamllint nested_structure.yml
```

Ansible 内置调试方法

```yaml
# debug_nested.yml
- name: 嵌套结构调试
  hosts: localhost
  gather_facts: no
  vars:
    config:
      servers:
        - name: web1
          ip: 192.168.1.10
          ports:
            - 80
            - 443
        - name: db1
          ip: 192.168.1.20
          ports:
            - 5432
  
  tasks:
    - name: 调试输出
      debug:
        var: config.servers[0].ports[0]
    
    - name: 使用to_nice_yaml过滤器
      debug:
        msg: "{{ config | to_nice_yaml }}"
```

条件执行

```yaml
# conditional_tasks.yml
- name: 条件执行测试
  hosts: localhost
  gather_facts: yes
  vars:
    deploy_env: "production"
    web_server: "nginx"
  
  tasks:
    - name: 在生产环境安装安全补丁
      yum:
        name: security-updates
        state: latest
      when: deploy_env == "production"
    
    - name: 安装Nginx
      yum:
        name: nginx
        state: present
      when: web_server == "nginx"
    
    - name: 安装Apache
      yum:
        name: httpd
        state: present
      when: web_server == "apache"
```

基于系统信息的条件执行

```yaml
# os_specific.yml
- name: 跨平台任务
  hosts: all
  gather_facts: yes
  
  tasks:
    - name: 在Debian系系统安装Python3
      apt:
        name: python3
        state: present
      when: ansible_os_family == "Debian"
    
    - name: 在RedHat系系统安装Python3
      yum:
        name: python3
        state: present
      when: ansible_os_family == "RedHat"
    
    - name: 在Windows系统启用远程桌面
      win_regedit:
        path: HKLM:\System\CurrentControlSet\Control\Terminal Server
        name: fDenyTSConnections
        data: 0
        type: dword
      when: ansible_os_family == "Windows"
```

复杂条件组合，when 列表是 and 关系

```yaml
# complex_conditions.yml
- name: 复杂条件测试
  hosts: all
  gather_facts: yes
  vars:
    min_ram: 2048  # MB
    required_disk: 10  # GB
  
  tasks:
    - name: 检查内存和磁盘空间
      debug:
        msg: "系统资源满足要求"
      when: 
        - ansible_memtotal_mb >= min_ram
        - ansible_mounts[0].size_available / 1024 / 1024 >= required_disk
        - (ansible_distribution == "CentOS" and ansible_distribution_major_version|int >= 7)
          or ansible_distribution == "Ubuntu"
```

#### 2.3.9 Playbook 高级编写技巧

变量优先级层级和覆盖顺序

```text
1. 命令行参数 (-e, --extra-vars)
2. 环境变量 (ANSIBLE_VAR_NAME)
3. playbook文件中定义的vars_prompt
4. playbook文件中定义的vars
5. 任务中定义的vars
6. include_vars模块引入的变量
7. 角色中的vars/main.yml
8. 块(Block)中定义的vars
9. 主机清单中定义的变量
10. 主机清单中组变量
11. 主机清单中继承的组变量
12. playbook文件中定义的vars_files
13. 角色中的defaults/main.yml
14. 命令行指定的-vault-password-file或--ask-vault-pass
15. 事实收集(facts)
16. 注册变量(registered variables)
17. 魔法变量(magic variables)
18. 内置变量(如ansible_version)
19. 角色依赖中的变量
20. 插件返回的变量
21. 缓存的事实(cached facts)
22. 清单组的组变量文件
23. 主机的主机变量文件
24. 全局配置文件中的变量
```

第 24 级，全局配置文件的加载顺序：

1. 环境变量 `ANSIBLE_CONFIG` 指定的路径（例如 `export ANSIBLE_CONFIG=/etc/ansible/my_ansible.cfg`）
2. 当前目录下的 ansible.cfg
3. 用户主目录下的 ~/.ansible.cfg
4. 系统级默认配置：/etc/ansible/ansible.cfg

加载顺序：Ansible 会按上述顺序查找配置文件，找到第一个存在的文件后停止搜索。例如，如果 ANSIBLE_CONFIG 环境变量已设置，则优先使用该路径的配置文件。

查看当前 ansible 执行对应的全局配置文件：

```console
$ ansible --version
ansible 2.10.17
  config file = None
  configured module search path = ['/Users/wuwenxiang/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /Users/wuwenxiang/local/github-mine/demotheworld/.venv/lib/python3.10/site-packages/ansible
  executable location = /Users/wuwenxiang/local/github-mine/demotheworld/.venv/bin/ansible
  python version = 3.10.17 (main, Apr  8 2025, 12:10:59) [Clang 17.0.0 (clang-1700.0.13.3)]
```

最佳实践：

1. 系统级配置：在 /etc/ansible/ansible.cfg 中设置全局默认值。
2. 项目级配置：在项目根目录创建 ansible.cfg，覆盖系统默认配置。
3. 变量优先级：尽量使用角色 defaults（低优先级）定义通用默认值，通过 extra_vars 或 host_vars（高优先级）覆盖特定场景的值。

举例说明：

```yaml
# variable_priority.yml
- name: 变量优先级测试
  hosts: localhost
  gather_facts: no
  vars:
    # 优先级9: playbook vars
    test_var: "playbook_vars"
  vars_files:
    - vars/defaults.yml  # 优先级8: vars_files
  vars_prompt:
    - name: test_var
      prompt: "请输入变量值"  # 优先级12: vars_prompt
      private: no
  
  tasks:
    - name: 打印变量值
      debug:
        var: test_var
    
    - name: 命令行变量覆盖测试
      debug:
        msg: "命令行变量优先级最高: {{ test_var }}"
      when: test_var == "extra_vars"
```

测试不同来源的变量：

```bash
# 1. 执行默认情况（vars_files优先级低于playbook vars）
ansible-playbook variable_priority.yml

# 2. 使用命令行变量（extra_vars，优先级最高）
ansible-playbook variable_priority.yml -e "test_var=extra_vars"

# 3. 交互式输入变量（vars_prompt，优先级中等）
ansible-playbook variable_priority.yml --skip-tags=extra
```

角色依赖管理和角色的递归加载

```text
roles/
├── webserver/
│   ├── tasks/
│   │   └── main.yml
│   └── meta/
│       └── main.yml  # 定义依赖
└── common/
    └── tasks/
        └── main.yml
```

#### 2.3.10 自定义模块开发实战

#### 2.3.11 AI 辅助 Ansible 模块生成

### 2.4 Ansible 和容器技术

[返回目录](#课程目录)

#### 2.4.1 Ansible 的 docker 组件

[返回目录](#课程目录)

参考：[Community.Docker](https://docs.ansible.com/ansible/latest/collections/community/docker)

- 作业：安装 Ansible Docker 模块

部署 Django 应用，参考：[Github](https://github.com/duicikeyihangaolou/ZZLARGE-Project-DjangoTest) 或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-django/)

- 作业：通过 Docker 部署容器应用

#### 2.4.2 把 Ansible 装进容器里

[返回目录](#课程目录)

Dockerfile

```dockerfile
FROM python:bullseye

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ansible==2.9.27
```

```bash
docker build --tag ansible:2.9.27 .
```

```console
$ docker run -it ansible:2.9.27 ansible --version
ansible 2.9.27
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/local/lib/python3.10/site-packages/ansible
  executable location = /usr/local/bin/ansible
  python version = 3.10.1 (main, Dec 21 2021, 09:01:08) [GCC 10.2.1 20210110]

$ docker run -it -v "/root/.ssh":"/root/.ssh" -uroot -v "$(pwd)"/lab-django:/app ansible:2.9.27 ansible-playbook -i /app/ansible-u1804/inventory/inventory.ini /app/ansible-u1804/playbooks/deploy.yml
```

- 作业：将 Ansible 装进容器

将 ansible 运行在容器中的参考案例：

- [kubeasz](https://github.com/easzlab/kubeasz)
- [ks-installer](https://github.com/easzlab/kubeasz/blob/master/docs/guide/kubesphere.md)

### 2.5 Ansible 与云平台

[返回目录](#课程目录)

Ansible 的云组件

- [libvirt](https://docs.ansible.com/ansible/latest/collections/community/libvirt/index.html)
- [vmware](https://docs.ansible.com/ansible/latest/collections/community/vmware/index.html)
- [kubernetes](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/index.html#plugins-in-kubernetes-core)
- [OpenStack](https://docs.ansible.com/ansible/latest/collections/openstack/cloud/index.html#plugins-in-openstack-cloud)
  - [openstack-ansible 用户手册](https://docs.openstack.org/openstack-ansible/latest/user/test/example.html)
  - [Kolla-Ansible](https://github.com/openstack/kolla-ansible)
  - 操作案例：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#lab-03-openstack-ansible-provider--catalog-)
    或
    [Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-02-OpenStack-API-and-Development.md#lab-03-openstack-ansible-provider--catalog-)

**补充**：YAML 应用广泛，除了 K8S、Ansible 用到之外，OpenStack Heat、OpenAPI，包括
[Restful API 自动化测试](autotest.md#471-gabbi)也会用到。

## 3. 任务管理

[返回目录](#课程目录)

### 3.1 版本控制

[返回目录](#课程目录)

Git 参考：[版本控制](we-know-python.md#31-版本控制)

### 3.2 Jenkins+Zuul

[返回目录](#课程目录)

OpenStack
质量保证体系，参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#112-openstack-%E5%A6%82%E4%BD%95%E4%BF%9D%E8%AF%81%E4%BB%A3%E7%A0%81%E8%B4%A8%E9%87%8F)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#112-openstack-%E5%A6%82%E4%BD%95%E4%BF%9D%E8%AF%81%E4%BB%A3%E7%A0%81%E8%B4%A8%E9%87%8F)

### 3.3 Drone

[返回目录](#课程目录)

Gitlab +
Drone，参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/cicd/gitlab_drone.md) 或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/cicd/gitlab_drone.md)

### 3.4 CI/CD

[返回目录](#课程目录)

OIDC + Gitlab + Gerrit + Redmine +
Drone，参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/cicd/cicd-install-guide.md)
或 [Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/cicd/cicd-install-guide.md)

### 3.5 K8S Cronjob

[返回目录](#课程目录)

配置默认 StorageClass，参考：[Github] 或
[Gitee](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/main/doc/kubernetes-best-practices.md#45-local-%E5%92%8C%E5%8A%A8%E6%80%81%E5%88%86%E9%85%8D)

参考：[KubeSphere 部署官网](https://kubesphere.io/docs/v3.3/quick-start/minimal-kubesphere-on-k8s/)

参考：[Cronjob](https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/cron-jobs/)

## 4. 监控计量

[返回目录](#课程目录)

### 4.1 监控框架对比

[返回目录](#课程目录)

监控是为了解决什么问题？

- **长期趋势分析**：通过对监控样本数据的持续收集和统计，对监控指标进行长期趋势分析。例如，通过对磁盘空间增长率的判断，我们可以提前预测在未来什么时间节点上需要对资源进行扩容。
- **对照分析**：两个版本的系统运行资源使用情况的差异如何？在不同容量情况下系统的并发和负载变化如何？通过监控能够方便的对系统进行跟踪和比较。
- **告警**：当系统出现或者即将出现故障时，监控系统需要迅速反应并通知管理员，从而能够对问题进行快速的处理或者提前预防问题的发生，避免出现对业务的影响。
- **故障分析与定位**：当问题发生后，需要对问题进行调查和处理。通过对不同监控监控以及历史数据的分析，能够找到并解决根源问题。
- **数据可视化**：通过可视化仪表盘能够直接获取系统的运行状态、资源使用情况、以及服务运行状态等直观的信息。

白盒监控

- 了解系统内部的实际运行状态
- 通过对监控指标的观察能够预判可能出现的问题
- 从而对潜在的不确定因素进行优化

黑盒监控

- 常见的如 HTTP 探针，TCP 探针等
- 可以在系统或者服务在发生故障时能够快速通知相关的人员进行处理

参考：[K8S 探针](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

### 4.2 Promtheus

[返回目录](#课程目录)

参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#4-%E7%9B%91%E6%8E%A7%E5%92%8C%E5%91%8A%E8%AD%A6)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#4-%E7%9B%91%E6%8E%A7%E5%92%8C%E5%91%8A%E8%AD%A6)

### 4.3 Alertmanager

[返回目录](#课程目录)

### 4.4 Grafana

[返回目录](#课程目录)

## 5. 日志分析

[返回目录](#课程目录)

### 5.1 Fluentd

[返回目录](#课程目录)

### 5.2 ElasticSearch

[返回目录](#课程目录)

参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#8-elastic-search)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-03-OpenStack-Maintenance.md#8-elastic-search)

### 5.3 Kibana

[返回目录](#课程目录)

### 5.4 其它的日志收集和分析方案

[返回目录](#课程目录)

[Grafana Loki 官方文档](https://grafana.com/oss/loki/)

也可以参考：[Grafana Loki 初探](https://zhuanlan.zhihu.com/p/403113044)

## 6. 问题排查案例

[返回目录](#课程目录)

### 6.1 OpenStack 日志分析

[返回目录](#课程目录)

Cinder
服务报错排查，参考：[Github](https://github.com/99cloud/lab-openstack/blob/master/doc/class-01-OpenStack-Administration.md#94-debug-cinder)
或
[Gitee](https://gitee.com/dev-99cloud/lab-openstack/blob/master/doc/class-01-OpenStack-Administration.md#94-debug-cinder)

### 6.2 Python2 处理中文问题

[返回目录](#课程目录)

参考：[老版本 OpenStack 中 Python2 中文处理问题](http://blog.wuwenxiang.net/OpenStack-Debug)

### 6.3 MTU 问题

[返回目录](#课程目录)

参考：[K8S 应用故障调试](http://blog.wuwenxiang.net/k8s-app-debug)
