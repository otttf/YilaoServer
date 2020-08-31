# YilaoServer 
逸劳App服务端

# Restful Api Design

我们很清楚，逸劳想要成为一款好的web应用，那么对于当下主流的开发架构我们就必须要有很好的了解。为此，我们开始在网上查阅相关资料，对各种架构进行比较，筛选。最后，我们决定采取前后端分离的形式，[rest](https://baike.baidu.com/item/RESTful)作为前后端分离技术的一种，是一个非常出色的架构。restful api的实现，有助于我们之后扩展更多的平台。

## 第一版

* 设计

    1. 在选择开发语言上，我们基于一些考虑，选择了python。第一，python易于学习，内置了大量的库，对于开发非常便利，相较于其他语言，python的代码也要少很多。第二，python是我们刚开始学习的语言，开发一个项目，这对于我们的理解将会能够很好的提升。
    2. python有一些主流的部署方案，我们选择了nginx+gunicorn+flask。
    3. 使用sql脚本，并且自己实现其自动化执行
    4. 自己实现dao、管理连接池
    
* 资料

    [Web API design](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design)
    
    [Flask Document](https://flask.palletsprojects.com/en/1.1.x/)
    
    [Alibaba Short Message Service](https://api.aliyun.com/new#/?product=Dysmsapi&version=2017-05-25&api=SendSms&params={}&tab=DEMO&lang=PYTHON)
    
    [Sqlite 教程](https://www.runoob.com/sqlite/sqlite-tutorial.html)
    
    [Python Sqlite Document](https://docs.python.org/zh-cn/3/library/sqlite3.html)
    
* 依赖

    |         服务搭建         |      描述       | 使用 |
    | :----------------------: | :-------------: | :--: |
    | ubuntu 18.04 1核1G 1Mbps |   服务器环境    |  √   |
    |        python3.8         | web应用开发平台 |  √   |
    |          nginx           |    web服务器    |  *   |
    |          https           | web应用安全保证 |  *   |
    |         gunicorn         |   wsgi服务器    |  *   |
    
    |           开发依赖            |       描述       | 使用 |
    | :---------------------------: | :--------------: | :--: |
    | Alibaba Short Message Service | 阿里巴巴短信服务 |  √   |
    |             flask             |   web应用框架    |  √   |
    |            sqlite             | python内嵌数据库 |  √   |

* 进度
  
    1. 实现短信注册
    2. 实现部分dao
  
* 弊端
  
    1. dao、字段检验代码重复度高，对于后续开发维护非常不利
    2. 自己实现连接池极有可能出现意料之外的问题
## 第二版

在尝试第一版的设计方案中，我们深刻体会到了自己造轮子的困难之处。其实，网上已经有了一些成熟的方案了。

* 改进

    1. sql语句可以使用orm框架来代替，orm即对象-关系映射，可以将数据库的表和python中的类对应起来，在对比了当下热门的python orm框架后，我们选择了sqlalchemy，sqlalchemy可以自动生成sql语句，并且可以轻易的切换数据库，深受好评。
    2. 数据库升级可以使用alembic——一个sqlalchemy作者开发的库，网上另一个方案是使用flask_migrate。
    3. 字段检验我们找到了marshmallow库，这个库可以非常简单的对json数据进行检验。
    4. 在用户登录检验方面，我们也查阅了许多资料，如basic、digest，在这个过程中，我们意识到不能将用户密码以明文方式储存在数据库，因此再次去查阅了有关的解决方案。md5和sha哈希是当下比较好的措施，md5现在已经不足够安全，因此我们选择了sha256算法。

* 资料

    [sqlalchemy docs](https://docs.sqlalchemy.org/en/13/)

    [marshmallow docs](https://marshmallow.readthedocs.io/en/stable/)

    [http认证方式](https://www.jianshu.com/p/51f4cfe0171d)

    [密码安全](https://zhuanlan.zhihu.com/p/20407064)

* 依赖

    |         服务搭建         |      描述       | 使用 |
    | :----------------------: | :-------------: | :--: |
    | ubuntu 18.04 1核1G 1Mbps |   服务器环境    |  √   |
    |        python3.8         | web应用开发平台 |  √   |
    |          nginx           |    web服务器    |  *   |
    |          https           | web应用安全保证 |  *   |
    |         gunicorn         |   wsgi服务器    |  *   |
    
    |           开发依赖            |        描述         | 使用 |
    | :---------------------------: | :-----------------: | :--: |
    | Alibaba Short Message Service |  阿里巴巴短信服务   |  √   |
    |         flask_restful         | web restful api框架 |  √   |
    |          sqlalchemy           |         orm         |  √   |
    |            alembic            |   数据库版本控制    |  *   |
    |          marshmallow          | 类型转换、字段检验  |  √   |
    |            sha256             |      密码哈希       |  √   |
    |            sqlite             |  python内嵌数据库   |  √   |

* 进度
  
    1. 短信注册
    2. 更安全的存储密码
    3. orm映射
    4. 字段检验
  
* 弊端
  
    1. 我们需要提供的服务其实不算很大，sqlalchemy虽然实现了对象和关系之间的映射，但是在开发过程中我们并没有体验到多少orm带来的好处，引入orm随之而来的是新的知识的学习，并且我们需要用这些新学习的知识来代替熟悉的sql语句，并且我们没法实时的掌握它生成的sql语句，非常的吃力不讨好，加之一些查询也要用上原生的sql语句，在这个小型的项目中orm失去了它的优势。
    2. sqlite是python自带的数据库，虽然小巧，但功能也相对没有那么完善，其对于变量类型的约束也没有，很多地方需要我们人为的去判断。实际上，sqlite也是安卓内嵌的数据，为什么当我们在服务器使用sqlite时会出现问题呢。我们考虑分析后，得出如下结论：作为服务器，对外提供了开放的api，那么我们就要考虑到各种错误，因为我们不能保证与我们通信的一定是我们本身开发的客户端，这其中也包括了类型、范围等数据方面的错误，而安卓端作为获取服务器数据的一方，其获取到的数据必定是合法的，因此其对数据的约束并不需要那么高的要求，sqlite确实能作为它的一个非常不错的选择。所以，当初我们对于数据库的选择，有很多东西都尚未考虑。

## 第三版
* 改进

  1. 作为sqlite的代替，我们选择了web应用开发最好的数据库之一mysql，mysql除了能够加强数据库的安全性外，还有储存过程、函数等特性，最重要的是，它本身具有处理几何、地理的能力，能对二维的点进行索引，这恰好是我们应用最核心部分需要用到的功能。
  2. 考虑加入了token，让服务器即时生成一个有期限的口令返回给客户端，我们取消了密码这个概念，将其改为了永久token。并且我们在服务器中增添了活跃用户，利用时间局部性，大幅度减少了检查token的数据库查询。

* 资料

    [mysql 教程](https://www.runoob.com/mysql/mysql-tutorial.html)

    [mysql 储存过程](https://www.runoob.com/w3cnote/mysql-stored-procedure.html)

    [使用MySQL的geometry类型处理经纬度距离问题](https://segmentfault.com/a/1190000018072395)

    [mysql中geometry类型的简单使用](https://blog.csdn.net/MinjerZhang/article/details/78137795?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.edu_weight&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromMachineLearnPai2-1.edu_weight)

    [MySQL索引类型详解](http://c.biancheng.net/view/7897.html)

    [空间索引Spatial Indexing](https://zhuanlan.zhihu.com/p/38597148)

    [从B树、B+树、B*树谈到R 树](https://blog.csdn.net/v_JULY_v/article/details/6530142)

    [深入浅出空间索引：为什么需要空间索引](https://www.cnblogs.com/LBSer/p/3392491.html)

* 依赖

    |         服务搭建         |      描述       | 使用 |
    | :----------------------: | :-------------: | :--: |
    | ubuntu 20.04 1核1G 1Mbps |   服务器环境    |  √   |
    |        python3.8         | web应用开发平台 |  √   |
    |          nginx           |    web服务器    |  *   |
    |          https           | web应用安全保证 |  *   |
    |         gunicorn         |   wsgi服务器    |  √   |
    |         mysql8.0         |   mysql数据库   |  √   |

    |           开发依赖            |              描述              | 使用 |
    | :---------------------------: | :----------------------------: | :--: |
    | Alibaba Short Message Service |        阿里巴巴短信服务        |  √   |
    |         flask_restful         |      web restful api框架       |  √   |
    |          marshmallow          |       类型转换、字段检验       |  √   |
    |            sha256             |            密码哈希            |  √   |
    |            pymysql            | 最流行的python mysql connector |  √   |

* 进度

  1. 短信注册、登陆、忘记密码功能
  2. 更安全的存储密码
  3. 实现活跃用户
  4. 重写sql脚本，加入与用户有关的一些储存过程和函数
  5. sql脚本自动化
  6. 字段检验
  7. 将项目的模块更加细化

* 弊端

    1. pymysql无法执行多语句，而sql脚本文件又不易控制，需要使用子进程，并且需要手动处理返回的结果，容易出错。
    2. mysql储存过程和函数难以调试，其中可能存在我们难以找出的bug。
    3. 启动gunicorn时，gunicorn中会为我们的服务器开启多个进程以进行负载均衡，这时我们的sql脚本自动化面临一个问题：多个服务器同时进行脚本执行，这导致经常出现问题。
    4. 多个服务器间保存的活跃用户仅用python无法做到共享。

## 第四版

* 改进
  1. mysql自家也有一个python库，并且可以执行多语句，考虑更换库。
  2. 使用redis，redis既可以当作锁来使用，又可以共享内存。
  3. 将密码视作一个永久有效的验证码。使用redis记录活跃用户，便于进程间的共享。

* 资料

    [MySQL Connector/Python Developer Guide](https://dev.mysql.com/doc/connector-python/en/)

    [Redis 教程](https://www.runoob.com/redis/redis-tutorial.html)

* 依赖

    |         服务搭建         |         描述         | 使用 |
    | :----------------------: | :------------------: | :--: |
    | ubuntu 20.04 1核1G 1Mbps |      服务器环境      |  √   |
    |        python3.8         |   web应用开发平台    |  √   |
    |          nginx           |      web服务器       |  *   |
    |          https           |   web应用安全保证    |  *   |
    |         gunicorn         |      wsgi服务器      |  √   |
    |         mysql8.0         |      关系数据库      |  √   |
    |         redis5.0         | 键值形式的内存数据库 |  √   |

    |           开发依赖            |        描述         | 使用 |
    | :---------------------------: | :-----------------: | :--: |
    | Alibaba Short Message Service |  阿里巴巴短信服务   |  √   |
    |         flask_restful         | web restful api框架 |  √   |
    |          marshmallow          | 类型转换、字段检验  |  √   |
    |            sha256             |      密码哈希       |  √   |
    |    mysql-connector-python     | mysql官方connector  |  √   |
    |             redis             |   redis connector   |  √   |

* 进度

    1. 短信注册、登陆、忘记密码功能。
    2. 更安全的存储密码
    3. 身份验证，在使用特定功能时，需要用户进行验证。
    4. redis实现进程间同步、共享，能够同时多开服务器，大幅度提升服务性能，使用redis作token查询的缓存，减少对mysql的查询。
    5. 简化sql脚本，取消不必要的sql函数和储存过程，改用python实现。
    6. sql脚本自动化
    7. 字段检验