# Server Hosted Apps

The services in this directory are to be run on the Timing Server in the form of a Docker stack. 

## Important Note About Folder Structure

Each hosted app has two sub-folders in the services and volumes folders. 
- Services folder contents: This is what Docker will use to build a new container for the app.
    - On build, the contents of the services sub-folder are copied into the volumes sub-folder.
    - This WILL overwrite whatever is in the volumes sub-folder and can cause data loss. 
- Volumes folder contents: This (your intended sub-folder) is the working director for the app.
    - Each time the docker container is started, the contents in this sub-folder will be used to as the running app.
    - If you want to re-build the container, it is best practice to delete the sub-folder here before building.
 
**NOTE: The volumes folder is NOT pushed to git. This is intentional. you MUST copy your working code into the services sub-folder before committing and pushing to remote.**
See below for a recommended workflow. 

## Get Started with Docker

The following commands will differ based on your host OS and environment. The following are what are executed on the Server itself and provided as reference.

To get started after a fresh repo pull:
1. Ensure docker and docker-compose are installed and up to date
    ```
    sudo apt update
    sudo apt install -y docker docker-compose
    ```
2. Pull down the latest images from the docker repos
    ```
    docker-compose pull
    ```
3. Rebuild local images with new images from docker
    ```
    docker-compose build --pull --no-cache
    ```
4. Recreate the containers that have new images to use
    ```
    docker-compose up --build -d
    ```

At this point you will notice the Web UI app fails due to the postgres database being empty. You can run the create_schema.py file in the utilities folder to set up the tables and views. Then, bounce the webUI container to see the updates:
```
docker-compose down timingcontrolwebui
python3 ./utilities/Initialization/create_schema.py
docker-compose up -d timingcontrolwebui
```

## Recommended Development Workflow

Making changes to a python app is as simple as editing the code sitting in the volumes sub-folder. You can modify anything here and when the container is restarted it will run the app files in this sub-folder. 

If you need to add an imported package that needs a pip install, this should be copied to the services sub-folder to re-build the image
```
cp -r volumes/YourAppHere/app/* services/YourAppHere/.
rm -rf volumes/YourAppHere
docker-compose build --force-rm YourAppHere
docker-compose up -d --force-recreate YourAppHere
docker system prune -f
```

When you are ready to commit and push, first move everything into the services sub-folder so that when the repo is pulled the latest images and contents are present. 
```
cp -r volumes/YourAppHere/app/* services/YourAppHere/.
```

  
