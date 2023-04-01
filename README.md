# README

## DBの初期化

```
 docker run --name samesdb -e POSTGRES_USER=<postgres_user> -e POSTGRES_PASSWORD=<postgres_user_password> -e POSTGRES_DB=samesdb  -p 5432:5432 -d postgres:15.2
```

```
python manage.py makemigrations users
```

```
python manage.py makemigrations postapp
```

```
python manage.py migrate
```

## サンプルデータの投入

```
python manage.py loaddata init.json
```

## サーバの立ち上げ

```
python manage.py runserver
```

## サンプルデータでのログイン

ログインページ : <http://127.0.0.1:8000/login>

user24でのログイン情報は以下

- email : user_24@django.com
- password : user_24

userは0~49まで利用できます。
