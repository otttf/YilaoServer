# 文档介绍

## 一些字段的意义

`appid`：用来区分一个应用是否是我们自身开发的，如果没有这个字段，那么发送短信的功能只要调用api就能随便使用，存在风险。

## 如何查看

在文档中，会用`$param`表示param是一个变量，并在下方给出其意义。`$param...`指的是param为可变参数，即同时指代`$param1`，`$param2`，...，`$paramN`多个参数。

引用文档时，会用**$key**=value的形式给出，value不一定是常量，其中可能也会定义新变量。

文档会给出测试时的一些数据，每个HTTP报文的交互作为一块显示。

```
==================== REQUEST =====================
方法 URL

发送数据
==================== RESPONSE ====================
Http状态码 状态字符串

返回数据
====================== END =======================
```

## 数据类型

### Point

一个点可以用来标记用户、商品、任务目标的位置，其结构如下

```
{
	"longitude": $longitude,
	"latitude": $latitude,
	"name": $name
}
```

`$longitude`：经度，范围为-180到180

`$latitude`：纬度，范围为0到90

`$name`：该地点的名字，可以为空。

**注意：**由于特殊原因，**$longitude**=0且**$latitude**=90的点将会被看作为`null`。

# 发送验证码

在访问一些需要验证码验证的链接时，需要首先发送验证码。

```
POST http://api.yilao.tk:5000/v1.0/sms

{
	"appid": "df3b72a07a0a4fa1854a48b543690eab",
	"mobile": $mobile,
	"method": $method,
	"base_url": $base_url
}
```

`$mobile`**：用户手机号码**

`$method $base_url`**：需要访问的链接**

注意，base_url并不包含参数部分。

##### 返回

`201`：成功

# 用户

|       属性       |  类型  |           限制           |     解释     |
| :--------------: | :----: | :----------------------: | :----------: |
|      mobile      |  整数  |       手机号码格式       |    手机号    |
|      passwd      | 字符串 |                          |     密码     |
|     nickname     | 字符串 |                          |     昵称     |
|       sex        | 字符串 |       male或female       |     性别     |
|     portrait     |  整数  | 必须是自己所拥有的资源id |     头像     |
| default_location | Point  |                          | 用户默认地址 |
|    create_at     | 字符串 |                          |   注册日期   |

## 注册

##### 1. 发送验证码

**$method**=`PUT`

**$base_url**=`http://api.yilao.tk:5000/v1.0/users/$mobile`

##### 2. 验证并注册

```
PUT http://api.yilao.tk:5000/v1.0/users/$mobile?appid=df3b72a07a0a4fa1854a48b543690eab&code=$code

{
	"passwd": $passwd
}
```

`$mobile`**：用户手机号码**

`$code`**：验证码**

`$passwd`**：用户要设置的密码**

##### 返回

`201`：成功

`401`：用户验证失败

## 登陆

用户登陆采取token的方式，通过密码或者验证码来获得token。在设计中token拥有权限域，在使用api时不同的功能可能需要不同的权限，不过目前token只有全部权限这个选择。

### 通过验证码

##### 1. 发送验证码

**$method**=`POST`

**$base_url**=`http://api.yilao.tk:5000/v1.0/users/$mobile/tokens`

##### 2. 验证获取token

```
POST http://api.yilao.tk:5000/v1.0/users/$mobile/tokens?appid=df3b72a07a0a4fa1854a48b543690eab&code=$code
```

`$mobile`**：用户手机号码**

`$code`**：验证码**

### 通过密码

```
POST http://api.yilao.tk:5000/v1.0/users/$mobile/tokens?appid=df3b72a07a0a4fa1854a48b543690eab&passwd=$passwd
```

`$passwd`**：用户密码**

### 返回

`201`：成功，并且token会以json格式返回，

```
{
	"token": $token
}
```

`$token`**：令牌**

`401`：用户验证失败

## 更新

更新用户的信息，有一些字段如手机号、注册时间等会被拒绝更新。

### 更新非重要字段

```
PATCH http://api.yilao.tk:5000/v1.0/users/$mobile?appid=df3b72a07a0a4fa1854a48b543690eab&token=$token

{
	$key1: $value1, 
	$key2: $value2,
	...
}
```

`$key...`**：用户字段**

`$value...`**：字段值**

`$token`**：令牌**

##### 返回

`204`：成功

`401`：用户验证失败

### 更新重要字段

更新一些比较重要的字段时，不能使用token来验证，需要进行密码验证或者短信验证。更新过程基本和非重要字段一致，相应的，短信验证需要先发送短信，并且`token=$token`也应该改为`code=$code`或者`passwd=$passwd`。

`$code`：验证码

