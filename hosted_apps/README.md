# Server Hosted Apps

The services in this directory are to be run on the Timing Server in the form of a Docker stack. 

## Get Started with Docker

The following commands will differ based on your host OS and environment. The following are what are executed on the Server itself and provided as reference.

```
sudo apt update
sudo apt install -y docker docker-compose
docker-compose pull
docker-compose build --pull --no-cache
docker-compose up --build -d
```

