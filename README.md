# Simple VPN

### Installing using GitHub
    
```bash
git clone https://github.com/RomanHlodann/simple_vpn
cd simple_vpn
python -m venv venv
On mac: source venv/bin/activate Windows: venv/Scripts/activate
```

### Create new .env file with your values (Copy keys from .env.sample)
```
POSTGRES_PASSWORD=POSTGRES_PASSWORD
POSTGRES_USER=POSTGRES_USER
POSTGRES_DB=POSTGRES_DB
POSTGRES_HOST=POSTGRES_HOST
POSTGRES_PORT=POSTGRES_PORT
```

## Run with Docker
To run the project with Docker, follow these steps:

```bash
docker-compose up
```


## Access the API endpoints
`http://localhost:8000/`
* **Websites** `vpn/websites/`
* **Access website via vpn** `vpn/{website_name}/`


Users endpoint:
* **Login** `accounts/login/`
* **Register** `accounts/register/`
* **Account info** `accounts/me/`