`$passwd`：密码

## 获取

```
GET http://api.yilao.tk:5000/v1.0/users/$mobile?appid=df3b72a07a0a4fa1854a48b543690eab&token=$token
```

##### 返回

`200`：成功，结果包含用户的所有信息。

`401`：用户验证失败

`404`：用户不存在

可以通过不传输密码来获取用户信息，如果返回401则是用户存在，返回404用户不存在。

# 订单

|      属性       |   类型   |      限制      |           解释           |
| :-------------: | :------: | :------------: | :----------------------: |
|       id        |   整数   |                |          订单id          |
|    from_user    |   整数   |                |    哪个用户创建的订单    |
|   destination   |  Point   |                | 完成所有任务后去哪里交付 |
| emergency_level |  字符串  | normal或urgent |         紧急程度         |
|    create_at    |  字符串  |                |       创建订单时间       |
|   receive_at    |  字符串  |                |       接受订单时间       |
|    executor     |   整数   |                |          执行者          |
|    close_at     |  字符串  |                |       关闭订单时间       |
|   close_state   |  字符串  |                |        关闭的状态        |
|      tasks      | Task列表 |                |         任务列表         |

## Task类型

|      属性      |  类型  |                             解释                             |
| :------------: | :----: | :----------------------------------------------------------: |
|       id       |  整数  |                            表单id                            |
|      name      | 字符串 |                            任务名                            |
|      type      | 字符串 |                           任务类型                           |
|     detail     | 字符串 |                           任务描述                           |
| protected_info | 字符串 |                 接单后才能告诉别人的私密信息                 |
|  destination   | Point  |                        任务的目的地址                        |
|     count      |  整数  |                           执行次数                           |
|     reward     | 浮点数 |                             奖赏                             |
|     in_at      | 字符串 | 用户借出资源的时间（做某项任务时可能需要用户给的某些资源，因此有一个借出时间） |
|     out_at     | 字符串 | 用户收回资源的时间（同理，资源使用完成后用户可能会有一个收回的时候） |

## 新建

```
POST http://127.0.0.1:5000/v1.0/users/$mobile/orders?token=$token&appid=df3b72a07a0a4fa1854a48b543690eab

{
	$key1: $value1, 
	$key2: $value2,
	...
}
```

`$mobile`：手机号码

`$token`：登陆时获取到的令牌

`$key...`**：字段**

`$value...`**：值**

## 聊天记录

|   属性    |  类型  |     解释     |
| :-------: | :----: | :----------: |
|   uuid    | 字符串 |     uuid     |
| from_user |  整数  | 来自哪位用户 |
| create_at | 字符串 |   创建时间   |

# 资源

|   属性    |  类型  |     解释     |
| :-------: | :----: | :----------: |
|   uuid    | 字符串 |     uuid     |
| from_user |  整数  | 来自哪位用户 |
| create_at | 字符串 |   创建时间   |

## 新建

# 测试

**注意：**在测试中，列举的是完整过程，看起来每次都会申请token，但实际上token并不需要重复申请。

## 用户注册

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/users/13927553153
==================== RESPONSE ====================
404 NOT FOUND
====================== END =======================
```

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/sms

{
    "appid": "df3b72a07a0a4fa1854a48b543690eab",
    "mobile": 13927553153,
    "method": "PUT",
    "base_url": "http://127.0.0.1:5000/v1.0/users/13927553153"
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

```
==================== REQUEST =====================
PUT http://127.0.0.1:5000/v1.0/users/13927553153?appid=df3b72a07a0a4fa1854a48b543690eab&code=1234

{
    "passwd": "12345679"
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

## 用户登录

### 通过密码

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "64f821c1103d44a8b1750e1fbb840fa7"
}
====================== END =======================
```

### 通过验证码

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/sms

{
    "appid": "df3b72a07a0a4fa1854a48b543690eab",
    "mobile": 13927553153,
    "method": "POST",
    "base_url": "http://127.0.0.1:5000/v1.0/users/13927553153/tokens"
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?code=1234&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "3c9d640882cd4fa48590ee9731c4c664"
}
====================== END =======================
```

## 更新用户信息

### 重要字段

#### 通过密码

```
==================== REQUEST =====================
PATCH http://127.0.0.1:5000/v1.0/users/13927553153?passwd=12345679

{
    "passwd": "12345680"
}
==================== RESPONSE ====================
204 NO CONTENT
====================== END =======================
```

#### 通过验证码

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/sms

