# 发送验证码

在访问一些需要验证码验证的链接时，需要首先发送验证码。

```
POST http://api.yilao.tk:5000/v1.0/sms
Content-Type: application/json

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

### 举例

用户`12345678910`需要访问`GET http://api.yilao.tk:5000/v1.0/users/12345678910?arg=xxx`时

**$mobile**=`12345678910`

**$method**=`GET`

**$base_url**=`http://api.yilao.tk:5000/v1.0/users/12345678910`

# 用户

## 注册

##### 1. 发送验证码

**$method**=`PUT`

**$base_url**=`http://api.yilao.tk:5000/v1.0/users/$mobile`

##### 2. 验证并注册

```
PUT http://api.yilao.tk:5000/v1.0/users/$mobile?appid=df3b72a07a0a4fa1854a48b543690eab&code=$code
Content-Type: application/json

{
	"passwd": $passwd
}
```

`$mobile`**：用户手机号码**

`$code`**：验证码**

`$passwd`**：用户密码**

##### 返回

`201`：成功

## 登陆

用户登陆采取换取token的方式，通过密码或者验证码来获得token，token拥有权限域，在使用Api时不同的功能可能需要不同的权限。

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

`201`：成功，内容如下

```
{
	"token": $token
}
```

`$token`**：令牌**

## 更新

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

有一些重要的字段会被拒绝更新。

##### 返回

`200`：成功

## 获取

```
GET http://api.yilao.tk:5000/v1.0/users/$mobile?appid=df3b72a07a0a4fa1854a48b543690eab&token=$token
```

##### 返回

`200`：成功，结果包含用户的所有信息。