{
    "appid": "df3b72a07a0a4fa1854a48b543690eab",
    "mobile": 13927553153,
    "method": "PATCH",
    "base_url": "http://127.0.0.1:5000/v1.0/users/13927553153"
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

```
==================== REQUEST =====================
PATCH http://127.0.0.1:5000/v1.0/users/13927553153?code=1234&appid=df3b72a07a0a4fa1854a48b543690eab

{
    "passwd": "12345679"
}
==================== RESPONSE ====================
204 NO CONTENT
====================== END =======================
```

### 普通字段

#### 通过token

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
PATCH http://127.0.0.1:5000/v1.0/users/13927553153?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab

{
    "default_location": {
        "longitude": 12,
        "latitude": 34,
        "name": "abc"
    }
}
==================== RESPONSE ====================
204 NO CONTENT
====================== END =======================
```

## 获取用户信息

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/users/13927553153?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
200 OK

{
    "mobile": 13927553153,
    "sex": null,
    "create_at": "2021-02-14T06:06:25",
    "nickname": null,
    "portrait": null,
    "default_location": {
        "longitude": 34.0,
        "latitude": 12.0,
        "name": "abc"
    },
    "mark": null
}
====================== END =======================
```

## 新建订单

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/orders?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab

{
    "tasks": [
        {
            "name": "abc",
            "type": "aaa",
            "count": 1,
            "reward": 1,
            "destination": {
                "longitude": 12,
                "latitude": 30,
                "name": "wwww"
            }
        }
    ]
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

## 获取和用户相关的订单

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/users/13927553153/orders?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
200 OK

[
    {
        "emergency_level": "normal",
        "close_at": null,
        "destination": {
            "longitude": 90.0,
            "latitude": 0.0,
            "name": null
        },
        "create_at": "2021-02-14T06:06:25",
        "id": 1,
        "executor": null,
        "tasks": [
            {
                "in_at": null,
                "destination": {
                    "longitude": 30.0,
                    "latitude": 12.0,
                    "name": "wwww"
                },
                "detail": null,
                "name": "abc",
                "count": 1,
                "id": 1,
                "out_at": null,
                "reward": 1.0,
                "protected_info": null,
                "type": "aaa"
            }
        ],
        "receive_at": null,
        "from_user": 13927553153,
        "close_state": null
    }
]
====================== END =======================
```

## 获取还没被接取的订单

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/public_orders
==================== RESPONSE ====================
200 OK

[
    {
        "emergency_level": "normal",
        "close_at": null,
        "destination": {
            "longitude": 90.0,
            "latitude": 0.0,
            "name": null
        },
        "create_at": "2021-02-14T06:06:25",
        "id": 1,
        "executor": null,
        "tasks": [
            {
                "in_at": null,
                "destination": {
                    "longitude": 30.0,
                    "latitude": 12.0,
                    "name": "wwww"
                },
                "detail": null,
                "name": "abc",
                "count": 1,
                "id": 1,
                "out_at": null,
                "reward": 1.0,
                "protected_info": null,
                "type": "aaa"
            }
        ],
        "receive_at": null,
        "from_user": 13927553153,
        "close_state": null
    }
]
====================== END =======================
```

## 注册另一位用户：16698066603

## 接单

还没测试。

## 取消订单/完成订单

还没测试。

## 发送信息

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/dialogs?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab

{
    "content": "hello!",
    "to_user": 16698066603
}
==================== RESPONSE ====================
201 CREATED
====================== END =======================
```

## 另一位用户回复信息：hi!

## 获取用户和另一个用户的交流

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/users/13927553153/dialogs_with/16698066603?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
200 OK

[
    {
        "to_user": 16698066603,
        "id": 1,
        "content": "hello!",
        "from_user": 13927553153,
        "send_at": "2021-02-14T06:06:25"
    },
    {
        "to_user": 13927553153,
        "id": 2,
        "content": "hi!",
        "from_user": 16698066603,
        "send_at": "2021-02-14T06:06:25"
    }
]
====================== END =======================
```

## 新建资源

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/mobile/13927553153/resources?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
200 OK

{
    "uuid": "9565fc6e-14f8-4880-9e29-5a759316cf4f"
}
====================== END =======================
```

## 下载资源

```
==================== REQUEST =====================
POST http://127.0.0.1:5000/v1.0/users/13927553153/tokens?passwd=12345679&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
201 CREATED

{
    "token": "c443bee7e5464f70b564b0cf570c75a5"
}
====================== END =======================
```

```
==================== REQUEST =====================
GET http://127.0.0.1:5000/v1.0/mobile/13927553153/resources/9565fc6e-14f8-4880-9e29-5a759316cf4f?token=c443bee7e5464f70b564b0cf570c75a5&appid=df3b72a07a0a4fa1854a48b543690eab
==================== RESPONSE ====================
200 OK
====================== END =======================
```

